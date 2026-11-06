"""Início com o computador no Mac e no Windows. No Linux quem cuida é o instalar.sh."""

import plistlib
import sys
from pathlib import Path

ROTULO = "meme.alarma"
VALOR_WINDOWS = "RatoAlarme"
CHAVE_WINDOWS = r"Software\Microsoft\Windows\CurrentVersion\Run"


def gerenciado() -> bool:
    """Só o app instalado se registra: rodando do código-fonte, o caminho não duraria."""
    return bool(getattr(sys, "frozen", False)) and sys.platform in ("darwin", "win32")


def caminho_mac() -> Path:
    return Path.home() / "Library/LaunchAgents" / f"{ROTULO}.plist"


def agente_mac(executavel: str) -> dict:
    return {
        "Label": ROTULO,
        "ProgramArguments": [executavel, "--boot"],
        "RunAtLoad": True,
        "KeepAlive": {"SuccessfulExit": False},
        "LimitLoadToSessionType": "Aqua",
    }


def _aplicar_mac(ligado: bool) -> None:
    caminho = caminho_mac()
    if not ligado:
        caminho.unlink(missing_ok=True)
        return
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_bytes(plistlib.dumps(agente_mac(sys.executable)))


def _aplicar_windows(ligado: bool) -> None:
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CHAVE_WINDOWS, 0, winreg.KEY_SET_VALUE) as chave:
        if ligado:
            winreg.SetValueEx(chave, VALOR_WINDOWS, 0, winreg.REG_SZ, f'"{sys.executable}" --boot')
            return
        try:
            winreg.DeleteValue(chave, VALOR_WINDOWS)
        except FileNotFoundError:
            pass


def aplicar(ligado: bool) -> None:
    """Regrava sempre: se a pessoa mover o app, o caminho volta a valer."""
    if not gerenciado():
        return
    try:
        if sys.platform == "darwin":
            _aplicar_mac(ligado)
        else:
            _aplicar_windows(ligado)
    except OSError:
        pass
