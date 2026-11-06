"""Travessuras do pet que mexem em outros programas: fechar aba, minimizar e falar alto.

Tudo é pedido educado ao sistema: nada mata processo nem digita texto em janela
alheia. No macOS, a primeira vez que o rato fizer uma dessas, o sistema pede
permissão de Acessibilidade ou de Automação para o Rato-Alarme.
"""

import json
import os
import shutil
import subprocess
import sys

from alarma import sistema

NAVEGADORES_MAC_ABAS = {
    "Google Chrome": "active tab",
    "Brave Browser": "active tab",
    "Microsoft Edge": "active tab",
    "Vivaldi": "active tab",
    "Opera": "active tab",
    "Chromium": "active tab",
    "Safari": "current tab",
}
NAVEGADORES_MAC_ATALHO = ("Firefox", "Arc", "Zen", "Orion")
NAVEGADORES = ("chrome", "firefox", "edge", "brave", "opera", "vivaldi", "chromium", "safari", "arc", "zen", "librewolf")
PROGRAMAS_DO_RATO = ("Rato-Alarme", "Python", "python3", "python")
ESPERA_S = 3


def _ler(*comando: str) -> str | None:
    try:
        saida = subprocess.run(comando, capture_output=True, text=True, timeout=ESPERA_S)
    except (OSError, subprocess.TimeoutExpired):
        return None
    return saida.stdout.strip() if saida.returncode == 0 else None


def _osascript(script: str) -> str | None:
    return _ler("osascript", "-e", script)


def eh_navegador(nome: str) -> bool:
    nome = nome.lower()
    return any(n in nome for n in NAVEGADORES)


# ---- macOS ----


def app_da_frente_mac() -> str | None:
    return _osascript('tell application "System Events" to get name of first application process whose frontmost is true')


def script_fechar_aba_mac(app: str) -> str | None:
    """Só fecha se a janela tiver mais de uma aba: fechar a última fecharia a janela inteira."""
    if app in NAVEGADORES_MAC_ABAS:
        aba = NAVEGADORES_MAC_ABAS[app]
        return (
            f'tell application "{app}" to if (count of windows) > 0 then '
            f"if (count of tabs of front window) > 1 then close {aba} of front window"
        )
    if app in NAVEGADORES_MAC_ATALHO:
        return 'tell application "System Events" to keystroke "w" using command down'
    return None


def _fechar_aba_mac() -> bool:
    app = app_da_frente_mac()
    script = script_fechar_aba_mac(app or "")
    return script is not None and _osascript(script) is not None


def _minimizar_mac() -> bool:
    app = app_da_frente_mac()
    if not app or app in PROGRAMAS_DO_RATO or app == "Finder":
        return False
    script = (
        f'tell application "System Events" to tell application process "{app}" to '
        'if (count of windows) > 0 then set value of attribute "AXMinimized" of window 1 to true'
    )
    return _osascript(script) is not None


def _empurrar_janela_mac(dx: int, dy: int) -> bool:
    app = app_da_frente_mac()
    if not app or app in PROGRAMAS_DO_RATO or app == "Finder":
        return False
    script = (
        f'tell application "System Events" to tell application process "{app}" to '
        f"if (count of windows) > 0 then set position of window 1 to "
        f"{{(item 1 of (get position of window 1)) + {dx}, (item 2 of (get position of window 1)) + {dy}}}"
    )
    return _osascript(script) is not None


# ---- Windows ----


def _janela_da_frente_windows():
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    janela = user32.GetForegroundWindow()
    if not janela:
        return None, ""
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(janela, ctypes.byref(pid))
    if pid.value == os.getpid():
        return None, ""
    tamanho = user32.GetWindowTextLengthW(janela)
    titulo = ctypes.create_unicode_buffer(tamanho + 1)
    user32.GetWindowTextW(janela, titulo, tamanho + 1)
    return janela, titulo.value


def _fechar_aba_windows() -> bool:
    import ctypes

    janela, titulo = _janela_da_frente_windows()
    if janela is None or not eh_navegador(titulo.replace("​", "")):
        return False
    user32 = ctypes.windll.user32
    ctrl, w, solta = 0x11, 0x57, 0x2
    user32.keybd_event(ctrl, 0, 0, 0)
    user32.keybd_event(w, 0, 0, 0)
    user32.keybd_event(w, 0, solta, 0)
    user32.keybd_event(ctrl, 0, solta, 0)
    return True


def _minimizar_windows() -> bool:
    import ctypes

    janela, _ = _janela_da_frente_windows()
    if janela is None:
        return False
    ctypes.windll.user32.ShowWindow(janela, 6)  # SW_MINIMIZE
    return True


def _empurrar_janela_windows(dx: int, dy: int) -> bool:
    import ctypes
    from ctypes import wintypes

    janela, _ = _janela_da_frente_windows()
    if janela is None:
        return False
    r = wintypes.RECT()
    user32 = ctypes.windll.user32
    if not user32.GetWindowRect(janela, ctypes.byref(r)):
        return False
    user32.SetWindowPos(janela, 0, r.left + dx, r.top + dy, 0, 0, 0x0001 | 0x0004 | 0x0010)  # sem mudar tamanho, ordem, foco
    return True


