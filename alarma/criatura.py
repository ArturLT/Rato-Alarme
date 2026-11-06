"""O rato do alarme: sai da gaiola, foge do cursor e volta para ela quando é pego."""

import os
import random
import time
from datetime import datetime

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtGui import QCloseEvent, QMouseEvent
from PySide6.QtWidgets import QLabel, QPlainTextEdit

from alarma import balao_alarme, config, falas, janela, sistema, sprites, travessuras
from alarma.animacao import CORRENDO, CORRIDA, DUR_ACERTO, FALANDO, depois_de_pego, escolher
from alarma.caca import FECHAR, JANELAS, LADO_RATO, MUDO, NOTAS, YOUTUBE, Caca
from alarma.logica import Alarme, Decisao, decidir, pendente
from alarma.registro import DISPARADO, PEGO, Registro, caminho_mudo, caminho_padrao
from alarma.som import tocar

APP_ID = "meme.alarma"
TITULO = "alarma"
TITULO_NOTAS = "bloco do rato"
REAVALIAR_MS = 2_000
PASSO_MS = 100
LETRA_MS = 70
QUADRO_MS = 50
BIP_MS = 4_000
BIP_INICIAL_MS = 700
AREA_RESERVA = (0, 0, 1920, 1080)


class Mascote(QLabel):
    """A janela sem moldura, transparente e sempre por cima, que é o próprio rato."""

    clicado = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(TITULO)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)
        self.setFixedSize(LADO_RATO, LADO_RATO)

    def mousePressEvent(self, _evento: QMouseEvent) -> None:
        self.clicado.emit()

    def closeEvent(self, evento: QCloseEvent) -> None:
        """Só o Hyprland deixa fechar o rato pelo atalho. Em outro sistema, o pedido
        vem do desligamento, e recusar impediria o computador de desligar."""
        if sistema.tem_hyprland():
            evento.ignore()


class Notas(QPlainTextEdit):
    fechada = Signal()

    def __init__(self, texto: str) -> None:
        super().__init__()
        self.setWindowTitle(TITULO_NOTAS)
        self.setReadOnly(True)
        self.resize(420, 300)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self._letras = iter(texto)
        self._relogio = QTimer(self, interval=LETRA_MS)
        self._relogio.timeout.connect(self._escrever)
        self._relogio.start()

    def _escrever(self) -> None:
        letra = next(self._letras, None)
        if letra is None:
            self._relogio.stop()
            return
        self.moveCursor(self.textCursor().MoveOperation.End)
        self.insertPlainText(letra)

    def closeEvent(self, evento: QCloseEvent) -> None:
        self._relogio.stop()
        self.fechada.emit()
        super().closeEvent(evento)


