from __future__ import annotations

from pathlib import Path


_APP_DIR = Path(__file__).resolve().parent
_ASSETS_DIR = _APP_DIR / "assets"


def asset_path(*parts: str) -> Path:
    """Return an absolute path to a packaged Desktop runtime asset.

    Keeping asset resolution anchored to ``desktop_client/app`` makes resource
    lookup independent of where feature/view modules live inside the package.
    """
    return _ASSETS_DIR.joinpath(*parts)