# ---- Linux (Hyprland) ----


def _fechar_aba_linux() -> bool:
    saida = _ler("hyprctl", "activewindow", "-j")
    try:
        janela = json.loads(saida or "")
    except ValueError:
        return False
    if not isinstance(janela, dict) or janela.get("pid") == os.getpid():
        return False
    if not eh_navegador(str(janela.get("class", ""))) or shutil.which("wtype") is None:
        return False
    return _ler("wtype", "-M", "ctrl", "w", "-m", "ctrl") is not None


# ---- o que o pet chama ----


def fechar_aba() -> bool:
    """Fecha a aba da frente se o navegador estiver na frente. True se tentou."""
    try:
        if sys.platform == "darwin":
            return _fechar_aba_mac()
        if sys.platform == "win32":
            return _fechar_aba_windows()
        return sistema.tem_hyprland() and _fechar_aba_linux()
    except Exception:
        return False


def minimizar() -> bool:
    try:
        if sys.platform == "darwin":
            return _minimizar_mac()
        if sys.platform == "win32":
            return _minimizar_windows()
    except Exception:
        return False
    return False


def empurrar_janela(dx: int = 80, dy: int = 0) -> bool:
    """Empurra a janela da frente uns pixels, como se o rato tivesse esbarrado nela."""
    try:
        if sys.platform == "darwin":
            return _empurrar_janela_mac(dx, dy)
        if sys.platform == "win32":
            return _empurrar_janela_windows(dx, dy)
    except Exception:
        return False
    return False


APPS = {
    "calculadora": {"darwin": ["open", "-a", "Calculator"], "win32": ["calc.exe"], "linux": ["gnome-calculator"]},
    "notas": {"darwin": ["open", "-a", "Stickies"], "win32": ["notepad.exe"], "linux": ["gnome-text-editor"]},
}


def abrir_app(nome: str) -> bool:
    """Abre um programa inofensivo do sistema (calculadora, notas)."""
    comandos = APPS.get(nome, {})
    comando = comandos.get(sys.platform) or comandos.get("linux")
    if not comando or (sys.platform.startswith("linux") and shutil.which(comando[0]) is None):
        return False
    try:
        subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        return False
    return True


def volume() -> int | None:
    """Volume atual de 0 a 100, se der para saber."""
    try:
        if sys.platform == "darwin":
            saida = _osascript("output volume of (get volume settings)")
            return int(saida) if saida and saida.isdigit() else None
        if sys.platform == "win32":
            sys.coinit_flags = 2
            from pycaw.pycaw import AudioUtilities

            return round(AudioUtilities.GetSpeakers().EndpointVolume.GetMasterVolumeLevelScalar() * 100)
    except Exception:
        return None
    return None


def definir_volume(nivel: int) -> bool:
    nivel = max(0, min(100, int(nivel)))
    try:
        if sys.platform == "darwin":
            return _osascript(f"set volume output volume {nivel}") is not None
        if sys.platform == "win32":
            sys.coinit_flags = 2
            from pycaw.pycaw import AudioUtilities

            AudioUtilities.GetSpeakers().EndpointVolume.SetMasterVolumeLevelScalar(nivel / 100, None)
            return True
    except Exception:
        return False
    return False


def pode_mexer_volume() -> bool:
    return sys.platform in ("darwin", "win32")


def pode_empurrar() -> bool:
    return sys.platform in ("darwin", "win32")


def pode_minimizar() -> bool:
    return sys.platform in ("darwin", "win32")


def pode_fechar_aba() -> bool:
    return sys.platform in ("darwin", "win32") or (sistema.tem_hyprland() and shutil.which("wtype") is not None)


def pode_mover_cursor() -> bool:
    """No Wayland nenhum programa move o cursor dos outros."""
    return not sistema.tem_hyprland()


def comando_voz(texto: str, plataforma: str | None = None) -> list[str] | None:
    plataforma = plataforma or sys.platform
    texto = " ".join(texto.split())[:300]
    if plataforma == "darwin":
        return ["say", "-v", "Luciana", texto]
    if plataforma == "win32":
        seguro = texto.replace("'", "''")
        return [
            "powershell", "-NoProfile", "-Command",
            "Add-Type -AssemblyName System.Speech; "
            f"(New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{seguro}')",
        ]
    for programa, argumentos in (("spd-say", ["-l", "pt"]), ("espeak-ng", ["-v", "pt-br"]), ("espeak", ["-v", "pt"])):
        if shutil.which(programa):
            return [programa, *argumentos, texto]
    return None


def falar(texto: str) -> None:
    comando = comando_voz(texto)
    if comando is None:
        return
    extra = {"creationflags": 0x08000000} if sys.platform == "win32" else {}  # sem janela de console
    try:
        subprocess.Popen(comando, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **extra)
    except OSError:
        pass
