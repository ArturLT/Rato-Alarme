"""Onde cada sistema guarda configuração e estado. As variáveis XDG valem em todos."""

import os
import sys
from pathlib import Path

PASTA = "alarma-meme"


def _pasta_de_usuario(variavel_xdg: str, padrao_linux: str) -> Path:
    xdg = os.environ.get(variavel_xdg)
    if xdg:
        return Path(xdg) / PASTA
    if sys.platform == "darwin":
        return Path.home() / "Library/Application Support" / PASTA
    if sys.platform == "win32":
        base = os.environ.get("APPDATA")
        return (Path(base) if base else Path.home() / "AppData/Roaming") / PASTA
    return Path.home() / padrao_linux / PASTA


def pasta_config() -> Path:
    return _pasta_de_usuario("XDG_CONFIG_HOME", ".config")


def pasta_estado() -> Path:
    return _pasta_de_usuario("XDG_STATE_HOME", ".local/state")
