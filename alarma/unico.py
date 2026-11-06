"""Garante um rato só. Abrir o programa de novo pede o painel ao que já está rodando.

Usa arquivos, como o resto do programa: a trava some sozinha se o processo morrer,
e a marca funciona igual nos três sistemas.
"""

from pathlib import Path

from PySide6.QtCore import QLockFile, QObject, QTimer, Signal

from alarma.caminhos import pasta_estado

OLHAR_MS = 300


class Instancia(QObject):
    pedido = Signal()

    def __init__(self, pasta: Path | None = None) -> None:
        super().__init__()
        pasta = pasta or pasta_estado()
        pasta.mkdir(parents=True, exist_ok=True)
        self._trava = QLockFile(str(pasta / "rodando.lock"))
        self._trava.setStaleLockTime(0)  # só vale como abandonada se o processo morreu
        self._marca = pasta / "abrir-painel"
        self._relogio = QTimer(self, interval=OLHAR_MS)
        self._relogio.timeout.connect(self._olhar)

    def assumir(self, avisar: bool) -> bool:
        """True se esta é a primeira. Senão, avisa a primeira quando `avisar`."""
        if not self._trava.tryLock(0):
            if avisar:
                try:
                    self._marca.touch()
                except OSError:
                    pass
            return False
        self._apagar_marca()
        self._relogio.start()
        return True

    def _apagar_marca(self) -> bool:
        try:
            self._marca.unlink()
        except OSError:
            return False
        return True

    def _olhar(self) -> None:
        if self._apagar_marca():
            self.pedido.emit()