class Criatura(QObject):
    def __init__(self, demo: bool = False) -> None:
        super().__init__()
        self._demo = demo
        self._registro = Registro(None if demo else caminho_padrao())
        self._acaso = random.Random()
        self._config = self._ler_config()
        self.decisao = self._decidir()
        self._caca: Caca | None = None
        self._janela: Mascote | None = None
        self._tela: janela.JanelaQt | janela.JanelaHyprland | None = None
        self._balao: balao_alarme.Balao | None = None
        self._tela_balao: janela.JanelaQt | janela.JanelaHyprland | None = None
        self._ultima_fala = ""
        self._animacoes: dict[str, sprites.Animacao] = {}
        self._nome_atual = ""
        self._inicio_clipe = 0.0
        self._acerto_ate = 0.0
        self._capturado_em: float | None = None
        self._oculto = True
        self._area = AREA_RESERVA
        self._notas: Notas | None = None
        self._marca_mudo = caminho_mudo()
        self._relogios: list[QTimer] = []

    def _ler_config(self) -> config.Config:
        return config.Config() if self._demo else config.carregar(config.caminho_padrao())

    def _decidir(self) -> Decisao:
        agora = datetime.now().astimezone()
        if self._demo:
            return Decisao(Alarme.MANHA, True, agora)
        return decidir(agora, self._config.entrada, self._config.saida)

    @property
    def ativa(self) -> bool:
        """O rato do alarme está na tela. O pet sai de cena enquanto isso."""
        return self._caca is not None or not self._oculto

    @property
    def _dia(self) -> str:
        return self.decisao.agora.date().isoformat()

    def iniciar(self) -> None:
        travessuras.restaurar_som(self._marca_mudo)

        self._janela = Mascote()
        self._janela.clicado.connect(self._clicado)
        self._tela = janela.nova(self._janela)
        self._balao = balao_alarme.Balao()
        self._tela_balao = janela.nova(self._balao)
        self._animacoes = sprites.carregar(LADO_RATO)
        self._sincronizar()
        self._quadro()

        QTimer.singleShot(BIP_INICIAL_MS, self._bip)
        for intervalo, acao in (
            (QUADRO_MS, self._quadro),
            (PASSO_MS, self._passo),
            (BIP_MS, self._bip),
            (REAVALIAR_MS, self._sincronizar),
        ):
            relogio = QTimer(self, interval=intervalo)
            relogio.timeout.connect(acao)
            relogio.start()
            self._relogios.append(relogio)

    def desligar(self) -> None:
        """Chamado na saída do app: solta as imagens antes do Qt fechar."""
        for relogio in self._relogios:
            relogio.stop()
        travessuras.restaurar_som(self._marca_mudo)
        self._animacoes = {}

    def _sincronizar(self) -> None:
        antes = self._config
        self._config = self._ler_config()
        self.decisao = self._decidir()
        self._reabrir(antes)
        alarme = self.decisao.alarme
        pego = self._registro.tem(self._dia, alarme, PEGO)
        disparado = self._registro.tem(self._dia, alarme, DISPARADO)
        solto = pendente(self.decisao, self._config.alarme_ligado, pego, disparado)
        if solto and not disparado:
            self._registro.marcar(self._dia, alarme, DISPARADO)
        if solto and self._caca is None:
            feito = self._registro.tem(self._dia, alarme, YOUTUBE)
            self._caca = Caca(self._acaso, time.monotonic(), youtube_feito=feito)
            self._mostrar()
        elif not solto:
            self._encerrar()
        if not self._config.alarme_ligado:
            self._capturado_em = None
        if not solto and not self._oculto and self._capturado_em is None:
            self._esconder()

    def _reabrir(self, antes: config.Config) -> None:
        """Horário mudado para mais tarde hoje vale de novo, mesmo com o rato já pego."""
        hora = self.decisao.agora.time()
        for alarme, velho, novo in (
            (Alarme.MANHA, antes.entrada, self._config.entrada),
            (Alarme.TARDE, antes.saida, self._config.saida),
        ):
            if novo != velho and hora < novo:
                self._registro.limpar(self._dia, alarme)

    def _encerrar(self) -> None:
        self._caca = None
        if self._balao is not None:
            self._balao.calar()
        travessuras.restaurar_som(self._marca_mudo)
        if self._notas is not None:
            self._notas.close()

    def _mostrar(self) -> None:
        self._capturado_em = None
        if self._oculto and self._janela is not None:
            self._oculto = False
            self._tela.esquecer()
            self._janela.show()
            self._tela_balao.esquecer()
            self._balao.show()

    def _esconder(self) -> None:
        """Some da tela até o próximo alarme. O processo continua vivo."""
        self._oculto = True
        if self._janela is not None:
            self._tela.esquecer()
            self._janela.hide()
            self._tela_balao.esquecer()
            self._balao.hide()

    def _quadro(self) -> None:
        if self._janela is None or self._oculto:
            return
        agora = time.monotonic()
        caca = self._caca
        depois = None
        if self._capturado_em is not None:
            depois = depois_de_pego(agora - self._capturado_em)
            if depois is None:
                self._capturado_em = None
                self._esconder()
                return
        nome = escolher(
            caca.fase if caca else None,
            caca.cansado(agora) if caca else False,
            agora < self._acerto_ate,
            depois,
            bool(caca and caca.falando(agora)),
        )
        virado = bool(caca and caca.esquerda)
        if nome == CORRENDO and caca:
            nome, virado = CORRIDA[caca.direcao]
        if nome != self._nome_atual:
            self._nome_atual = nome
            self._inicio_clipe = agora
        animacao = self._animacoes[nome]
        quadros = animacao.esquerda if virado else animacao.direita
        indice = animacao.clipe.indice(agora - self._inicio_clipe)
        if nome == FALANDO and not self._balao.digitando:
            indice = 0  # acabou de escrever: boca fechada enquanto a pessoa lê
        self._janela.setPixmap(quadros[indice])

    def _clicado(self) -> None:
        agora = time.monotonic()
        if self._caca is None:
            return
        pego = self._caca.clique(agora)
        self._balao.calar()
        if not pego:
            self._acerto_ate = agora + DUR_ACERTO
            self._nome_atual = ""
            return
        self._capturado_em = agora
        self._registro.marcar(self._dia, self.decisao.alarme, PEGO)
        self._encerrar()

    def _bip(self) -> None:
        if self._caca is not None:
            tocar(self.decisao.alarme)

    def _proibidas(self) -> tuple[str, ...]:
        if not sistema.mexe_em_outras_janelas():
            return (FECHAR, JANELAS)
        return () if self._config.fechar_janela else (FECHAR,)

    def _passo(self) -> None:
        if self._oculto or not self._tela.pronta() or self._caca is None:
            return

        agora = time.monotonic()
        cursor = self._tela.cursor()
        self._area = self._tela.area(cursor) or self._area
        posicao = self._caca.passo(agora, cursor, self._area)
        if posicao is not None:
            self._tela.mover(*posicao)
        self._falar(agora)

        travessura = self._caca.travessura(agora, self._proibidas())
        if travessura == NOTAS:
            self._abrir_notas()
        elif travessura == YOUTUBE:
            self._registro.marcar(self._dia, self.decisao.alarme, YOUTUBE)
            travessuras.abrir_youtube()
        elif travessura == JANELAS:
            travessuras.mexer_janelas(os.getpid(), self._acaso)
        elif travessura == FECHAR:
            travessuras.fechar_janela(os.getpid(), self._acaso)
        elif travessura == MUDO:
            travessuras.mutar(self._marca_mudo)

    def _falar(self, agora: float) -> None:
        caca = self._caca
        pronto = self._tela_balao.pronta()
        if self._balao.aberto and not caca.falando(agora):
            self._balao.calar()
        if not pronto or caca.x is None or not caca.quer_falar(agora):
            return
        manha = self.decisao.alarme == Alarme.MANHA
        horario = self._config.entrada if manha else self._config.saida
        atraso = falas.minutos_de_atraso(self.decisao.agora, horario)
        texto = falas.sortear(self._acaso, self.decisao.alarme, atraso, self._ultima_fala)
        self._ultima_fala = texto
        caca.falar(agora, balao_alarme.duracao_s(texto))
        onde = balao_alarme.lugar(round(caca.x), round(caca.y), caca.esquerda, self._area)
        self._tela_balao.mover(onde.x, onde.y)
        self._balao.dizer(texto, onde)

    def _abrir_notas(self) -> None:
        if self._notas is not None:
            return
        self._notas = Notas(travessuras.TEXTO_NOTAS)
        self._notas.fechada.connect(self._notas_fechadas)
        self._notas.show()

    def _notas_fechadas(self) -> None:
        self._notas = None
