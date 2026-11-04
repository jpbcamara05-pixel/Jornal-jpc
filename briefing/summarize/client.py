"""Wrapper fino sobre o SDK da Anthropic.

Decisões:
- `messages.parse` + pydantic → saída estruturada, sem parsear JSON na mão.
- Thinking adaptativo (padrão no Opus 5.5); profundidade via `output_config.effort`.
- `fallbacks="default"` (beta server-side-fallback) para o caso raro de recusa.
- System prompt estável vai com `cache_control` → o perfil do leitor + regras
  editoriais (~2k tokens) são pagos uma vez por dia, não por chamada.
- Custos acumulados em `Usage` para o RunResult.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeVar

import anthropic
from pydantic import BaseModel

log = logging.getLogger(__name__)
PROMPTS_DIR = Path(__file__).parent / "prompts"
T = TypeVar("T", bound=BaseModel)

# USD por 1M tokens (ver skill claude-api; atualizar se a tabela mudar)
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
}


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read: int = 0
    cost_usd: float = 0.0
    calls: list[str] = field(default_factory=list)

    def add(self, model: str, usage, label: str) -> None:
        inp, out = PRICES.get(model, (5.0, 25.0))
        self.input_tokens += usage.input_tokens
        self.output_tokens += usage.output_tokens
        self.cache_read += getattr(usage, "cache_read_input_tokens", 0) or 0
        self.cost_usd += usage.input_tokens / 1e6 * inp + usage.output_tokens / 1e6 * out
        self.calls.append(label)


USAGE = Usage()


def load_prompt(name: str, **vars) -> str:
    text = (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")
    return text.format(**vars) if vars else text


def parse(
    output_model: type[T],
    *,
    system: str,
    user: str,
    model: str = "claude-opus-5-5",
    effort: str = "high",
    max_tokens: int = 16000,
    label: str = "",
) -> T:
    """Uma chamada estruturada. `system` é o prefixo estável (cacheado)."""
    client = anthropic.Anthropic()
    try:
        resp = client.beta.messages.parse(
            model=model,
            max_tokens=max_tokens,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
            output_format=output_model,
            output_config={"effort": effort},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    except anthropic.RateLimitError as e:
        log.warning("rate limit em %s: %s", label, e)
        raise
    except anthropic.APIStatusError as e:
        log.error("erro API em %s (%s): %s", label, e.status_code, e.message)
        raise

    if resp.stop_reason == "refusal":
        raise RuntimeError(f"recusa do modelo em {label}: {getattr(resp, 'stop_details', None)}")
    USAGE.add(model, resp.usage, label or output_model.__name__)
    log.info("%s | in=%s out=%s cache_read=%s | acumulado US$ %.3f",
             label, resp.usage.input_tokens, resp.usage.output_tokens,
             getattr(resp.usage, "cache_read_input_tokens", 0), USAGE.cost_usd)
    return resp.parsed_output
