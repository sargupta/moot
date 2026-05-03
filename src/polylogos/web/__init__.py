"""Polylogos web UI — FastAPI backend serving the single-page Live Stance Theatre.

The package layout:

    polylogos/web/
      __init__.py
      app.py              # FastAPI application + JSON projection of a debate run
      static/index.html   # single-page UI (D3 stance theatre + transcript + graph + dissent)

Boot via the CLI: ``polylogos serve`` (see :mod:`polylogos.cli`).
"""

from polylogos.web.app import create_app

__all__ = ["create_app"]
