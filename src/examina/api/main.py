"""ASGI entrypoint — `uvicorn examina.api.main:app` or `python -m examina.api.main`."""

from __future__ import annotations

from examina.api.app import create_app

app = create_app()

if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
