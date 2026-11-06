"""Som e mudo em cada sistema. Falha aqui nunca pode derrubar o alarme."""

import os
import subprocess
import sys
from pathlib import Path

SAIDA_DE_SOM = "@DEFAULT_AUDIO_SINK@"


def _rodar(*comando: str) -> None:
    try:
        subprocess.Popen(
            comando,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


def _ler(*comando: str) -> str:
    try:
        saida = subprocess.run(comando, capture_output=True, text=True, timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return saida.stdout


def tem_hyprland() -> bool:
    """Olha as duas variáveis: no boot, a primeira pode ainda não ter chegado ao serviço."""
    return bool(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE")) or (
        "Hyprland" in os.environ.get("XDG_CURRENT_DESKTOP", "")
    )


def mexe_em_outras_janelas() -> bool:
    """Por enquanto, fechar e mexer em janelas alheias só existe no Hyprland."""
    return tem_hyprland()


def tocar(arquivo: Path) -> None:
    if sys.platform == "win32":
        import winsound

        winsound.PlaySound(str(arquivo), winsound.SND_FILENAME | winsound.SND_ASYNC)
    elif sys.platform == "darwin":
        _rodar("afplay", str(arquivo))
    else:
        _rodar("pw-play", str(arquivo))


def _volume_do_windows():
    sys.coinit_flags = 2  # o Qt já abre a thread principal nesse modo
    from pycaw.pycaw import AudioUtilities

    return AudioUtilities.GetSpeakers().EndpointVolume


def esta_mudo() -> bool:
    if sys.platform == "win32":
        try:
            return bool(_volume_do_windows().GetMute())
        except Exception:
            return False
    if sys.platform == "darwin":
        return _ler("osascript", "-e", "output muted of (get volume settings)").strip() == "true"
    return "[MUTED]" in _ler("wpctl", "get-volume", SAIDA_DE_SOM)


def definir_mudo(mudo: bool) -> None:
    if sys.platform == "win32":
        try:
            _volume_do_windows().SetMute(1 if mudo else 0, None)
        except Exception:
            pass
    elif sys.platform == "darwin":
        _rodar("osascript", "-e", f"set volume output muted {'true' if mudo else 'false'}")
    else:
        _rodar("wpctl", "set-mute", SAIDA_DE_SOM, "1" if mudo else "0")
