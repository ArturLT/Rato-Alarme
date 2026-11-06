"""Janelinhas que acompanham o pet: balão de fala, placa de madeira e coisas largadas na tela.

Tudo é desenhado com QPainter em blocos de PIXEL px, para combinar com os sprites.
"""

import itertools

from PySide6.QtCore import QPoint, QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QMouseEvent, QPainter, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from alarma import janela

PIXEL = 3
TINTA = QColor("#17121c")
PAPEL = QColor("#fff4e6")
SOMBRA_PAPEL = QColor("#d6cabf")
MADEIRA = (QColor("#3a2010"), QColor("#7a4a20"), QColor("#b07838"), QColor("#d09a58"))
CREME = QColor("#fff4e6")
LARGURA_MAX = 300
_ids = itertools.count(1)


def fonte(tamanho: int = 13, negrito: bool = True) -> QFont:
    f = QFont()
    f.setFamilies(["Menlo", "Consolas", "DejaVu Sans Mono", "Courier New", "monospace"])
    f.setPointSize(tamanho)
    f.setBold(negrito)
    f.setStyleHint(QFont.StyleHint.Monospace)
    return f


class Flutuante(QWidget):
    """Janela sem moldura, transparente e por cima de tudo, que o pet posiciona."""

    def __init__(self, foco: bool = False) -> None:
        super().__init__()
        self.setWindowTitle(f"alarma-flutuante-{next(_ids)}")
        bandeiras = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool
        if not foco:
            bandeiras |= Qt.WindowType.WindowDoesNotAcceptFocus
        self.setWindowFlags(bandeiras)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, not foco)
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)
        self._tela = janela.nova(self)

    def posicionar(self, x: int, y: int) -> None:
        if self._tela.pronta():
            self._tela.mover(int(x), int(y))


def _caixa_pixelada(p: QPainter, r: QRect, fundo: QColor, borda: QColor, s: int = PIXEL) -> None:
    """Retângulo com cantos em degrau e borda de s px."""
    x0, y0, x1, y1 = r.left(), r.top(), r.right() + 1, r.bottom() + 1
    p.fillRect(QRect(x0 + 2 * s, y0, x1 - x0 - 4 * s, y1 - y0), borda)
    p.fillRect(QRect(x0 + s, y0 + s, x1 - x0 - 2 * s, y1 - y0 - 2 * s), borda)
    p.fillRect(QRect(x0, y0 + 2 * s, x1 - x0, y1 - y0 - 4 * s), borda)
    p.fillRect(QRect(x0 + 2 * s, y0 + s, x1 - x0 - 4 * s, y1 - y0 - 2 * s), fundo)
    p.fillRect(QRect(x0 + s, y0 + 2 * s, x1 - x0 - 2 * s, y1 - y0 - 4 * s), fundo)


