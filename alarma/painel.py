"""Painel de controle. Só grava o arquivo de configuração: o rato e a bandeja releem."""

from datetime import time

from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from alarma import config, inicio, sistema
from alarma.versao import VERSAO


def _campo_hora() -> QTimeEdit:
    campo = QTimeEdit()
    campo.setDisplayFormat("HH:mm")
    campo.setWrapping(True)
    return campo


def _discreto(rotulo: QLabel) -> QLabel:
    rotulo.setForegroundRole(QPalette.ColorRole.PlaceholderText)
    return rotulo


def _rotulo(texto: str, dica: str) -> QWidget:
    caixa = QWidget()
    colunas = QVBoxLayout(caixa)
    colunas.setContentsMargins(0, 0, 0, 0)
    colunas.addWidget(QLabel(texto))
    colunas.addWidget(_discreto(QLabel(dica, wordWrap=True)))
    return caixa


class Painel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Rato-Alarme")
        self._entrada = _campo_hora()
        self._saida = _campo_hora()
        self._alarme = QCheckBox()
        self._fechar = QCheckBox()
        self._inicio = QCheckBox()

        linhas = [
            ("Horário de entrada", "Nessa hora o rato aparece e toca o alarme.", self._entrada),
            ("Horário de saída", "Nessa hora o rato aparece de novo.", self._saida),
            ("Alarme ligado", "Desligado, o rato some e não volta até você ligar de novo.", self._alarme),
        ]
        if sistema.mexe_em_outras_janelas():
            linhas.append(
                ("Rato pode fechar janelas", "Desligado, ele continua com as outras travessuras.", self._fechar)
            )
        if inicio.gerenciado():
            linhas.append(
                ("Iniciar com o computador", "Desligado, o rato só roda quando você abrir o programa.", self._inicio)
            )

        grade = QGridLayout()
        grade.setVerticalSpacing(16)
        grade.setHorizontalSpacing(24)
        grade.setColumnStretch(0, 1)
        for linha, (texto, dica, controle) in enumerate(linhas):
            grade.addWidget(_rotulo(texto, dica), linha, 0)
            grade.addWidget(controle, linha, 1, Qt.AlignmentFlag.AlignRight)

        self._aviso = QLabel(wordWrap=True)
        salvar = QPushButton("Salvar")
        salvar.setDefault(True)
        salvar.clicked.connect(self.salvar)
        rodape = QHBoxLayout()
        rodape.addWidget(self._aviso, 1)
        rodape.addWidget(salvar)

        corpo = QVBoxLayout(self)
        corpo.setContentsMargins(20, 20, 20, 20)
        corpo.setSpacing(20)
        corpo.addLayout(grade)
        corpo.addLayout(rodape)
        corpo.addWidget(_discreto(QLabel(f"Versão {VERSAO}")))
        self.setFixedWidth(440)

    def abrir(self) -> None:
        self._preencher(config.carregar(config.caminho_padrao()))
        self.show()
        self.raise_()
        self.activateWindow()

    def _preencher(self, atual: config.Config) -> None:
        self._entrada.setTime(QTime(atual.entrada.hour, atual.entrada.minute))
        self._saida.setTime(QTime(atual.saida.hour, atual.saida.minute))
        self._alarme.setChecked(atual.alarme_ligado)
        self._fechar.setChecked(atual.fechar_janela)
        self._inicio.setChecked(atual.iniciar_com_sistema)
        self._aviso.clear()

    def salvar(self) -> None:
        entrada, saida = self._entrada.time(), self._saida.time()
        novo = config.Config(
            time(entrada.hour(), entrada.minute()),
            time(saida.hour(), saida.minute()),
            self._alarme.isChecked(),
            self._fechar.isChecked(),
            self._inicio.isChecked(),
        )
        try:
            config.salvar(config.caminho_padrao(), novo)
        except ValueError:
            self._aviso.setText("A entrada precisa ser antes da saída.")
        except OSError:
            self._aviso.setText("Não consegui salvar a configuração.")
        else:
            inicio.aplicar(novo.iniciar_com_sistema)
            self._aviso.setText("Salvo.")
