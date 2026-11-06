"""Peças de interface em pixel art para o painel e os menus.

Tudo é pintado com QPainter em blocos de PX pixels: molduras com borda em degrau,
botões com relevo, interruptores, barras de status, um deslizante com queijo no
lugar do botão e uma fonte de 5x7 (do PixelFX) com acentos desenhados por cima.
"""

import atexit
import gc
import unicodedata
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QAbstractButton, QApplication, QCheckBox, QFrame, QLabel, QPushButton, QSlider, QSizePolicy, QWidget
from shiboken6 import Shiboken

from alarma.pixelfonte import ALTURA, GLIFOS

PX = 3
FOLHAS = Path(__file__).parent / "folhas"

COR = {
    "fundo": "#1b1424",
    "fundo2": "#231a2e",
    "painel": "#2a2036",
    "painel2": "#352944",
    "claro": "#4a3a5e",
    "borda": "#0e0a14",
    "brilho": "#6a5884",
    "texto": "#fff4e6",
    "suave": "#b8a8c8",
    "apagado": "#7a6a8e",
    "queijo": "#ffd23a",
    "queijo2": "#e09018",
    "vida": "#ff5a6a",
    "vida2": "#a02838",
    "verde": "#58d068",
    "verde2": "#2a8a40",
    "azul": "#5ab8ff",
    "azul2": "#2a5a9a",
    "rosa": "#ff8ab8",
    "rosa2": "#b04a7a",
    "roxo": "#a07ae0",
    "madeira": "#b07838",
    "madeira2": "#7a4a20",
    "madeira3": "#3a2010",
    "madeira4": "#d09a58",
}


def cor(nome: str) -> QColor:
    return QColor(COR.get(nome, nome))


def fonte_texto(tamanho: int = 12, negrito: bool = False) -> QFont:
    f = QFont()
    f.setFamilies(["Menlo", "SF Mono", "Consolas", "DejaVu Sans Mono", "Courier New", "monospace"])
    f.setPointSize(tamanho)
    f.setBold(negrito)
    f.setStyleHint(QFont.StyleHint.Monospace)
    return f


# ---- fonte pixel ----

_ACENTOS = {
    "́": [(1, 0), (0, 1)],  # agudo ´ (relativo ao meio, sobe à direita)
    "̀": [(-1, 0), (0, 1)],  # grave `
    "̂": [(-1, 1), (0, 0), (1, 1)],  # circunflexo ^
    "̃": [(-1, 1), (0, 0), (1, 1), (2, 0)],  # til ~
    "̈": [(-1, 1), (1, 1)],  # trema
}


def _glifo(ch: str) -> tuple[list[str], list[tuple[int, int]], bool]:
    """(linhas, acento, cedilha) de um caractere. Minúscula vira maiúscula."""
    decomposto = unicodedata.normalize("NFD", ch.upper())
    base = decomposto[0] if decomposto else ch
    marcas = decomposto[1:]
    linhas = GLIFOS.get(base) or GLIFOS.get(ch.upper())
    if linhas is None:
        return [], [], False
    acento = []
    for m in marcas:
        acento += _ACENTOS.get(m, [])
    return linhas, acento, "̧" in marcas


def largura_pixel(texto: str, escala: int = PX) -> int:
    w = 0
    for ch in texto:
        linhas, _, _ = _glifo(ch)
        w += (len(linhas[0]) if linhas else 3) + 1
    return max(0, (w - 1) * escala)


