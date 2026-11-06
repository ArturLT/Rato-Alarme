"""Garante um rato só. Abrir o programa de novo pede o painel ao que já está rodando."""

import getpass

from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

ESPERA_MS = 500


def nome_padrao() -> str:
    return f"alarma-meme-{getpass.getuser()}"


class Instancia(QObject):
    pedido = Signal()

    def __init__(self, nome: str | None = None) -> None:
        super().__init__()
        self._nome = nome or nome_padrao()
        self._servidor: QLocalServer | None = None

    def assumir(self, avisar: bool) -> bool:
        """True se esta é a primeira. Senão, avisa a primeira quando `avisar`."""
        outra = QLocalSocket()
        outra.connectToServer(self._nome)
        if outra.waitForConnected(ESPERA_MS):
            if avisar:
                outra.write(b"painel\n")
                outra.waitForBytesWritten(ESPERA_MS)
            outra.disconnectFromServer()
            return False
        QLocalServer.removeServer(self._nome)
        self._servidor = QLocalServer(self)
        self._servidor.newConnection.connect(self._nova_conexao)
        self._servidor.listen(self._nome)
        return True

    def _nova_conexao(self) -> None:
        conexao = self._servidor.nextPendingConnection()
        conexao.readyRead.connect(lambda: self._mensagem(conexao))
        conexao.disconnected.connect(conexao.deleteLater)

    def _mensagem(self, conexao: QLocalSocket) -> None:
        if bytes(conexao.readAll()):
            self.pedido.emit()