class Balao(Flutuante):
    """Balão de fala com rabinho para baixo. Os botões ensinam o rato: ♥ gostei, ✕ não gostei."""

    gostei = Signal()
    nao_gostei = Signal()
    respondido = Signal(str)
    fechado = Signal()

    RABO = 5 * PIXEL

    def __init__(self, texto: str, votar: bool = False, pergunta: bool = False) -> None:
        super().__init__(foco=pergunta)
        self._respondeu = False
        self._texto = QLabel(texto, wordWrap=True)
        self._texto.setFont(fonte(12))
        self._texto.setStyleSheet(f"color: {TINTA.name()}; background: transparent;")
        self._texto.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        corpo = QVBoxLayout(self)
        m = 5 * PIXEL
        corpo.setContentsMargins(m, m - PIXEL, m, m + self.RABO - PIXEL)
        corpo.setSpacing(6)
        corpo.addWidget(self._texto)
        self.campo: QLineEdit | None = None
        if pergunta:
            self.campo = QLineEdit()
            self.campo.setPlaceholderText("Escreva e aperte Enter")
            self.campo.setFont(fonte(11, False))
            self.campo.setStyleSheet(
                f"QLineEdit {{ background: white; color: {TINTA.name()}; border: {PIXEL}px solid {TINTA.name()}; padding: 3px; }}"
            )
            self.campo.returnPressed.connect(self._responder)
            corpo.addWidget(self.campo)
        if votar or pergunta:
            linha = QHBoxLayout()
            linha.addStretch(1)
            if votar:
                linha.addWidget(self._botao("♥", "Gostei: fala mais disso", self.gostei.emit))
                linha.addWidget(self._botao("✕", "Não gostei: fala menos disso", self.nao_gostei.emit))
            else:
                linha.addWidget(self._botao("pular", "Não quero responder", self.fechar))
            corpo.addLayout(linha)
        metrica = QFontMetrics(self._texto.font())
        largura = min(LARGURA_MAX, metrica.horizontalAdvance(texto) + 2 * m + 4)
        largura = max(largura, 230 if pergunta else 120 if votar else 60)
        self.setFixedWidth(largura)
        corpo.activate()
        self.setFixedHeight(max(corpo.totalHeightForWidth(largura), corpo.totalMinimumSize().height()))

    def _botao(self, texto: str, dica: str, acao) -> QPushButton:
        botao = QPushButton(texto)
        botao.setToolTip(dica)
        botao.setCursor(Qt.CursorShape.PointingHandCursor)
        botao.setFont(fonte(11))
        botao.setStyleSheet(
            f"QPushButton {{ color: {TINTA.name()}; background: {SOMBRA_PAPEL.name()}; border: {PIXEL}px solid {TINTA.name()};"
            f" padding: 1px 7px; }} QPushButton:hover {{ background: white; }}"
        )
        botao.clicked.connect(acao)
        botao.clicked.connect(self.fechar)
        return botao

    def _responder(self) -> None:
        if self.campo is None:
            return
        texto = self.campo.text().strip()
        if texto:
            self._respondeu = True
            self.respondido.emit(texto)
        self.fechar()

    @property
    def respondeu(self) -> bool:
        return self._respondeu

    def fechar(self) -> None:
        if self.isVisible():
            self.hide()
            self.fechado.emit()
        self.deleteLater()

    def ponta(self) -> QPoint:
        """Onde fica a ponta do rabinho, relativa à janela."""
        return QPoint(self.width() // 2 - 6 * PIXEL, self.height())

    def paintEvent(self, _evento) -> None:
        p = QPainter(self)
        s = PIXEL
        corpo = QRect(0, 0, self.width(), self.height() - self.RABO)
        _caixa_pixelada(p, corpo, PAPEL, TINTA)
        p.fillRect(QRect(corpo.left() + 2 * s, corpo.bottom() - 2 * s, corpo.width() - 4 * s, s), SOMBRA_PAPEL)
        # rabinho em degraus, apontando para a cabeça do rato
        base = self.width() // 2 - 6 * s
        for i in range(4):
            y = corpo.bottom() + 1 + i * s - s
            w = (4 - i) * s
            p.fillRect(QRect(base - s, y, w + 2 * s, s + 1), TINTA)
            if i < 3:
                p.fillRect(QRect(base, y, w, s + 1), PAPEL)
        p.end()


class Placa(Flutuante):
    """Placa de madeira presa no cabo que o rato segura. Título pequeno em cima, recado embaixo."""

    clicada = Signal()

    def __init__(self, titulo: str, texto: str) -> None:
        super().__init__()
        self._titulo = titulo.upper()
        self._texto = texto
        self._fonte_titulo = fonte(9)
        self._fonte = fonte(12)
        metrica = QFontMetrics(self._fonte)
        m = 7 * PIXEL
        largura = max(160, min(LARGURA_MAX + 40, metrica.horizontalAdvance(texto) + 2 * m))
        caixa = metrica.boundingRect(QRect(0, 0, largura - 2 * m, 2000), Qt.TextFlag.TextWordWrap, texto)
        altura_titulo = QFontMetrics(self._fonte_titulo).height() + 2 * PIXEL if titulo else 0
        self.setFixedSize(QSize(largura, caixa.height() + altura_titulo + 2 * m))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Clique para tirar a placa")

    def mousePressEvent(self, _evento: QMouseEvent) -> None:
        self.clicada.emit()

    def base(self) -> QPoint:
        """Onde o cabo encosta: meio da borda de baixo."""
        return QPoint(self.width() // 2, self.height())

    def paintEvent(self, _evento) -> None:
        p = QPainter(self)
        s = PIXEL
        escuro, medio, claro, brilho = MADEIRA
        r = QRect(0, 0, self.width(), self.height())
        _caixa_pixelada(p, r, medio, escuro)
        dentro = r.adjusted(2 * s, 2 * s, -2 * s, -2 * s)
        p.fillRect(dentro, claro)
        # tábuas
        tabua = max(6 * s, dentro.height() // 3)
        y = dentro.top() + tabua
        while y < dentro.bottom() - 2 * s:
            p.fillRect(QRect(dentro.left(), y, dentro.width(), s), medio)
            y += tabua
        p.fillRect(QRect(dentro.left(), dentro.top(), dentro.width(), s), brilho)
        for x, y in ((dentro.left() + s, dentro.top() + s), (dentro.right() - 2 * s, dentro.top() + s)):
            p.fillRect(QRect(x, y, s, s), escuro)
        m = 7 * PIXEL
        topo = m - 2 * PIXEL
        if self._titulo:
            p.setFont(self._fonte_titulo)
            p.setPen(escuro)
            altura = QFontMetrics(self._fonte_titulo).height()
            p.drawText(QRect(m, topo, self.width() - 2 * m, altura), Qt.AlignmentFlag.AlignHCenter, self._titulo)
            topo += altura + 2 * PIXEL
        p.setFont(self._fonte)
        area = QRect(m, topo, self.width() - 2 * m, self.height() - topo - m + 2 * PIXEL)
        p.setPen(escuro)
        p.drawText(area.translated(0, 2), Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignHCenter, self._texto)
        p.setPen(CREME)
        p.drawText(area, Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignHCenter, self._texto)
        p.end()


class Objeto(Flutuante):
    """Coisa que o rato largou. Some quando clicada ou quando o tempo acaba."""

    clicado = Signal(object)
    DURA_MS = 30 * 60 * 1000

    def __init__(self, nome: str, quadros: list[QPixmap], fps: int, recado: str = "") -> None:
        super().__init__()
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.nome = nome
        self.recado = recado
        self._quadros = quadros
        self._i = 0
        self.setFixedSize(quadros[0].size())
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip(recado or "Clique para tirar")
        if len(quadros) > 1:
            self._relogio = QTimer(self, interval=max(40, 1000 // max(1, fps)))
            self._relogio.timeout.connect(self._avancar)
            self._relogio.start()
        QTimer.singleShot(self.DURA_MS, self.close)

    def _avancar(self) -> None:
        self._i = (self._i + 1) % len(self._quadros)
        self.update()

    def mousePressEvent(self, _evento: QMouseEvent) -> None:
        self.clicado.emit(self)

    def paintEvent(self, _evento) -> None:
        p = QPainter(self)
        p.drawPixmap(0, 0, self._quadros[self._i])
        p.end()
