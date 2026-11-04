"""Modelos de dados compartilhados por todo o pipeline.

Fluxo:  Article (coleta)  →  Story (curadoria: dedup/cluster/rank)
        →  Briefing / AudioScript / DCMReport (síntese estruturada pelo LLM)
        →  render (PDF/áudio)  →  deliver (WhatsApp)

Os modelos de síntese (Briefing, AudioScript, DCMReport) são usados como
`output_format` em `client.messages.parse(...)`, então o LLM devolve JSON já
validado contra este esquema. Manter os campos enxutos: tudo que está aqui o
LLM precisa preencher.
"""

from __future__ import annotations

from datetime import date as Date
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, computed_field

# ---------------------------------------------------------------------------
# Coleta
# ---------------------------------------------------------------------------

class Source(str, Enum):
    VALOR = "valor"
    BRAZIL_JOURNAL = "brazil_journal"
    FT = "ft"
    NYT = "nyt"
    WSJ = "wsj"
    # Fontes estruturadas do Termômetro DCM
    VALOR_LEGAIS = "valor_legais"
    CVM = "cvm"
    B3 = "b3"
    ANBIMA = "anbima"
    TRUSTEE = "trustee"


class Market(str, Enum):
    LOCAL = "local"            # Brasil
    INTERNATIONAL = "intl"


class Article(BaseModel):
    """Um artigo bruto, como coletado. Persistido em SQLite para dedup e auditoria."""

    id: str = Field(description="Hash estável de (source, url)")
    source: Source
    market: Market
    url: HttpUrl
    title: str
    summary: str | None = Field(default=None, description="Lead/descrição do feed")
    body: str | None = Field(default=None, description="Texto integral, quando obtido")
    section: str | None = Field(default=None, description="Editoria: Empresas, Finanças, Brasil, Política...")
    authors: list[str] = []
    published_at: datetime | None = None
    fetched_at: datetime
    prominence: float = Field(
        default=0.0, ge=0, le=1,
        description="0..1; 1 = manchete de capa / edição impressa / top stories",
    )
    is_opinion: bool = False
    word_count: int | None = None
    raw: dict = Field(default_factory=dict, description="Campos extras do feed/API")


# ---------------------------------------------------------------------------
# Curadoria
# ---------------------------------------------------------------------------

class Topic(str, Enum):
    MERCADO_EMPRESAS = "mercado_empresas"
    ECONOMIA = "economia"
    POLITICA = "politica"
    INTERNACIONAL = "internacional"
    DCM = "dcm"
    OUTROS = "outros"


class Story(BaseModel):
    """Uma 'história' = cluster de artigos sobre o mesmo fato, já ranqueada."""

    id: str
    topic: Topic
    articles: list[Article] = Field(description="Artigos do cluster, o principal primeiro")
    score: float = Field(description="Pontuação final de ranking (ver curate/rank.py)")
    cross_coverage: int = Field(description="Nº de veículos distintos cobrindo")
    seen_before: bool = Field(default=False, description="Já apareceu em briefing anterior")


# ---------------------------------------------------------------------------
# Síntese · Briefing do Dia (PDF)
# ---------------------------------------------------------------------------

class Impact(str, Enum):
    ALTO = "alto"
    MEDIO = "medio"
    BAIXO = "baixo"


class Direction(str, Enum):
    POSITIVO = "positivo"
    NEGATIVO = "negativo"
    NEUTRO = "neutro"


class NewsCard(BaseModel):
    story_id: str
    title: str = Field(max_length=70, description="Título reescrito, curto e factual")
    summary: str = Field(max_length=280)
    why_it_matters: str = Field(max_length=160, description="Não repetir o resumo")
    impact: Impact
    direction: Direction = Field(description="Direção para o mercado local")
    tags: list[str] = Field(default_factory=list, description="setor, empresas, tipo")
    source_name: str
    url: str
    brazil_bridge: str | None = Field(
        default=None, max_length=160,
        description="Só para Internacional: 'Impacto para o Brasil: ...'",
    )


class ReadRecommendation(BaseModel):
    story_id: str
    title: str
    source_name: str
    url: str
    reading_minutes: int
    why_you_should_read: str = Field(
        max_length=200,
        description="Por que ESTE leitor (mercado financeiro / DCM / Brasil) deve ler o texto integral",
    )


class Briefing(BaseModel):
    date: Date
    edition_number: int
    phrase_of_the_day: str = Field(max_length=140)
    headline: NewsCard
    in_30_seconds: list[str] = Field(min_length=3, max_length=6)
    read_today: list[ReadRecommendation] = Field(min_length=3, max_length=5)
    mercado_empresas: list[NewsCard] = Field(min_length=4, max_length=8)
    economia: list[NewsCard] = Field(min_length=3, max_length=6)
    politica: list[NewsCard] = Field(min_length=2, max_length=5)
    internacional: list[NewsCard] = Field(min_length=3, max_length=6)
    agenda_do_dia: list[str] = Field(default_factory=list)
    sources_consulted: list[str] = Field(default_factory=list)
    articles_processed: int = 0


# ---------------------------------------------------------------------------
# Síntese · Áudios
# ---------------------------------------------------------------------------

class AudioChannel(str, Enum):
    MERCADO_EMPRESAS = "mercado_empresas"
    ECONOMIA = "economia"
    POLITICA = "politica"


class AudioScript(BaseModel):
    channel: AudioChannel
    date: Date
    opening: str
    segments: list[str] = Field(
        min_length=4, max_length=7,
        description="Um parágrafo por notícia, já com transições, escrito para ser ouvido",
    )
    closing: str

    @property
    def text(self) -> str:
        return "\n\n".join([self.opening, *self.segments, self.closing])

    @property
    def estimated_seconds(self) -> int:
        words = len(self.text.split())
        return int(words / 150 * 60)  # ~150 palavras/min


