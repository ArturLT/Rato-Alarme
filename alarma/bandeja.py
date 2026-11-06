"""Ícone na bandeja: mostra o estado do alarme, avisa de versão nova e encerra tudo."""

import platform
import shutil
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from alarma import atualizacao, config, travessuras
from alarma.logica import decidir, pendente, resumir
from alarma.painel import Painel
from alarma.registro import DISPARADO, PEGO, Registro, caminho_mudo, caminho_padrao

RAIZ = Path(__file__).parent.parent
ICONES = Path(__file__).parent / "icones"
ATUALIZAR_MS = 5_000
PRIMEIRA_BUSCA_MS = 30_000
NOVA_BUSCA_MS = 6 * 60 * 60 * 1000


def atualiza_sozinho() -> bool:
    """No Linux instalado pelo git, o atualizar.sh faz tudo sem navegador."""
    return (
        sys.platform.startswith("linux")
        and (RAIZ / ".git").exists()
        and shutil.which("systemd-run") is not None
    )


class Bandeja(QObject):
    _achou = Signal(object)

    def __init__(self, painel: Painel, pet=None) -> None:
        super().__init__()
        self._painel = painel
        self._pet = pet
        self._lancamento: atualizacao.Lancamento | None = None
        self._calmo = QIcon(str(ICONES / "rato-alarme.png"))
        self._solto = QIcon(str(ICONES / "rato-alarme-solto.png"))

        self._menu = QMenu()
        self._estado = QAction(self._menu)
        self._estado.setEnabled(False)
        self._atualizar_app = QAction(self._menu)
        self._atualizar_app.setVisible(False)
        self._atualizar_app.triggered.connect(self._instalar)
        abrir = QAction("Painel de controle", self._menu)
        abrir.triggered.connect(painel.abrir)
        sair = QAction("Sair", self._menu)
        sair.triggered.connect(self._sair)
        self._menu.addAction(self._estado)
        self._estado_pet = QAction(self._menu)
        self._estado_pet.setEnabled(False)
        self._menu.addAction(self._estado_pet)
        self._menu.addSeparator()
        self._menu.addAction(self._atualizar_app)
        self._dormir = QAction("💤 Pôr o rato para dormir (1 hora)", self._menu)
        self._dormir.triggered.connect(self._alternar_sono)
        if pet is not None:
            chamar = QAction("Chamar o rato", self._menu)
            chamar.triggered.connect(pet.chamar)
            queijo = QAction("🧀 Dar queijo", self._menu)
            queijo.triggered.connect(pet.dar_queijo)
            self._menu.addAction(chamar)
            self._menu.addAction(queijo)
            self._menu.addAction(self._dormir)
            self._menu.addSeparator()
        else:
            self._estado_pet.setVisible(False)
        self._menu.addAction(abrir)
        self._menu.addAction(sair)

        self._icone = QSystemTrayIcon(self._calmo)
        self._icone.setContextMenu(self._menu)
        self._icone.activated.connect(self._ativado)
        self._icone.show()

        self._achou.connect(self._mostrar_lancamento)
        self._atualizar()
        self._relogio = QTimer(self, interval=ATUALIZAR_MS)
        self._relogio.timeout.connect(self._atualizar)
        self._relogio.start()
        QTimer.singleShot(PRIMEIRA_BUSCA_MS, self._buscar)
        self._busca = QTimer(self, interval=NOVA_BUSCA_MS)
        self._busca.timeout.connect(self._buscar)
        self._busca.start()

    def _ativado(self, motivo: QSystemTrayIcon.ActivationReason) -> None:
        if motivo == QSystemTrayIcon.ActivationReason.Trigger and sys.platform != "darwin":
            self._painel.abrir()

    def _atualizar(self) -> None:
        preferencias = config.carregar(config.caminho_padrao())
        decisao = decidir(
            datetime.now().astimezone(), preferencias.entrada, preferencias.saida
        )
        dia = decisao.agora.date().isoformat()
        registro = Registro(caminho_padrao())
        pego = registro.tem(dia, decisao.alarme, PEGO)
        disparado = registro.tem(dia, decisao.alarme, DISPARADO)
        solto = pendente(decisao, preferencias.alarme_ligado, pego, disparado)
        texto = resumir(decisao, preferencias.alarme_ligado, pego, solto)
        self._estado.setText(texto)
        if self._pet is not None:
            resumo = self._pet.resumo()
            self._estado_pet.setText(f"Pet: {resumo}")
            dormindo = resumo.startswith("Dormindo")
            self._dormir.setText("☀️ Acordar o rato" if dormindo else "💤 Pôr o rato para dormir (1 hora)")
            texto = f"{texto}\nPet: {resumo}"
        self._icone.setToolTip(texto)
        self._icone.setIcon(self._solto if solto else self._calmo)

    def _alternar_sono(self) -> None:
        if self._pet is None:
            return
        if self._pet.resumo().startswith("Dormindo"):
            self._pet.acordar()
        else:
            self._pet.dormir((datetime.now() + timedelta(hours=1)).isoformat(timespec="minutes"))
        self._atualizar()

    def _buscar(self) -> None:
        """Em outra thread: rede lenta não pode travar o rato."""
        threading.Thread(target=self._consultar, daemon=True).start()

    def _consultar(self) -> None:
        lancamento = atualizacao.buscar(sys.platform, platform.machine())
        if lancamento is not None:
            self._achou.emit(lancamento)

    def _mostrar_lancamento(self, lancamento: atualizacao.Lancamento) -> None:
        novidade = self._lancamento is None or self._lancamento.versao != lancamento.versao
        self._lancamento = lancamento
        self._atualizar_app.setText(f"Atualizar para a versão {lancamento.versao}")
        self._atualizar_app.setVisible(True)
        if novidade:
            self._icone.showMessage(
                "Rato-Alarme",
                f"A versão {lancamento.versao} está disponível. Atualize pelo menu da bandeja.",
            )

    def _instalar(self) -> None:
        lancamento = self._lancamento
        if lancamento is None:
            return
        if atualiza_sozinho():
            subprocess.Popen(
                ["systemd-run", "--user", "--collect", str(RAIZ / "atualizar.sh")],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            webbrowser.open(lancamento.download or lancamento.pagina)

    def _sair(self) -> None:
        """Encerra até o próximo boot. O início automático continua habilitado."""
        travessuras.restaurar_som(caminho_mudo())
        self._icone.hide()
        QApplication.exit(0)
