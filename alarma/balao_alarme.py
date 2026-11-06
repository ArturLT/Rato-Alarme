"""O balão de fala do rato do alarme: uma janela própria, que nunca recebe clique nem foco.

O do pet fica em balao.py: lá o balão recebe clique e cada fala abre uma janela nova.
"""

from dataclasses import dataclass

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontDatabase, QFontMetrics, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from alarma.caca import LADO_RATO

TITULO = "alarma-balao"
LARGURA = 300
ALTURA = 124
PONTA = 18
BORDA = 3
RESPIRO = 14
TAMANHO_LETRA = 15
LETRA_MS = 45
LEITURA_MS = 2_500
# Onde fica a boca do rato na folha, olhando para a direita, em fração do lado.
BOCA_X = 0.83
TOPO_DA_CABECA = 0.46
ESCURO = QColor("#17121c")
CLARO = QColor("#fff4e6")


@dataclass(frozen=True)
class Lugar:
    x: int
    y: int
    acima: bool
    ponta: int


def lugar(rato_x: int, rato_y: int, esquerda: bool, area: tuple[int, int, int, int]) -> Lugar:
    """Acima da cabeça do rato. Sem espaço em cima, vai para baixo dele."""
    x0, y0, x1, y1 = area
    boca = rato_x + round(LADO_RATO * (1 - BOCA_X if esquerda else BOCA_X))
    x = min(max(boca - LARGURA // 2, x0), x1 - LARGURA)
    y = rato_y + round(LADO_RATO * TOPO_DA_CABECA) - ALTURA
    acima = y >= y0
    if not acima:
        y = min(rato_y + LADO_RATO, y1 - ALTURA)
    return Lugar(x, y, acima, min(max(boca - x, 2 * PONTA), LARGURA - 2 * PONTA))


def duracao_s(texto: str) -> float:
    return (len(texto) * LETRA_MS + LEITURA_MS) / 1000


def quebrar(texto: str, medidas: QFontMetrics, largura: int) -> list[str]:
    """Quebra antes de digitar, para a palavra não pular de linha no meio da escrita."""
    linhas: list[str] = []
    for palavra in texto.split():
        junto = f"{linhas[-1]} {palavra}" if linhas else palavra
        if linhas and medidas.horizontalAdvance(junto) <= largura:
            linhas[-1] = junto
        else:
            linhas.append(palavra)
    return linhas


def fonte() -> QFont:
    letra = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
    letra.setPixelSize(TAMANHO_LETRA)
    letra.setBold(True)
    return letra


class Balao(QWidget):
    """Fica aberta e vazia enquanto o rato está na tela: no Hyprland, abrir a janela a
    cada fala mostraria ela fora do lugar antes de mover."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(TITULO)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
            | Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)
        self.setFixedSize(LARGURA, ALTURA)
        self.setFont(fonte())
        self._linhas: list[str] = []
        self._letras = 0
        self._acima = True
        self._ponta = LARGURA // 2
        self._relogio = QTimer(self, interval=LETRA_MS)
        self._relogio.timeout.connect(self._escrever)

    @property
    def aberto(self) -> bool:
        return bool(self._linhas)

    @property
    def digitando(self) -> bool:
        return self._relogio.isActive()

    def dizer(self, texto: str, onde: Lugar) -> None:
        self._acima = onde.acima
        self._ponta = onde.ponta
        self._linhas = quebrar(texto, self.fontMetrics(), LARGURA - 2 * RESPIRO)
        self._letras = 0
        self._relogio.start()
        self.update()

    def calar(self) -> None:
        self._relogio.stop()
        self._linhas = []
        self.update()

    def _escrever(self) -> None:
        self._letras += 1
        if self._letras >= sum(len(linha) for linha in self._linhas):
            self._relogio.stop()
        self.update()

    def _corpo(self) -> QRect:
        return QRect(0, 0 if self._acima else PONTA, LARGURA, ALTURA - PONTA)

    def _desenhar_caixa(self, pintor: QPainter) -> None:
        """Cantos em degrau e ponta em escada, para combinar com o pixel do rato."""
        corpo = self._corpo()
        for cor, recuo in ((ESCURO, 0), (CLARO, BORDA)):
            for r in (
                corpo.adjusted(recuo + BORDA, recuo, -recuo - BORDA, -recuo),
                corpo.adjusted(recuo, recuo + BORDA, -recuo, -recuo - BORDA),
            ):
                pintor.fillRect(r, cor)
        degraus = PONTA // BORDA
        for i in range(degraus + 1):
            meia = (degraus - i) * 4
            y = corpo.bottom() - BORDA + 1 + i * BORDA if self._acima else corpo.top() - i * BORDA
            pintor.fillRect(self._ponta - meia - BORDA, y, 2 * (meia + BORDA), BORDA, ESCURO)
            pintor.fillRect(self._ponta - meia, y, 2 * meia, BORDA, CLARO)

    def paintEvent(self, _evento: QPaintEvent) -> None:
        if not self._linhas:
            return
        pintor = QPainter(self)
        self._desenhar_caixa(pintor)
        pintor.setPen(ESCURO)
        medidas = self.fontMetrics()
        altura = medidas.lineSpacing() * len(self._linhas)
        corpo = self._corpo()
        y = corpo.top() + (corpo.height() - altura) // 2 + medidas.ascent()
        restam = self._letras
        for linha in self._linhas:
            pintor.drawText(RESPIRO, y, linha[: max(restam, 0)])
            restam -= len(linha)
            y += medidas.lineSpacing()
