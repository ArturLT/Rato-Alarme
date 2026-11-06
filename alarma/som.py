"""Tom curto do alarme. Dois bipes, sem arquivo de áudio no repositório."""

import math
import os
import struct
import subprocess
import wave
from pathlib import Path

from alarma.logica import Alarme

_FREQUENCIA = {
    Alarme.MANHA: 880.0,
    Alarme.TARDE: 520.0,
}


def _tom(taxa: int, frequencia: float, segundos: float) -> bytes:
    amostras = int(taxa * segundos)
    quadros = bytearray()
    for i in range(amostras):
        envoltorio = math.sin(math.pi * i / amostras)
        valor = int(32767 * 0.4 * envoltorio * math.sin(2 * math.pi * frequencia * i / taxa))
        quadros += struct.pack("<h", max(-32767, min(32767, valor)))
    return bytes(quadros)


def caminho_do_tom(alarme: str) -> Path:
    base = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
    return base / f"alarma-meme-{alarme}.wav"


def garantir_tom(alarme: str) -> Path:
    frequencia = _FREQUENCIA[alarme]
    destino = caminho_do_tom(alarme)
    if destino.exists():
        return destino
    taxa = 22050
    silencio = b"\x00\x00" * int(taxa * 0.08)
    dados = _tom(taxa, frequencia, 0.12) + silencio + _tom(taxa, frequencia, 0.18)
    with wave.open(str(destino), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(taxa)
        wav.writeframes(dados)
    return destino


def tocar(alarme: str) -> None:
    if alarme == Alarme.NENHUM:
        return
    arquivo = garantir_tom(alarme)
    subprocess.Popen(
        ["pw-play", str(arquivo)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
