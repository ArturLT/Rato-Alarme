"""Sobe o rato, a bandeja e o painel em um processo só."""

import sys

from PySide6.QtWidgets import QApplication

from alarma import config, inicio, sprites
from alarma.bandeja import Bandeja
from alarma.caca import LADO_RATO
from alarma.criatura import APP_ID, Criatura
from alarma.painel import Painel
from alarma.unico import Instancia


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Rato-Alarme")
    app.setDesktopFileName(APP_ID)
    app.setQuitOnLastWindowClosed(False)

    if "--verificar" in sys.argv:
        sprites.carregar(LADO_RATO)
        return 0
    if "--demo" in sys.argv:
        criatura = Criatura(demo=True)
        criatura.iniciar()
        return app.exec()

    no_boot = "--boot" in sys.argv
    instancia = Instancia()
    if not instancia.assumir(avisar=not no_boot):
        return 0

    inicio.aplicar(config.carregar(config.caminho_padrao()).iniciar_com_sistema)
    criatura = Criatura()
    painel = Painel()
    bandeja = Bandeja(painel)
    instancia.pedido.connect(painel.abrir)
    criatura.iniciar()
    if not no_boot:
        painel.abrir()
    return app.exec()
