"""Fontes estruturadas para o Termômetro DCM (avisos, editais, fatos relevantes, ofertas).

"Valor Legais" não existe mais como seção web (avisos legais só na réplica em PDF do impresso).
O que a substitui, tudo público e sem login (URLs em config/sources.yaml → dcm):
  1. CVM Dados Abertos · IPE (documentos eventuais de cias abertas): Fato Relevante, Aviso aos
     Debenturistas, Assembleia AGDEB (edital de convocação), Documentos de Oferta, Escrituras.
     CSV anual em zip; atualização com alguns dias de atraso.
  2. CVM Dados Abertos · Ofertas (oferta_resolucao_160.csv): requerimentos de rito automático
     (debêntures, CRI, CRA, notas comerciais) com emissor, líder, valor, status. Diário.
  3. B3 · Publicação de Ofertas Públicas em andamento: página HTML com PDFs de Aviso ao Mercado,
     Anúncio de Início/Encerramento.
  4. (fase 3) RAD CVM em tempo real, B3 GetMaterialFacts, Fundos.NET (FIDC/FII), ANBIMA Data,
     páginas de assembleias dos agentes fiduciários.
Cada item vira Article com source ∈ {CVM, B3, ...} e `section` = tipo do aviso.
"""

from __future__ import annotations

import csv
import io
import logging
import re
import zipfile
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup

from ..models import Market, Source
from .base import Collector

log = logging.getLogger(__name__)
DEBT_WORDS = re.compile(r"deb[eê]ntur|CRI\b|CRA\b|nota[s]? comercia|emiss[ãa]o|oferta|resgate|assembleia|waiver|agente fiduci", re.IGNORECASE)
RAD_DOWNLOAD = "https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx"


class DCMNoticesCollector(Collector):
    name = "dcm_notices"
    source = Source.CVM
    market = Market.LOCAL

    def collect(self, settings: dict, day: date) -> list:
        from .. import config
        cfg = config.load_yaml("sources.yaml")["dcm"]
        since = day - timedelta(days=settings.get("dcm_lookback_days", 3))
        # o CSV anual do IPE é publicado com ~3–5 dias de atraso; janela maior + dedup por signal_id no SQLite
        since_ipe = day - timedelta(days=settings.get("dcm_ipe_lookback_days", 8))
        out = []
        for fn in (self._cvm_ipe, self._cvm_ofertas_160, self._b3_ofertas, self._vortx_events):
            try:
                got = fn(cfg, since_ipe if fn.__name__ == "_cvm_ipe" else since)
                log.info("%s: %d itens", fn.__name__, len(got))
                out.extend(got)
            except Exception:  # fonte estruturada fora do ar não derruba o Termômetro
                log.exception("falha em %s", fn.__name__)
        return out

    # ------------------------------------------------------------------ CVM IPE
    def _cvm_ipe(self, cfg: dict, since: date) -> list:
        rows = _csv_from_zip(cfg["cvm_ipe_zip"].format(yyyy=since.year))
        wanted = {c.lower() for c in cfg["cvm_ipe_categories"]}
        out, seen = [], set()
        for r in rows:
            cat = (r.get("Categoria") or "").strip()
            if cat.lower() not in wanted or (r.get("Data_Entrega") or "") < since.isoformat():
                continue
            tipo, especie, assunto = (r.get(k, "") or "" for k in ("Tipo", "Especie", "Assunto"))
            subject = f"{tipo} {especie} {assunto}"
            c = cat.lower()
            # Assembleia: só AGDEB (ou AGE cuja pauta fala de emissão/dívida); FR/Comunicado: só se falam de dívida
            if c == "assembleia" and "agdeb" not in tipo.lower() and not DEBT_WORDS.search(assunto):
                continue
            if c in {"fato relevante", "comunicado ao mercado"} and not DEBT_WORDS.search(subject):
                continue
            key = (r.get("Codigo_CVM"), c, tipo, especie, assunto[:80])  # reapresentações/versões
            if key in seen:
                continue
            seen.add(key)
            kind = _ipe_kind(cat, tipo, especie)
            url = r.get("Link_Download") or RAD_DOWNLOAD
            a = self.make(url, f"{r.get('Nome_Companhia', '').strip()} — {cat}: {r.get('Assunto', '').strip()[:140]}",
                          summary=subject.strip(), section=kind, prominence=0.9 if kind in ("agd", "aviso_debenturistas") else 0.6,
                          raw={k: r.get(k) for k in ("Nome_Companhia", "Codigo_CVM", "Categoria", "Tipo", "Especie", "Data_Entrega")})
            out.append(a)
        return out

    # ----------------------------------------------------------- CVM ofertas 160
    def _cvm_ofertas_160(self, cfg: dict, since: date) -> list:
        rows = _csv_from_zip(cfg["cvm_ofertas_zip"], member=cfg["cvm_ofertas_csv"])
        out = []
        for r in rows:
            vm = (r.get("Valor_Mobiliario") or "")
            if not re.search(r"deb[eê]nture|CRI|CRA|nota", vm, re.IGNORECASE):
                continue
            if (r.get("Data_requerimento") or r.get("Data_Requerimento") or "") < since.isoformat():
                continue
            title = (f"{r.get('Nome_Emissor', '').strip()} — {vm} · R$ {r.get('Valor_Total_Registrado', '?')} · "
                     f"{r.get('Status_Requerimento', '')} · líder: {r.get('Nome_Lider', '')}")
            out.append(self.make("https://dados.cvm.gov.br/dataset/oferta-distrib", title,
                                 summary=f"Destinação: {r.get('Destinacao_recursos', '')} | Público: {r.get('Publico_alvo', '')}",
                                 section="inicio_oferta", prominence=0.7, raw=dict(r)))
        return out

    # ------------------------------------------------------------- B3 ofertas
    def _b3_ofertas(self, cfg: dict, since: date) -> list:
        html = requests.get(cfg["b3_ofertas_andamento"], timeout=60, headers={"User-Agent": "Mozilla/5.0"}).text
        soup = BeautifulSoup(html, "html.parser")
        out = []
        for a in soup.select("a[href$='.pdf']"):
            text = a.get_text(" ", strip=True)
            row = a.find_parent("tr")
            ctx = row.get_text(" | ", strip=True) if row else text
            if not DEBT_WORDS.search(ctx):
                continue
            kind = "inicio_oferta" if re.search(r"in[ií]cio", ctx, re.IGNORECASE) else (
                "encerramento_oferta" if re.search(r"encerramento", ctx, re.IGNORECASE) else "aviso_ao_mercado")
            href = a["href"] if a["href"].startswith("http") else "https://www.b3.com.br" + a["href"]
            out.append(self.make(href, ctx[:160], summary=ctx, section=kind, prominence=0.75))
        return out


    # ---------------------------------------------------------------- Vórtx
    def _vortx_events(self, cfg: dict, since: date) -> list:
        """Assembleias e consultas formais no site da Vórtx (maior agente fiduciário em nº de ofertas 2026).
        Tabela server-rendered, 10 por página; só eventos Ativa/Iniciada viram sinal."""
        tcfg = cfg["trustees"]["vortx"]
        out = []
        for page in range(1, tcfg.get("pages", 3) + 1):
            html = requests.get(tcfg["events"].format(page=page), timeout=60, headers={"User-Agent": "Mozilla/5.0"}).text
            soup = BeautifulSoup(html, "html.parser")
            for row in soup.select("table tr"):
                cells = [c.get_text(" ", strip=True) for c in row.find_all(["td", "th"])]
                text = " | ".join(cells)
                if not cells or not re.search(r"ativa|iniciada", text, re.IGNORECASE):
                    continue
                if not re.search(r"AGD|AGT|debenturista|consulta formal|edital", text, re.IGNORECASE):
                    continue
                link = row.find("a", href=True)
                url = link["href"] if link and link["href"].startswith("http") else tcfg["events"].format(page=page)
                a = self.make(url, text[:160], summary=text, section="agd", prominence=0.9, raw={"cells": cells})
                a.source = Source.TRUSTEE
                out.append(a)
        return out


