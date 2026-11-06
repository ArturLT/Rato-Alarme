"""Carrega as folhas de sprites do PixelFX em texturas, ampliadas sem borrar."""

import json
from pathlib import Path

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf, GLib

from alarma.animacao import NOMES, Clipe, clipe_da_folha

PASTA = Path(__file__).parent / "folhas"


class Animacao:
    def __init__(self, clipe: Clipe, direita: list, esquerda: list) -> None:
        self.clipe = clipe
        self.direita = direita
        self.esquerda = esquerda


def _textura(imagem: GdkPixbuf.Pixbuf) -> Gdk.Texture:
    _ok, dados = imagem.save_to_bufferv("png", [], [])
    return Gdk.Texture.new_from_bytes(GLib.Bytes.new(dados))


def carregar(lado: int) -> dict[str, Animacao]:
    animacoes = {}
    for nome in NOMES:
        base = PASTA / f"rato-{nome}"
        folha = json.loads(base.with_suffix(".json").read_text(encoding="utf-8"))
        imagem = GdkPixbuf.Pixbuf.new_from_file(str(base.with_suffix(".png")))
        clipe = clipe_da_folha(folha["meta"])
        direita, esquerda = [], []
        for quadro in folha["frames"][: clipe.quadros]:
            r = quadro["frame"]
            recorte = imagem.new_subpixbuf(r["x"], r["y"], r["w"], r["h"])
            ampliado = recorte.scale_simple(lado, lado, GdkPixbuf.InterpType.NEAREST)
            direita.append(_textura(ampliado))
            esquerda.append(_textura(ampliado.flip(True)))
        animacoes[nome] = Animacao(clipe, direita, esquerda)
    return animacoes
