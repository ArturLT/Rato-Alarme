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


def carregar(lado: int, nomes=NOMES, prefixo: str = "rato-", montador=None) -> dict[str, Animacao]:
    """lado é o tamanho na tela do quadro de 48 px; folhas menores encolhem na mesma proporção.
    montador (aparencia.Montador) veste o rato: pelo, roupa e acessórios."""
    animacoes = {}
    for nome in nomes:
        base = PASTA / f"{prefixo}{nome}"
        folha = json.loads(base.with_suffix(".json").read_text(encoding="utf-8"))
        imagem = QImage(str(base.with_suffix(".png")))
        if imagem.isNull():
            raise OSError(f"não consegui abrir {base.with_suffix('.png')}")
        clipe = clipe_da_folha(folha["meta"])
        vestir = montador is not None and montador.mexe and "ancoras" in folha["meta"]
        mascara = None
        if vestir:
            mascara = QImage(str(PASTA / f"{prefixo}{nome}.mascara.png"))
            mascara = None if mascara.isNull() else mascara
        ancoras = folha["meta"].get("ancoras") or []
        direita, esquerda = [], []
        for i, quadro in enumerate(folha["frames"][: clipe.quadros]):
            r = quadro["frame"]
            w, h = round(lado * r["w"] / 48), round(lado * r["h"] / 48)
            recorte = imagem.copy(r["x"], r["y"], r["w"], r["h"])
            if vestir:
                pedaco = mascara.copy(r["x"], r["y"], r["w"], r["h"]) if mascara is not None else None
                recorte = montador.vestir(recorte, pedaco, ancoras[i] if i < len(ancoras) else None, nome)
            ampliado = recorte.scaled(
                w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation
            )
            pixmap = QPixmap.fromImage(ampliado)
            direita.append(pixmap)
            esquerda.append(pixmap.transformed(ESPELHO))
        animacoes[nome] = Animacao(clipe, direita, esquerda)
    return animacoes
