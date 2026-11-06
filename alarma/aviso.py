"""Janela que avisa da versão nova e mostra o andamento da atualização."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLayout,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from alarma.versao import VERSAO

LARGURA = 380


class Aviso(QWidget):
    atualizar = Signal()
    abrir_site = Signal()

    def __init__(self) -> None:
        super().__init__(None, Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("Atualização do Rato-Alarme")
        self._titulo = QLabel()
        fonte = self._titulo.font()
        fonte.setBold(True)
        fonte.setPointSizeF(fonte.pointSizeF() * 1.2)
        self._titulo.setFont(fonte)
        self._texto = QLabel(wordWrap=True)
        self._texto.setFixedWidth(LARGURA)
        self._barra = QProgressBar()
        self._barra.setRange(0, 100)
        self._barra.hide()

        self._agora = QPushButton("Atualizar agora")
        self._agora.setDefault(True)
        self._agora.clicked.connect(self.atualizar)
        self._site = QPushButton("Abrir o site")
        self._site.clicked.connect(self.abrir_site)
        self._site.hide()
        self._depois = QPushButton("Depois")
        self._depois.clicked.connect(self.hide)
        botoes = QHBoxLayout()
        botoes.addStretch(1)
        botoes.addWidget(self._depois)
        botoes.addWidget(self._site)
        botoes.addWidget(self._agora)

        corpo = QVBoxLayout(self)
        corpo.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
        corpo.setContentsMargins(20, 20, 20, 20)
        corpo.setSpacing(12)
        corpo.addWidget(self._titulo)
        corpo.addWidget(self._texto)
        corpo.addWidget(self._barra)
        corpo.addLayout(botoes)

    def _trazer(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def oferecer(self, versao: str, explicacao: str) -> None:
        self._titulo.setText(f"Versão {versao} disponível")
        self._texto.setText(f"Você está na versão {VERSAO}. {explicacao}")
        self._barra.hide()
        self._site.hide()
        self._agora.setText("Atualizar agora")
        self._agora.show()
        self._depois.show()
        self._trazer()

    def trabalhando(self, texto: str, com_barra: bool) -> None:
        self._texto.setText(texto)
        self._barra.setValue(0)
        self._barra.setVisible(com_barra)
        self._site.hide()
        self._agora.hide()
        self._depois.hide()
        self._trazer()

    def progresso(self, porcentagem: int) -> None:
        self._barra.setValue(porcentagem)

    def falhou(self) -> None:
        self._texto.setText(
            "Não consegui atualizar. Sua versão continua funcionando. "
            "Tente de novo ou baixe pelo site."
        )
        self._barra.hide()
        self._agora.setText("Tentar de novo")
        self._agora.show()
        self._site.show()
        self._depois.show()
        self._trazer()
