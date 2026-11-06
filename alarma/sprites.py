"""Carrega as folhas de sprites do PixelFX em pixmaps, ampliados sem borrar."""

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap, QTransform

from alarma.animacao import NOMES, Clipe, clipe_da_folha

PASTA = Path(__file__).parent / "folhas"
ESPELHO = QTransform().scale(-1, 1)


class Animacao:
    def __init__(self, clipe: Clipe, direita: list, esquerda: list) -> None:
        self.clipe = clipe
        self.direita = direita
        self.esquerda = esquerda


def carregar(lado: int) -> dict[str, Animacao]:
    animacoes = {}
    for nome in NOMES:
        base = PASTA / f"rato-{nome}"
        folha = json.loads(base.with_suffix(".json").read_text(encoding="utf-8"))
        imagem = QImage(str(base.with_suffix(".png")))
        if imagem.isNull():
            raise OSError(f"não consegui abrir {base.with_suffix('.png')}")
        clipe = clipe_da_folha(folha["meta"])
        direita, esquerda = [], []
        for quadro in folha["frames"][: clipe.quadros]:
            r = quadro["frame"]
            ampliado = imagem.copy(r["x"], r["y"], r["w"], r["h"]).scaled(
                lado, lado, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation
            )
            pixmap = QPixmap.fromImage(ampliado)
            direita.append(pixmap)
            esquerda.append(pixmap.transformed(ESPELHO))
        animacoes[nome] = Animacao(clipe, direita, esquerda)
    return animacoes