@lru_cache(maxsize=512)
def texto_pixel(texto: str, escala: int = PX, tinta: str = "texto", sombra: str | None = "borda") -> QPixmap:
    """O texto na fonte 5x7, com 2 linhas de folga em cima para os acentos e 2 embaixo para cedilha e sombra."""
    w = max(1, largura_pixel(texto, 1) + 1)
    h = ALTURA + 4
    img = QImage(w * escala + escala, h * escala + escala, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    camadas = ([(sombra, escala, escala)] if sombra else []) + [(tinta, 0, 0)]
    for nome, ox, oy in camadas:
        c = cor(nome)
        x = 0
        for ch in texto:
            linhas, acento, cedilha = _glifo(ch)
            if not linhas:
                x += 4
                continue
            larg = len(linhas[0])
            for j, linha in enumerate(linhas):
                for i, v in enumerate(linha):
                    if v == "#":
                        p.fillRect((x + i) * escala + ox, (j + 2) * escala + oy, escala, escala, c)
            meio = larg // 2
            for dx, dy in acento:
                p.fillRect((x + meio + dx) * escala + ox, dy * escala + oy, escala, escala, c)
            if cedilha:
                p.fillRect((x + meio) * escala + ox, (ALTURA + 2) * escala + oy, escala, escala, c)
                p.fillRect((x + meio - 1) * escala + ox, (ALTURA + 3) * escala + oy, escala, escala, c)
            x += larg + 1
    p.end()
    return QPixmap.fromImage(img)


class RotuloPixel(QLabel):
    """Um título na fonte pixel."""

    def __init__(self, texto: str = "", escala: int = PX, tinta: str = "texto", sombra: str | None = "borda") -> None:
        super().__init__()
        self._escala, self._tinta, self._sombra = escala, tinta, sombra
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.definir(texto)

    def definir(self, texto: str, tinta: str | None = None) -> None:
        self._texto = texto
        if tinta:
            self._tinta = tinta
        self.setPixmap(texto_pixel(texto, self._escala, self._tinta, self._sombra))

    def texto(self) -> str:
        return self._texto


# ---- molduras ----

ESTILOS = {
    # fundo, borda de fora, luz (cima/esquerda), sombra (baixo/direita)
    "painel": ("painel", "borda", "claro", "fundo2"),
    "fundo": ("fundo2", "borda", "painel", "fundo"),
    "madeira": ("madeira", "madeira3", "madeira4", "madeira2"),
    "botao": ("claro", "borda", "brilho", "painel"),
    "botao_hover": ("brilho", "borda", "suave", "claro"),
    "botao_apertado": ("painel2", "borda", "fundo2", "claro"),
    "botao_ligado": ("queijo2", "borda", "queijo", "madeira2"),
    "verde": ("verde2", "borda", "verde", "#1a5a28"),
    "vermelho": ("vida2", "borda", "vida", "#5a1020"),
    "campo": ("fundo", "borda", "fundo2", "painel"),
}


def moldura(p: QPainter, r: QRect, estilo: str = "painel", s: int = PX) -> None:
    """Retângulo com cantos em degrau, borda escura e relevo de um pixel."""
    fundo, borda, luz, sombra = (cor(c) for c in ESTILOS.get(estilo, ESTILOS["painel"]))
    x0, y0, w, h = r.x(), r.y(), r.width(), r.height()
    if w < 4 * s or h < 4 * s:
        p.fillRect(r, fundo)
        return
    p.fillRect(QRect(x0 + s, y0, w - 2 * s, h), borda)
    p.fillRect(QRect(x0, y0 + s, w, h - 2 * s), borda)
    p.fillRect(QRect(x0 + s, y0 + s, w - 2 * s, h - 2 * s), fundo)
    p.fillRect(QRect(x0 + s, y0 + s, w - 2 * s, s), luz)
    p.fillRect(QRect(x0 + s, y0 + s, s, h - 2 * s), luz)
    p.fillRect(QRect(x0 + s, y0 + h - 2 * s, w - 2 * s, s), sombra)
    p.fillRect(QRect(x0 + w - 2 * s, y0 + 2 * s, s, h - 3 * s), sombra)


class Moldura(QFrame):
    """Um QFrame pintado com moldura pixel. Ponha um layout dentro."""

    def __init__(self, estilo: str = "painel") -> None:
        super().__init__()
        self._estilo = estilo
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def definir_estilo(self, estilo: str) -> None:
        self._estilo = estilo
        self.update()

    def paintEvent(self, _evento) -> None:
        p = QPainter(self)
        moldura(p, self.rect(), self._estilo)
        p.end()


# ---- ícones ----

_ICONE_CORES = {
    "k": "#0e0a14", "w": "#fff4e6", "y": "#ffd23a", "Y": "#fff0a0", "o": "#e09018", "r": "#ff5a6a", "R": "#a02838",
    "g": "#58d068", "G": "#2a8a40", "b": "#5ab8ff", "B": "#2a5a9a", "p": "#ff8ab8", "P": "#8a5ac8", "s": "#8a84a0",
    "S": "#c8c0d8", "m": "#b07838", "n": "#5a3a18", "l": "#a07ae0",
}
ICONES = {
    "casa": ["....kk....", "...kRRk...", "..kRRRRk..", ".kRRRRRRk.", "kkkkkkkkkk", ".kSSSSSSk.", ".kSkkSbbk.", ".kSkmkSSk.", ".kSkmkSSk.", ".kkkkkkkk."],
    "chapeu": ["...kkkk...", "..kPPPPk..", "..kPllPk..", "..kPPPPk..", "..kPPPPk..", "..krrrrk..", "kkkkkkkkkk", "kPPPPPPPPk", "kkkkkkkkkk", ".........."],
    "engrenagem": ["...k..k...", "..kkSSkk..", ".kSSSSSSk.", "kkSkkkkSkk", ".kSk..kSk.", ".kSk..kSk.", "kkSkkkkSkk", ".kSSSSSSk.", "..kkSSkk..", "...k..k..."],
    "cadeado": ["...kkkk...", "..kSkkSk..", "..kS..Sk..", "..kS..Sk..", ".kkkkkkkk.", ".kyyyyyyk.", ".kyykkyyk.", ".kyykkyyk.", ".kooooook.", ".kkkkkkkk."],
    "balao": [".kkkkkkkk.", "kwwwwwwwwk", "kwkwkwkwwk", "kwwwwwwwwk", "kwkkkkwwwk", "kwwwwwwwwk", ".kkwkkkkk.", "..kwk.....", "..kk......", ".........."],
    "relogio": ["..kkkkkk..", ".kwwwwwwk.", "kwwwkwwwwk", "kwwwkwwwwk", "kwwwkkkwwk", "kwwwwwwwwk", "kwwwwwwwwk", ".kwwwwwwk.", "..kkkkkk..", ".........."],
    "cerebro": ["..kkkkk...", ".kppppPk..", "kpPpppPpk.", "kppPpPppk.", "kpPppppPk.", "kppPpPppk.", ".kpppPpk..", "..kkpkk...", "....kk....", ".........."],
    "sino": ["....kk....", "...kyyk...", "..kyYyyk..", "..kyYyyk..", "..kyyyyk..", ".kyyyyyyk.", "kyyyyyyyyk", "kkkkkkkkkk", "....ko....", ".....k...."],
    "queijo": [".........k", ".......kky", ".....kkyyk", "...kkyyyyk", ".kkyyykyyk", "kyyyyyyyyk", "kyykyyyyok", "kyyyyyykok", "koooooooko", "kkkkkkkkkk"],
    "bola": ["..kkkkk...", ".krRrrrk..", "kwRrrrrrk.", "kRrrrrrRk.", "krrrrrRRk.", "krrrrRRRk.", ".kRRRRRk..", "..kkkkk...", "..........", ".........."],
    "coracao": [".kk...kk..", "kppk.kppk.", "kpwpkpppk.", "kpppppppk.", "kpppppppk.", ".kpppppk..", "..kpppk...", "...kpk....", "....k.....", ".........."],
    "joia": ["....kk....", "...kyyk...", "...kyyk...", "..kyyyk...", "kkkyyyykk.", "kyyyyyyyk.", "kyyyyyyyk.", "kyyyyyyyk.", "kyyyyyyk..", ".kkkkkk..."],
    "nao": ["kk......kk", "krk....krk", ".krk..krk.", "..krkkrk..", "...krrk...", "...krrk...", "..krkkrk..", ".krk..krk.", "krk....krk", "kk......kk"],
    "lua": ["...kkkk...", "..kbbbBk..", ".kbbBkk...", ".kbBk.....", ".kbBk.....", ".kbBk.....", ".kbbBkk...", "..kbbbBk..", "...kkkk...", ".........."],
    "tchau": ["..k.k.k...", ".kmkmkmk..", ".kmkmkmkk.", ".kmmmmmkmk", ".kmmmmmmmk", ".kmmmmmmk.", "..kmmmmk..", "...kmmk...", "...kkkk...", ".........."],
    "mais": ["....kk....", "...kgGk...", "...kgGk...", "kkkkgGkkkk", "kggggggggk", "kGGGGGGGGk", "kkkkgGkkkk", "...kgGk...", "...kgGk...", "....kk...."],
    "lixo": ["...kkkk...", "kkkkkkkkkk", "kSSSSSSSSk", ".kkkkkkkk.", ".kSkSkSkk.", ".kSkSkSkk.", ".kSkSkSkk.", ".kSkSkSkk.", ".kSSSSSSk.", ".kkkkkkkk."],
    "lapis": ["......kkk.", ".....kprk.", "....kyyk..", "...kyyk...", "..kyyk....", ".kyyk.....", "kmyk......", "knmk......", "kkk.......", ".........."],
    "dado": ["kkkkkkkkkk", "kwwwwwwwwk", "kwkwwwwkwk", "kwwwwwwwwk", "kwwwkkwwwk", "kwwwkkwwwk", "kwwwwwwwwk", "kwkwwwwkwk", "kwwwwwwwwk", "kkkkkkkkkk"],
    "estrela": ["....kk....", "....yk....", "...kyyk...", "kkkkyykkkk", ".kyyyyyyk.", "..kyyyyk..", "..kyykyk..", ".kyk..kyk.", ".kk....kk.", ".........."],
    "caveira": ["..kkkkkk..", ".kwwwwwwk.", "kwwwwwwwwk", "kwkkwwkkwk", "kwkkwwkkwk", "kwwwkkwwwk", ".kwwwwwwk.", "..kwkwkk..", "..kkkkkk..", ".........."],
    "sol": ["....y.....", ".y..y..y..", "..kkkkkk..", ".kyyyyyyk.", "ykyYyyyyky", ".kyyyyyyk.", ".kyyyyyyk.", "..kkkkkk..", ".y..y..y..", "....y....."],
    "raio": ["....kkkk..", "...kyyyk..", "..kyyyk...", ".kyyyyykk.", ".kkkyyyyk.", "...kyyyk..", "..kyyk....", "..kyk.....", ".kk.......", ".........."],
    "livro": [".kkkkkkkk.", "kBbbbkbbBk", "kBbbbkbbBk", "kBbwbkbwBk", "kBbbbkbbBk", "kBbwbkbwBk", "kBbbbkbbBk", "kBbbbkbbBk", "kkkkkkkkkk", ".........."],
    "rato": ["....kk.kk.", "...kppkppk", "..kssskkk.", ".kssskssk.", "kssssssswk", "kssssssskp", ".kssssssk.", "kpkkkkkkk.", ".pp.......", ".........."],
    "volta": ["...kkkk...", "..kgggGk..", ".kgk..kgk.", "kkk....kgk", ".......kgk", "..kk...kgk", ".kgk..kgk.", "..kgggGk..", "...kkkk...", ".........."],
    "comida": ["..k.k.k...", "..k.k.k...", "..kkkkk...", "...kmk....", "...kmk....", "...kmk....", "...kmk....", "...kmk....", "...kkk....", ".........."],
    "vassoura": ["......kk..", ".....kmk..", "....kmk...", "...kmk....", "..kkk.....", ".kyyyk....", "kyyoyyk...", "kyoyoyk...", ".kkkkk....", ".........."],
}


@lru_cache(maxsize=256)
def pixmap_icone(nome: str, escala: int = 2) -> QPixmap:
    arte = ICONES.get(nome)
    if arte is None:
        return QPixmap()
    w, h = max(len(l) for l in arte), len(arte)
    img = QImage(w * escala, h * escala, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    for j, linha in enumerate(arte):
        for i, ch in enumerate(linha):
            if ch in _ICONE_CORES:
                p.fillRect(i * escala, j * escala, escala, escala, QColor(_ICONE_CORES[ch]))
    p.end()
    return QPixmap.fromImage(img)


def icone(nome: str) -> QIcon:
    return QIcon(pixmap_icone(nome, 2))


@lru_cache(maxsize=64)
def pixmap_item(tipo: str, lado: int = 40) -> QPixmap:
    """O primeiro quadro de um objeto do rato (queijo, bolinha...), recortado e ampliado sem borrar."""
    import json

    try:
        folha = json.loads((FOLHAS / f"objeto-{tipo}.json").read_text(encoding="utf-8"))
        imagem = QImage(str(FOLHAS / f"objeto-{tipo}.png"))
        r = folha["frames"][0]["frame"]
    except (OSError, ValueError, KeyError, IndexError):
        return QPixmap()
    recorte = imagem.copy(r["x"], r["y"], r["w"], r["h"])
    return QPixmap.fromImage(recorte.scaled(lado, lado, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))


def icone_item(tipo: str) -> QIcon:
    return QIcon(pixmap_item(tipo, 32))


def _recortar(imagem: QImage) -> QImage:
    """Tira a borda transparente."""
    x0, y0, x1, y1 = imagem.width(), imagem.height(), -1, -1
    for y in range(imagem.height()):
        for x in range(imagem.width()):
            if imagem.pixelColor(x, y).alpha():
                x0, y0, x1, y1 = min(x0, x), min(y0, y), max(x1, x), max(y1, y)
    return imagem.copy(x0, y0, x1 - x0 + 1, y1 - y0 + 1) if x1 >= 0 else imagem


@lru_cache(maxsize=128)
def pixmap_acessorio(ident: str, lado: int = 32, cor_cabelo: str = "#7a4a2a") -> QPixmap:
    """O acessório de lado, recortado e ampliado em múltiplo inteiro (sem borrar). Cabelo na cor dada."""
    caminho = FOLHAS / "acessorios" / f"{ident}-lado.png"
    imagem = QImage(str(caminho))
    if imagem.isNull():
        return QPixmap()
    imagem = _recortar(imagem.convertToFormat(QImage.Format.Format_ARGB32))
    from alarma.aparencia import CABELO_BASE, rampa

    tons = rampa(cor_cabelo, 4)
    trocas = {QColor(v).rgb() & 0xFFFFFF: QColor(*t) for v, t in zip(CABELO_BASE, tons)}
    for y in range(imagem.height()):
        for x in range(imagem.width()):
            c = imagem.pixelColor(x, y)
            if c.alpha() and (c.rgb() & 0xFFFFFF) in trocas:
                imagem.setPixelColor(x, y, trocas[c.rgb() & 0xFFFFFF])
    k = max(1, lado // max(imagem.width(), imagem.height()))
    return QPixmap.fromImage(imagem.scaled(imagem.width() * k, imagem.height() * k, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation))


# ---- botões e controles ----


class BotaoPixel(QPushButton):
    """Botão com relevo pixel. Texto na fonte pixel, ícone opcional à esquerda."""

    def __init__(self, texto: str = "", icone_nome: str = "", estilo: str = "botao", escala: int = 2) -> None:
        super().__init__(texto)
        self._icone = icone_nome
        self._estilo = estilo
        self._escala = escala
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

    def sizeHint(self) -> QSize:
        largura = largura_pixel(self.text(), self._escala) + 6 * PX + (24 + 6 if self._icone else 0)
        return QSize(max(largura, 40), max(36, (ALTURA + 4) * self._escala + 4 * PX))

    def paintEvent(self, _evento) -> None:
        p = QPainter(self)
        apertado = self.isDown() or (self.isCheckable() and self.isChecked())
        if not self.isEnabled():
            estilo = "fundo"
        elif self.isCheckable() and self.isChecked():
            estilo = "botao_ligado"
        elif self.isDown():
            estilo = "botao_apertado"
        elif self.underMouse():
            estilo = "botao_hover" if self._estilo == "botao" else self._estilo
        else:
            estilo = self._estilo
        r = self.rect()
        desloca = PX if apertado else 0
        moldura(p, r, estilo)
        texto = texto_pixel(self.text(), self._escala, "texto" if self.isEnabled() else "apagado") if self.text() else None
        icone_px = pixmap_icone(self._icone, 2) if self._icone else None
        largura = (texto.width() if texto else 0) + (icone_px.width() + 6 if icone_px and texto else icone_px.width() if icone_px else 0)
        x = (r.width() - largura) // 2
        if icone_px:
            p.drawPixmap(x, (r.height() - icone_px.height()) // 2 + desloca, icone_px)
            x += icone_px.width() + 6
        if texto:
            p.drawPixmap(x, (r.height() - texto.height()) // 2 + desloca + PX // 2, texto)
        p.end()

    def enterEvent(self, evento) -> None:
        self.update()
        super().enterEvent(evento)

    def leaveEvent(self, evento) -> None:
        self.update()
        super().leaveEvent(evento)


class Interruptor(QCheckBox):
    """Liga e desliga em pixel art. Continua sendo um QCheckBox (isChecked, toggled...)."""

    def __init__(self, texto: str = "") -> None:
        super().__init__(texto)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(fonte_texto(12))

    def sizeHint(self) -> QSize:
        extra = self.fontMetrics().horizontalAdvance(self.text()) + 12 if self.text() else 0
        return QSize(16 * PX + extra, 9 * PX)

    def hitButton(self, ponto: QPoint) -> bool:
        return self.rect().contains(ponto)

    def paintEvent(self, _evento) -> None:
        p = QPainter(self)
        s = PX
        ligado = self.isChecked()
        trilho = QRect(0, (self.height() - 8 * s) // 2, 16 * s, 8 * s)
        moldura(p, trilho, "verde" if ligado and self.isEnabled() else "campo")
        botao = QRect(trilho.x() + (8 * s if ligado else s), trilho.y() + s, 7 * s, 6 * s)
        moldura(p, botao, "botao_hover" if self.isEnabled() else "fundo", s)
        if ligado:
            p.fillRect(QRect(trilho.x() + 3 * s, trilho.y() + 3 * s, s, 2 * s), cor("texto"))
        if self.text():
            p.setPen(cor("texto") if self.isEnabled() else cor("apagado"))
            p.setFont(self.font())
            p.drawText(QRect(trilho.right() + 12, 0, self.width(), self.height()), Qt.AlignmentFlag.AlignVCenter, self.text())
        p.end()


class Barra(QWidget):
    """Barra de status em gomos, com ícone e valor. tipo: vida, barriga, diversao, felicidade, xp."""

    CORES = {
        "vida": ("vida", "vida2"),
        "barriga": ("queijo", "queijo2"),
        "diversao": ("azul", "azul2"),
        "felicidade": ("rosa", "rosa2"),
        "xp": ("verde", "verde2"),
        "neutro": ("roxo", "claro"),
    }
    ICONE = {"vida": "coracao", "barriga": "queijo", "diversao": "bola", "felicidade": "estrela", "xp": "raio"}

    def __init__(self, tipo: str = "neutro", rotulo: str = "", gomos: int = 10, icone_visivel: bool = True, largura_rotulo: int = 0) -> None:
        super().__init__()
        self._tipo, self._rotulo, self._gomos = tipo, rotulo, gomos
        self._largura_rotulo = largura_rotulo
        self._valor = 0.0
        self._texto = ""
        self._icone = icone_visivel and tipo in self.ICONE
        self.setMinimumHeight(30)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def definir(self, valor: float, texto: str = "") -> None:
        self._valor = max(0.0, min(100.0, valor))
        self._texto = texto
        self.setToolTip(f"{self._rotulo}: {round(self._valor)}%" if self._rotulo else "")
        self.update()

    def valor(self) -> float:
        return self._valor

    def paintEvent(self, _evento) -> None:
        p = QPainter(self)
        s = PX
        x = 0
        if self._icone:
            ic = pixmap_icone(self.ICONE[self._tipo], 2)
            p.drawPixmap(0, (self.height() - ic.height()) // 2, ic)
            x = ic.width() + 6
        rotulo_px = texto_pixel(self._rotulo, 2, "suave") if self._rotulo else None
        if rotulo_px:
            p.drawPixmap(x, (self.height() - rotulo_px.height()) // 2 + 2, rotulo_px)
            x += max(rotulo_px.width(), self._largura_rotulo) + 8
        valor_txt = self._texto or f"{round(self._valor)}"
        valor_px = texto_pixel(valor_txt, 2, "texto")
        largura = self.width() - x - max(valor_px.width(), 34) - 8
        caixa = QRect(x, (self.height() - 8 * s) // 2, max(20, largura), 8 * s)
        moldura(p, caixa, "campo")
        claro, escuro = (cor(c) for c in self.CORES.get(self._tipo, self.CORES["neutro"]))
        if self._valor < 25 and self._tipo in ("vida", "barriga", "diversao", "felicidade"):
            claro, escuro = cor("vida"), cor("vida2")
        dentro = caixa.adjusted(2 * s, 2 * s, -2 * s, -2 * s)
        gw = dentro.width() / self._gomos
        cheios = self._valor / 100 * self._gomos
        for g in range(self._gomos):
            preenche = min(1.0, max(0.0, cheios - g))
            if preenche <= 0:
                continue
            gx = dentro.x() + round(g * gw)
            largura_gomo = max(1, round(gw * preenche) - (s if preenche >= 1 else 0))
            p.fillRect(QRect(gx, dentro.y(), largura_gomo, dentro.height()), escuro)
            p.fillRect(QRect(gx, dentro.y(), largura_gomo, max(1, dentro.height() // 2)), claro)
        p.drawPixmap(self.width() - valor_px.width(), (self.height() - valor_px.height()) // 2 + 2, valor_px)
        p.end()


class Pontos(QWidget):
    """Atributo de 0 a 5 em bolinhas pixel (inteligência, afeto...)."""

    def __init__(self, rotulo: str, tinta: str = "queijo") -> None:
        super().__init__()
        self._rotulo, self._tinta, self._valor = rotulo, tinta, 0
        self.setFixedHeight(24)
        self.setMinimumWidth(largura_pixel(rotulo, 2) + 5 * 14 + 14)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def definir(self, valor: int, dica: str = "") -> None:
        self._valor = max(0, min(5, valor))
        self.setToolTip(dica)
        self.update()

    def valor(self) -> int:
        return self._valor

    def paintEvent(self, _evento) -> None:
        p = QPainter(self)
        rot = texto_pixel(self._rotulo, 2, "suave")
        p.drawPixmap(0, (self.height() - rot.height()) // 2 + 2, rot)
        s = 2
        x = self.width() - 5 * 7 * s
        for i in range(5):
            r = QRect(x + i * 7 * s, (self.height() - 5 * s) // 2, 5 * s, 5 * s)
            p.fillRect(r.adjusted(s, 0, -s, 0), cor("borda"))
            p.fillRect(r.adjusted(0, s, 0, -s), cor("borda"))
            dentro = r.adjusted(s, s, -s, -s)
            p.fillRect(dentro, cor(self._tinta) if i < self._valor else cor("fundo"))
        p.end()


class Deslizante(QSlider):
    """QSlider pintado em pixel: trilho em degrau e um queijinho de botão."""

    def __init__(self) -> None:
        super().__init__(Qt.Orientation.Horizontal)
        self.setRange(0, 100)
        self.setSingleStep(5)
        self.setPageStep(10)
        self.setMinimumWidth(200)
        self.setFixedHeight(10 * PX)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def paintEvent(self, _evento) -> None:
        p = QPainter(self)
        s = PX
        botao = 8 * s
        trilho = QRect(botao // 2, (self.height() - 5 * s) // 2, self.width() - botao, 5 * s)
        moldura(p, trilho, "campo")
        k = (self.value() - self.minimum()) / max(1, self.maximum() - self.minimum())
        cheio = trilho.adjusted(2 * s, 2 * s, -2 * s, -2 * s)
        cheio.setWidth(max(0, round(cheio.width() * k)))
        p.fillRect(cheio, cor("queijo2"))
        p.fillRect(QRect(cheio.x(), cheio.y(), cheio.width(), s), cor("queijo"))
        x = trilho.x() + round((trilho.width()) * k) - botao // 2
        ic = pixmap_icone("queijo", 3)
        p.drawPixmap(x, (self.height() - ic.height()) // 2, ic)
        p.end()

    def mousePressEvent(self, evento) -> None:
        self._pular(evento.position().x())

    def mouseMoveEvent(self, evento) -> None:
        self._pular(evento.position().x())

    def _pular(self, x: float) -> None:
        botao = 8 * PX
        k = (x - botao / 2) / max(1, self.width() - botao)
        valor = self.minimum() + round(max(0.0, min(1.0, k)) * (self.maximum() - self.minimum()) / self.singleStep()) * self.singleStep()
        self.setValue(valor)


class Amostra(QAbstractButton):
    """Um quadradinho para escolher cor ou peça: cor lisa, uma imagem ou um texto."""

    escolhida = Signal(str)

    def __init__(self, chave: str, cor_hex: str = "", imagem: QPixmap | None = None, dica: str = "", lado: int = 44) -> None:
        super().__init__()
        self.chave = chave
        self._cor = cor_hex
        self._imagem = imagem
        self.setCheckable(True)
        self.setAutoExclusive(False)
        self.setToolTip(dica)
        self.setFixedSize(lado, lado)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self._clicou)

    def _clicou(self) -> None:
        self.escolhida.emit(self.chave)

    def paintEvent(self, _evento) -> None:
        p = QPainter(self)
        moldura(p, self.rect(), "botao_ligado" if self.isChecked() else "botao_hover" if self.underMouse() else "botao")
        dentro = self.rect().adjusted(3 * PX, 3 * PX, -3 * PX, -3 * PX)
        if self._cor:
            p.fillRect(dentro, QColor(self._cor))
            p.fillRect(QRect(dentro.x(), dentro.y(), dentro.width(), PX), QColor(255, 255, 255, 70))
        elif self._imagem is not None and not self._imagem.isNull():
            img = self._imagem
            p.drawPixmap(dentro.x() + (dentro.width() - img.width()) // 2, dentro.y() + (dentro.height() - img.height()) // 2, img)
        else:
            ic = pixmap_icone("nao", 2)
            p.drawPixmap(dentro.x() + (dentro.width() - ic.width()) // 2, dentro.y() + (dentro.height() - ic.height()) // 2, ic)
        p.end()

    def enterEvent(self, evento) -> None:
        self.update()
        super().enterEvent(evento)

    def leaveEvent(self, evento) -> None:
        self.update()
        super().leaveEvent(evento)


# ---- estilos de widgets comuns do Qt (campos, listas, menus) ----

ESTILO = f"""
QWidget {{ color: {COR['texto']}; font-family: Menlo, "SF Mono", Consolas, "DejaVu Sans Mono", monospace; font-size: 12px; }}
QLabel {{ background: transparent; }}
QToolTip {{ background: {COR['painel']}; color: {COR['texto']}; border: 3px solid {COR['borda']}; padding: 4px; }}
QLineEdit, QTimeEdit, QComboBox, QSpinBox {{
    background: {COR['fundo']}; color: {COR['texto']}; border: 3px solid {COR['borda']};
    border-top-color: {COR['borda']}; padding: 4px 6px; selection-background-color: {COR['queijo2']};
    min-height: 20px;
}}
QLineEdit:focus, QTimeEdit:focus, QComboBox:focus {{ border-color: {COR['queijo2']}; }}
QComboBox::drop-down, QTimeEdit::up-button, QTimeEdit::down-button {{ background: {COR['claro']}; border: 0; width: 16px; }}
QComboBox QAbstractItemView {{ background: {COR['painel']}; color: {COR['texto']}; border: 3px solid {COR['borda']};
    selection-background-color: {COR['claro']}; selection-color: {COR['queijo']}; }}
QListWidget, QTreeWidget {{ background: {COR['fundo']}; border: 3px solid {COR['borda']}; outline: 0; }}
QListWidget::item, QTreeWidget::item {{ padding: 4px; }}
QListWidget::item:selected, QTreeWidget::item:selected {{ background: {COR['claro']}; color: {COR['queijo']}; }}
QHeaderView::section {{ background: {COR['painel2']}; color: {COR['suave']}; border: 0; border-bottom: 3px solid {COR['borda']}; padding: 4px; }}
QScrollArea {{ background: transparent; border: 0; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: {COR['fundo']}; width: 14px; border: 0; }}
QScrollBar::handle:vertical {{ background: {COR['claro']}; border: 3px solid {COR['borda']}; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar:horizontal {{ height: 0; }}
QMessageBox {{ background: {COR['painel']}; }}
QMessageBox QPushButton {{ background: {COR['claro']}; border: 3px solid {COR['borda']}; padding: 6px 14px; color: {COR['texto']}; }}
"""

ESTILO_MENU = f"""
QMenu {{ background: {COR['painel']}; border: 3px solid {COR['borda']}; padding: 6px; color: {COR['texto']};
    font-family: Menlo, "SF Mono", Consolas, "DejaVu Sans Mono", monospace; font-size: 13px; font-weight: bold; }}
QMenu::item {{ padding: 7px 18px 7px 34px; border: 0; }}
QMenu::item:selected {{ background: {COR['claro']}; color: {COR['queijo']}; }}
QMenu::item:disabled {{ color: {COR['suave']}; }}
QMenu::separator {{ height: 3px; background: {COR['borda']}; margin: 5px 8px; }}
QMenu::icon {{ padding-left: 8px; }}
"""


def estilizar_menu(menu) -> None:
    menu.setStyleSheet(ESTILO_MENU)


def limpar() -> None:
    """Solta as imagens guardadas e as janelas antes do Qt fechar: QPixmap ou janela liberados depois do
    QApplication derrubam o programa na saída. O app chama isso ao sair; nos testes, roda no atexit."""
    for funcao in (texto_pixel, pixmap_icone, pixmap_item, pixmap_acessorio):
        funcao.cache_clear()
    app = QApplication.instance()
    if app is not None:
        for widget in list(app.topLevelWidgets()):
            if Shiboken.isValid(widget):
                liberar = getattr(widget, "liberar", None)
                if callable(liberar):
                    liberar()
                Shiboken.delete(widget)
    gc.collect()


atexit.register(limpar)
