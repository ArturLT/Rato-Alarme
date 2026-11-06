"""Move a janela do rato e acha o cursor. No Wayland o Qt não posiciona janelas."""

import os

from PySide6.QtCore import QPoint
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QWidget

from alarma import hypr, sistema


class JanelaQt:
    """Mac e Windows: o próprio Qt lê o cursor e move a janela."""

    def __init__(self, janela: QWidget) -> None:
        self._janela = janela

    def pronta(self) -> bool:
        return True

    def esquecer(self) -> None:
        pass

    def cursor(self) -> tuple[int, int] | None:
        posicao = QCursor.pos()
        return posicao.x(), posicao.y()

    def area(self, cursor: tuple[int, int] | None) -> tuple[int, int, int, int] | None:
        tela = QGuiApplication.screenAt(QPoint(*cursor)) if cursor else None
        tela = tela or QGuiApplication.primaryScreen()
        if tela is None:
            return None
        g = tela.availableGeometry()
        return g.left(), g.top(), g.left() + g.width(), g.top() + g.height()

    def mover(self, x: int, y: int) -> None:
        self._janela.move(x, y)


class JanelaHyprland:
    def __init__(self, janela: QWidget) -> None:
        self._titulo = janela.windowTitle()
        self._endereco: str | None = None

    def pronta(self) -> bool:
        if self._endereco is None:
            self._endereco = hypr.endereco(os.getpid(), self._titulo)
            if self._endereco is None:
                return False
            hypr.preparar(self._endereco)
        return True

    def esquecer(self) -> None:
        self._endereco = None

    def cursor(self) -> tuple[int, int] | None:
        return hypr.cursor()

    def area(self, cursor: tuple[int, int] | None) -> tuple[int, int, int, int] | None:
        return hypr.area_do_cursor(cursor)

    def mover(self, x: int, y: int) -> None:
        if self._endereco is not None:
            hypr.mover(self._endereco, x, y)


def nova(janela: QWidget) -> JanelaQt | JanelaHyprland:
    return JanelaHyprland(janela) if sistema.tem_hyprland() else JanelaQt(janela)
