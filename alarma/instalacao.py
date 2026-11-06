"""Troca o app instalado pelo instalador baixado. Só vale no app empacotado."""

import os
import subprocess
import sys
from pathlib import Path

ARGUMENTOS_WINDOWS = ["/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"]

# Roda depois que o app fecha. Se algo falhar, o app antigo fica no lugar e reabre.
SCRIPT_MAC = r"""
dmg=$1; app=$2; pid=$3
novo="$app.novo"; velho="$app.velho"
tentativas=0
while kill -0 "$pid" 2>/dev/null && [ "$tentativas" -lt 60 ]; do
    sleep 1
    tentativas=$((tentativas + 1))
done
ponto=$(mktemp -d)
if hdiutil attach -nobrowse -readonly -quiet -mountpoint "$ponto" "$dmg"; then
    rm -rf "$novo" "$velho"
    if ditto "$ponto/Rato-Alarme.app" "$novo" && mv "$app" "$velho"; then
        mv "$novo" "$app" || mv "$velho" "$app"
    fi
    rm -rf "$novo" "$velho"
    hdiutil detach -quiet "$ponto"
fi
rmdir "$ponto"
open "$app"
"""


def app_do_mac(executavel: str) -> Path | None:
    """O pacote .app que contém o executável, se dá para trocá-lo sem pedir senha."""
    pacote = next((pai for pai in Path(executavel).parents if pai.suffix == ".app"), None)
    if pacote is None or not os.access(pacote.parent, os.W_OK):
        return None
    return pacote


def sabe_instalar() -> bool:
    if not getattr(sys, "frozen", False):
        return False
    if sys.platform == "darwin":
        return app_do_mac(sys.executable) is not None
    return sys.platform == "win32"


def _ambiente() -> dict[str, str]:
    """Sem isso, o app novo herdaria os caminhos internos do PyInstaller do app velho."""
    return {**os.environ, "PYINSTALLER_RESET_ENVIRONMENT": "1"}


def iniciar(instalador: Path) -> None:
    """Dispara a troca em um processo separado. Quem chama precisa fechar o app em seguida."""
    if sys.platform == "win32":
        subprocess.Popen(
            [str(instalador), *ARGUMENTOS_WINDOWS],
            env=_ambiente(),
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        return
    pacote = app_do_mac(sys.executable)
    if pacote is None:
        raise OSError("app do Mac não pode ser trocado")
    subprocess.Popen(
        ["/bin/sh", "-c", SCRIPT_MAC, "sh", str(instalador), str(pacote), str(os.getpid())],
        env=_ambiente(),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
