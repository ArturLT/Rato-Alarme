"""Sobe o rato, a bandeja e o painel em um processo só."""

import gc
import sys

from PySide6.QtWidgets import QApplication, QWidget
from shiboken6 import Shiboken

from alarma import config, inicio, sprites
from alarma.bandeja import Bandeja
from alarma.caca import LADO_RATO
from alarma.criatura import APP_ID, Criatura
from alarma.painel import Painel
from alarma.pet import Pet
from alarma.unico import Instancia


def encerrar(objetos: dict) -> None:
    """Desmonta tudo enquanto o Qt ainda existe. Janela ou imagem liberada depois que o
    QApplication some derruba o programa na saída."""
    for objeto in objetos.values():
        desligar = getattr(objeto, "desligar", None)
        if callable(desligar):
            desligar()
    for objeto in objetos.values():
        if isinstance(objeto, QWidget) and Shiboken.isValid(objeto):
            liberar = getattr(objeto, "liberar", None)
            if callable(liberar):
                liberar()
            objeto.close()
            Shiboken.delete(objeto)
    from alarma import pixelui

    pixelui.limpar()
    gc.collect()


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Rato-Alarme")
    app.setDesktopFileName(APP_ID)
    app.setQuitOnLastWindowClosed(False)

    if "--verificar" in sys.argv:
        sprites.carregar(LADO_RATO)
        from alarma.pet import ANIMACOES, LADO, OBJETOS

        sprites.carregar(LADO, ANIMACOES)
        sprites.carregar(LADO, OBJETOS, prefixo="objeto-")
        return 0
    if "--demo" in sys.argv:
        criatura = Criatura(demo=True)
        criatura.iniciar()
        return app.exec()
    if "--pet" in sys.argv:
        pet = Pet(demo=True)
        painel = Painel(pet)
        pet.abrir_painel.connect(painel.abrir)
        pet.iniciar()
        painel.abrir()
        codigo = app.exec()
        encerrar(locals())
        return codigo

    no_boot = "--boot" in sys.argv
    instancia = Instancia()
    if not instancia.assumir(avisar=not no_boot):
        return 0

    inicio.aplicar(config.carregar(config.caminho_padrao()).iniciar_com_sistema)
    criatura = Criatura()
    pet = Pet(criatura)
    painel = Painel(pet)
    bandeja = Bandeja(painel, pet)
    instancia.pedido.connect(painel.abrir)
    pet.abrir_painel.connect(painel.abrir)
    criatura.iniciar()
    # Sempre que o computador liga (--boot), o pet dá oi; aberto à mão, ele também aparece logo.
    pet.iniciar(boot=True)
    if not no_boot:
        painel.abrir()
    codigo = app.exec()
    encerrar(locals())
    return codigo
