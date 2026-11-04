"""Linha de comando.

    python -m briefing run                      # dia de hoje, pipeline completo
    python -m briefing run --from summarize     # retoma a partir da síntese
    python -m briefing run --dry-run            # tudo menos o envio
    python -m briefing run --until curate       # só coleta + curadoria (sem LLM)
    python -m briefing login valor              # abre navegador p/ logar e salvar cookies
    python -m briefing test-delivery            # manda um "ping" no WhatsApp
    python -m briefing test-delivery --sample   # manda texto + 2 PDFs + 3 áudios de exemplo (sem LLM)
"""

from __future__ import annotations

import argparse
import logging
from datetime import date

STAGES = ["ingest", "curate", "summarize", "render", "deliver"]


def main(argv: list[str] | None = None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    p = argparse.ArgumentParser(prog="briefing")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run")
    r.add_argument("--date", type=date.fromisoformat, default=None)
    r.add_argument("--from", dest="start_from", default="ingest", choices=STAGES)
    r.add_argument("--until", default="deliver", choices=STAGES, help="última etapa a executar")
    r.add_argument("--dry-run", action="store_true")

    lg = sub.add_parser("login")
    lg.add_argument("source", choices=["valor", "ft", "nyt", "wsj"])

    td = sub.add_parser("test-delivery")
    td.add_argument("--sample", action="store_true",
                    help="envia o conjunto de exemplo completo (texto + 2 PDFs + 3 áudios) em vez de um ping")

    a = p.parse_args(argv)
    if a.cmd == "run":
        from .pipeline import run
        res = run(a.date, a.start_from, a.dry_run, a.until)
        print(res.model_dump_json(indent=2))
    elif a.cmd == "login":
        from .ingest.browser import interactive_login
        interactive_login(a.source)
    elif a.cmd == "test-delivery":
        if a.sample:
            from .config import load_settings
            from .deliver import send_sample
            send_sample(load_settings())
        else:
            from .deliver import ping
            ping()


if __name__ == "__main__":
    main()
