"""Acesso a conteúdo assinado com o PRÓPRIO login do usuário.

Abordagem: Playwright com *perfil persistente* (BROWSER_PROFILE_DIR). O login é
feito UMA vez, manualmente, via `python -m briefing login valor` (abre o Chromium,
você loga, fecha). A partir daí os cookies ficam no perfil e a coleta roda sem
interação. Quando a sessão expira, o pipeline detecta (paywall na página) e
avisa no WhatsApp para refazer o login.

Regras de uso:
- Uso pessoal, sem redistribuição do texto integral (o PDF traz resumo + link).
- Ritmo humano: 1 página por vez, pausa de 2–5 s, no máximo ~60 páginas/dia por fonte.
- Nunca rodar isso em IP de datacenter (GitHub Actions) para FT/NYT/WSJ: anti-bot.
"""

from __future__ import annotations

import os
import random
import time
from pathlib import Path

LOGIN_URLS = {
    "valor": "https://login.globo.com/login/4728",
    "ft": "https://accounts.ft.com/login",
    "nyt": "https://myaccount.nytimes.com/auth/login",
    "wsj": "https://accounts.wsj.com/login",
}


def profile_dir() -> Path:
    from .. import config
    return Path(os.environ.get("BROWSER_PROFILE_DIR") or (config.ROOT / "browser_profile")).resolve()


def has_profile() -> bool:
    """True depois do primeiro `login <fonte>` (o Chromium cria o diretório Default/ com os cookies)."""
    return (profile_dir() / "Default").exists()


def interactive_login(source: str) -> None:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(str(profile_dir()), headless=False)
        page = ctx.new_page()
        page.goto(LOGIN_URLS[source])
        input(f"Faça o login de {source} no navegador e pressione ENTER aqui quando terminar... ")
        ctx.close()
    print(f"sessão salva em {profile_dir()}")


class LoggedBrowser:
    """Context manager: `with LoggedBrowser() as b: html = b.fetch(url)`."""

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self._p = sync_playwright().start()
        self.ctx = self._p.chromium.launch_persistent_context(str(profile_dir()), headless=True)
        return self

    def __exit__(self, *exc):
        self.ctx.close()
        self._p.stop()

    def fetch(self, url: str, wait_selector: str | None = None) -> str:
        page = self.ctx.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=45_000)
            if wait_selector:
                page.wait_for_selector(wait_selector, timeout=15_000)
            time.sleep(random.uniform(2, 5))
            return page.content()
        finally:
            page.close()


def extract_text(html: str, url: str) -> dict:
    """HTML → {title, text, author, date} com trafilatura (bom em páginas de jornal)."""
    import trafilatura
    meta = trafilatura.extract(html, url=url, output_format="json", with_metadata=True,
                               include_comments=False, favor_precision=True)
    import json
    return json.loads(meta) if meta else {}
