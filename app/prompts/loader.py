"""Prompt loader — load and render Jinja2 prompt templates.

Usage:
    from app.prompts.loader import render

    # static prompt
    prompt = render("system/agnes")

    # with variables
    prompt = render("user/compliance_rank",
                    original=rm.model_dump(),
                    product=product.model_dump(),
                    substitutes=sub_payload,
                    top_x=5)
"""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

def _tojson(value, indent=None):
    return json.dumps(value, indent=indent, ensure_ascii=False)


_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent),
    undefined=StrictUndefined,   # raise on missing variables — catch bugs early
    trim_blocks=True,
    lstrip_blocks=True,
)
_env.filters["tojson"] = _tojson


def render(name: str, **kwargs) -> str:
    """Load and render a prompt template.

    Args:
        name: Template path relative to app/prompts/ without extension.
              e.g. "system/agnes", "user/compliance_rank"
        **kwargs: Variables to inject into the template.
    """
    template = _env.get_template(f"{name}.j2")
    return template.render(**kwargs)