# ---------------------------------------------------------------------------
def _download_cached(url: str) -> bytes:
    """Zips da CVM mudam uma vez por dia: guarda em data/cache/<nome>-<hoje>.zip e apaga versões antigas."""
    from .. import config
    cache = config.DATA_DIR / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    stem = url.rsplit("/", 1)[-1].removesuffix(".zip")
    path = cache / f"{stem}-{date.today().isoformat()}.zip"
    if path.exists():
        return path.read_bytes()
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    for old in cache.glob(f"{stem}-*.zip"):
        old.unlink()
    path.write_bytes(r.content)
    return r.content


def _csv_from_zip(url: str, member: str | None = None) -> list[dict]:
    """Baixa (com cache diário) um zip da CVM e devolve as linhas do CSV (separador ';', latin-1) como dicts."""
    csv.field_size_limit(10**8)
    z = zipfile.ZipFile(io.BytesIO(_download_cached(url)))
    name = member or next(n for n in z.namelist() if n.lower().endswith(".csv"))
    with z.open(name) as f:
        text = io.TextIOWrapper(f, encoding="latin-1", errors="replace")
        return list(csv.DictReader(text, delimiter=";"))


def _ipe_kind(cat: str, tipo: str, especie: str) -> str:
    c, t, e = cat.lower(), tipo.lower(), especie.lower()
    if "agdeb" in t or ("assembleia" in c and "debent" in (t + e)):
        return "agd" if "convoca" in e else "agd_ata"
    if "debenturistas" in c:
        return "aviso_debenturistas"
    if "escritura" in c:
        return "aditamento_escritura" if "adit" in (t + e + c) and "escritura" not in e else "escritura"
    if "oferta" in c:
        return "aviso_ao_mercado"
    if "fato relevante" in c:
        return "fato_relevante"
    return "outro"