# ---------------------------------------------------------------------------
# Síntese · Termômetro DCM
# ---------------------------------------------------------------------------

class OpportunityType(str, Enum):
    NOVA_EMISSAO = "nova_emissao"            # família A
    REFINANCIAMENTO = "refinanciamento"      # família B (liability management, muro de vencimentos)
    CONSENT_WAIVER = "consent_waiver"        # família C (AGD, waiver, repactuação, RE/RJ)
    GATILHO_FUNDING = "gatilho_funding"      # família D (M&A, capex, leilão, concessão)
    EVENTO_CREDITO = "evento_credito"        # família E (rating, covenant, inadimplência)
    MACRO_REGULATORIO = "macro_regulatorio"  # família F (juros, fluxo, CVM/CMN, tributação)


class SourceType(str, Enum):
    """Tipo da fonte → componente 'confiança da fonte' do score (config/dcm_signals.yaml)."""
    DOCUMENTO_OFICIAL = "documento_oficial"    # CVM IPE / Fundos.NET / CSV CVM / B3
    TRUSTEE = "trustee"                        # Vórtx, Oliveira Trust, Pentágono…
    JORNAL_LEGAL = "jornal_legal"              # Diário Comercial, Gazeta SP, Valor RI
    IMPRENSA_PRINCIPAL = "imprensa_principal"  # Valor, Pipeline, Brazil Journal
    OUTRA_MIDIA = "outra_midia"
    RUMOR = "rumor"                            # "apurou", "segundo fontes"


class Confidence(str, Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAIXA = "baixa"


class DCMSignalDraft(BaseModel):
    """O que o LLM extrai de um documento/notícia. O score NÃO é tarefa do LLM (ver dcm_score.py)."""

    company: str
    sector: str
    economic_group: str | None = None
    opportunity: OpportunityType
    subtype: str = Field(description="Subtipo da taxonomia (config/dcm_signals.yaml → signals.*.subtypes), "
                                     "ex.: agd_convocada, resgate_antecipado, rca_aprova_emissao, leilao_vencido")
    instrument: str | None = Field(default=None, description="DEB 5ª emissão, CRA, NC, bond…")
    amount_brl: float | None = Field(default=None, description="Valor em R$ (número puro), se citado no texto")
    event_date: Date | None = Field(default=None, description="AGD, vencimento, bookbuilding, liquidação…")
    source_type: SourceType
    confidence: Confidence
    evidence: str = Field(max_length=300, description="Trecho LITERAL da fonte")
    reading: str = Field(max_length=220, description="Interpretação em 1 frase")
    next_step: str = Field(max_length=160, description="Ação concreta sugerida")
    source_name: str
    url: str
    keywords_matched: list[str] = Field(default_factory=list)
    parties: dict[str, str] = Field(default_factory=dict,
                                    description="coordenador_lider, agente_fiduciario, rating, assessor…")


class DCMSignal(DCMSignalDraft):
    """Sinal pontuado pelo código (determinístico) a partir do rascunho do LLM."""

    id: str = ""
    score: int = Field(default=0, ge=0, le=100)
    band: str = Field(default="frio", description="frio · morno · aquecendo · quente · fervendo")
    score_components: dict[str, int] = Field(default_factory=dict)
    corroborations: int = Field(default=0, description="Nº de fontes independentes adicionais")
    status: str = Field(default="novo", description="novo · acompanhando · concluido · descartado")

    @computed_field  # type: ignore[misc]
    @property
    def heat(self) -> int:
        """1–5 para exibição (🔥)."""
        return max(1, min(5, -(-self.score // 20)))


class LegalNotice(BaseModel):
    """Aviso/edital: AGD, anúncio de início/encerramento, fato relevante sobre dívida."""

    kind: Literal["agd", "inicio_oferta", "encerramento_oferta", "fato_relevante", "aviso_ao_mercado",
                  "aviso_debenturistas", "outro"]
    company: str
    instrument: str | None = Field(default=None, description="debênture 5ª emissão, CRA, nota comercial…")
    date: Date | None = None
    summary: str = Field(max_length=200)
    source_name: str
    url: str


class DCMReportDraft(BaseModel):
    """O que o LLM devolve na consolidação; o relatório final é montado em código."""

    top_signal_ids: list[str] = Field(max_length=5, description="ids dos sinais mais acionáveis, em ordem")
    temperature_rationale: str = Field(max_length=240)
    notices: list[LegalNotice] = Field(default_factory=list)
    credit_context: list[str] = Field(default_factory=list, description="Selic/DI, fluxo, regulação")
    upcoming_events: list[str] = Field(default_factory=list, description="DD/MM — empresa — evento")


class DCMReport(BaseModel):
    date: Date
    temperature: int = Field(ge=0, le=100)
    temperature_label: Literal["frio", "morno", "aquecendo", "quente", "fervendo"]
    temperature_rationale: str = Field(max_length=240)
    top_signals: list[DCMSignal] = Field(max_length=5)
    other_signals: list[DCMSignal] = Field(default_factory=list)
    notices: list[LegalNotice] = Field(default_factory=list)
    credit_context: list[str] = Field(default_factory=list)
    upcoming_events: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Execução
# ---------------------------------------------------------------------------

class RunResult(BaseModel):
    date: Date
    started_at: datetime
    finished_at: datetime | None = None
    articles_collected: int = 0
    stories_ranked: int = 0
    outputs: dict[str, str] = Field(default_factory=dict, description="nome → caminho do arquivo")
    llm_cost_usd: float = 0.0
    tts_chars: int = 0
    delivered: bool = False
    errors: list[str] = Field(default_factory=list)
