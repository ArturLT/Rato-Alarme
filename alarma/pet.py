"""O rato de estimação: aparece do nada, senta, fala, segura placas, carrega coisas,
apronta e aprende com carinho, queijo e tapa.

O pet roda uma fila de passos (surgir, andar, falar, arrastar o cursor...). Cada
interação do repertório vira alguns passos. Enquanto o rato do alarme está na
tela, o pet sai de cena.
"""

import os
import random
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from PySide6.QtCore import QObject, QPoint, Qt, QTimer, Signal
from PySide6.QtGui import QAction, QCloseEvent, QCursor, QMouseEvent
from PySide6.QtWidgets import QApplication, QLabel, QMenu
from shiboken6 import Shiboken

from alarma import acoes, config, janela, sistema, sprites, travessuras
from alarma import comportamento as comp
from alarma import repertorio as rep
from alarma.cerebro import Cerebro, caminho_padrao as caminho_cerebro
from alarma.informacoes import Informante
from alarma.registro import caminho_mudo

LADO = 196
ESCALA = LADO / 48
QUADRO_MS = 40
DECIDIR_MS = 1_000
RELER_MS = 3_000
BUSCAR_MS = 20 * 60 * 1000
VEL_ANDAR = 110.0
VEL_CORRER = 420.0
VEL_ARRASTAR = 140.0
MAX_OBJETOS = 8
ESPERA_BOOT_MS = 4_000
VIDEO_A_CADA_S = 3600.0
MUDO_DURA_S = 25.0

ITENS = ("queijo", "meia", "bilhete", "moeda", "flor")
ANIMACOES = (
    "sentado", "falando", "placa", "acenando", "comendo", "feliz", "cochilando", "andando", "puxando", "surgindo",
    "acerto", "correndo", "correndo-cima", "correndo-baixo", "correndo-cima-lado", "correndo-baixo-lado",
    *(f"andando-{i}" for i in ITENS),
)
OBJETOS = (*ITENS, "migalhas", "pegadas")
# Pontos no quadro de 48 px, rato virado para a direita: origem (24, 44).
BOCA = (39, 37)
CABECA = (29, 13)
CABO = (41, 1)
TITULOS = {
    rep.CLIMA: "Previsão do rato",
    rep.NOTICIAS: "Notícia fresquinha",
    rep.MUNDO: "O rato informa",
    rep.COMPUTADOR: "Seu computador",
    rep.CURIOSIDADES: "Você sabia?",
    rep.PERGUNTAS: "Pergunta do rato",
    rep.BRINCADEIRA: "Recado do rato",
}
DIARIO = [
    "querido diário,\n\nhoje eu fiquei de olho no humano.\nele digita rápido. eu queria digitar também.\n\nassinado: o rato\n",
    "lista de compras:\n- queijo\n- queijo\n- mais queijo\n- um pedaço de queijo\n- (queijo)\n",
    "plano secreto:\n1. aparecer do nada\n2. fazer carinho no humano com o bigode\n3. ganhar queijo\n4. dominar o mundo\n\nnão conta pra ninguém.\n",
    "poema do rato:\n\nroeu, roeu,\no rato roeu\na roupa do rei\ne o queijo era meu.\n",
]


@dataclass
class Passo:
    tipo: str
    dur: float = 0.0
    anim: str = "sentado"
    destino: tuple[float, float] | None = None
    vel: float = VEL_ANDAR
    acao: object = None
    texto: str = ""
    titulo: str = ""
    interacao: rep.Interacao | None = None
    extra: dict = field(default_factory=dict)


class MascotePet(QLabel):
    tapa = Signal()
    menu = Signal(QPoint)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("alarma-pet")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_MacAlwaysShowToolWindow)
        self.setFixedSize(LADO, LADO)
        self.setToolTip("Clique para dar um tapa. Botão direito: queijo, carinho e mais.")

    def mousePressEvent(self, evento: QMouseEvent) -> None:
        if evento.button() == Qt.MouseButton.RightButton:
            self.menu.emit(evento.globalPosition().toPoint())
        elif evento.button() == Qt.MouseButton.LeftButton:
            self.tapa.emit()

    def contextMenuEvent(self, evento) -> None:
        evento.accept()

    def closeEvent(self, evento: QCloseEvent) -> None:
        if sistema.tem_hyprland():
            evento.ignore()


class Pet(QObject):
    mudou = Signal()
    _resultado = Signal(str, bool)
    abrir_painel = Signal()

    AUSENTE = "ausente"
    ATIVO = "ativo"
    DORMINDO = "dormindo"

    def __init__(self, criatura=None, demo: bool = False, acaso: random.Random | None = None) -> None:
        super().__init__()
        self._demo = demo
        self._criatura = criatura
        self._acaso = acaso or random.Random()
        self.cerebro = Cerebro(None if demo else caminho_cerebro())
        self.informante = Informante(self._acaso)
        self.cfg = self._ler_config()
        self.estado = self.AUSENTE
        self.motivo = ""
        self._fila: deque[Passo] = deque()
        self._passo: Passo | None = None
        self._inicio_passo = 0.0
        self._ultimo = time.monotonic()
        self._proxima_visita = time.monotonic() + comp.espera_ate_aparecer(self.cfg.intensidade, self._acaso)
        self._fim_visita = 0.0
        self._janela: MascotePet | None = None
        self._tela = None
        self._anims: dict[str, sprites.Animacao] = {}
        self._objetos_anim: dict[str, sprites.Animacao] = {}
        self._anim = "sentado"
        self._anim_desde = 0.0
        self._esquerda = False
        self.x, self.y = 400.0, 400.0
        self._area = (0, 0, 1920, 1080)
        self._balao = None
        self._placa = None
        self._objetos: list = []
        self._notas = None
        self._tapas = comp.Tapas()
        self._carinho = comp.Carinho()
        self._ultimo_carinho = 0.0
        self._ultimo_video = -VIDEO_A_CADA_S
        self._mudo_ate = 0.0
        self._marca_mudo = caminho_mudo()
        self._atual: rep.Interacao | None = None
        self._repertorio = rep.todas()
        self._relogios: list[QTimer] = []
        self._resultado.connect(self._depois_da_acao)

    # ---- ciclo de vida ----

    def _ler_config(self) -> config.Config:
        if self._demo:
            return config.Config(intensidade=100, travessura=60)
        return config.carregar(config.caminho_padrao())

    def iniciar(self, boot: bool = False) -> None:
        self._janela = MascotePet()
        self._janela.tapa.connect(self.tapa)
        self._janela.menu.connect(self._menu)
        self._tela = janela.nova(self._janela)
        self._anims = sprites.carregar(LADO, ANIMACOES)
        self._objetos_anim = sprites.carregar(LADO, OBJETOS, prefixo="objeto-")
        self.cerebro.ligacoes += 1 if boot else 0
        self.cerebro.salvar()
        self.informante.buscar(self.cfg.cidade, self.cfg.internet)
        for intervalo, acao in (
            (QUADRO_MS, self._quadro),
            (DECIDIR_MS, self._decidir),
            (RELER_MS, self._reler),
            (BUSCAR_MS, lambda: self.informante.buscar(self.cfg.cidade, self.cfg.internet)),
        ):
            relogio = QTimer(self, interval=intervalo)
            relogio.timeout.connect(acao)
            relogio.start()
            self._relogios.append(relogio)
        if self._demo or (boot and self.cfg.saudacao_boot and self.cfg.pet_ligado):
            QTimer.singleShot(ESPERA_BOOT_MS if boot else 800, self.saudar)
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.desligar)

    def desligar(self) -> None:
        """Fecha as janelas do pet antes do Qt fechar: janela destruída depois do Qt derruba o programa."""
        for relogio in self._relogios:
            relogio.stop()
        self._relogios.clear()
        self._desmutar()
        self.cerebro.salvar()
        self._fechar_falas()
        janelas = [*self._objetos, self._notas, self._janela]
        self._objetos.clear()
        self._notas = self._janela = None
        self._anims, self._objetos_anim = {}, {}  # QPixmap solto depois do Qt também derruba
        self.estado = self.AUSENTE
        for widget in janelas:
            if widget is not None and Shiboken.isValid(widget):
                widget.hide()
                Shiboken.delete(widget)

    def _reler(self) -> None:
        antes = self.cfg
        self.cfg = self._ler_config()
        if antes.intensidade != self.cfg.intensidade and self.estado == self.AUSENTE:
            self._agendar()
        if not self.cfg.pet_ligado and self.estado != self.AUSENTE:
            self._sumir_ja()
        self.mudou.emit()

    def _alarme_na_tela(self) -> bool:
        return bool(self._criatura is not None and self._criatura.ativa)

    def _agendar(self, espera: float | None = None) -> None:
        if espera is None:
            espera = comp.espera_ate_aparecer(self.cfg.intensidade, self._acaso)
        self._proxima_visita = time.monotonic() + espera
        self.mudou.emit()

    def segundos_ate_voltar(self) -> float:
        return max(0.0, self._proxima_visita - time.monotonic())

    def _decidir(self) -> None:
        agora = time.monotonic()
        if self._alarme_na_tela():
            if self.estado != self.AUSENTE:
                self._sumir_ja()
            return
        if self._mudo_ate and agora > self._mudo_ate:
            self._desmutar()
        dormindo = self.cfg.dormindo(datetime.now())
        if dormindo and self.estado == self.ATIVO and (self._passo is None or self._passo.tipo != "dormir"):
            self._ir_dormir()
        elif not dormindo and self.estado == self.DORMINDO:
            self._acordar()
        elif self.estado == self.AUSENTE and not dormindo and self.cfg.pet_ligado and agora >= self._proxima_visita:
            self.aparecer()

    # ---- visitas ----

    def _local_aleatorio(self) -> tuple[float, float]:
        x0, y0, x1, y1 = self._area
        x = self._acaso.uniform(x0 + 40, max(x0 + 41, x1 - LADO - 40))
        # quase sempre perto do chão da tela, às vezes em qualquer lugar
        if self._acaso.random() < 0.6:
            y = y1 - LADO - self._acaso.uniform(0, 40)
        else:
            y = self._acaso.uniform(y0 + 180, max(y0 + 181, y1 - LADO))
        return x, y

    def _atualizar_area(self) -> None:
        if self._tela is None:
            return
        cursor = self._tela.cursor()
        self._area = self._tela.area(cursor) or self._area

    def _mostrar(self) -> None:
        if self._janela is not None and not self._janela.isVisible():
            self._tela.esquecer()
            self._janela.show()
            self._mover()

    def aparecer(self, saudacao: str = "") -> None:
        """Surge do nada num canto qualquer e começa uma visita."""
        if self._janela is None or self._alarme_na_tela():
            return
        self._atualizar_area()
        self._limpar()
        self.estado = self.ATIVO
        self._fim_visita = time.monotonic() + comp.duracao_visita(self.cfg.intensidade, self._acaso)
        self.x, self.y = self._local_aleatorio()
        self._esquerda = self._acaso.random() < 0.5
        self._mostrar()
        self._enfileirar(Passo("anim", 1.0, "surgindo"))
        if saudacao:
            self._enfileirar(Passo("falar", anim="acenando", texto=saudacao))
        elif self._acaso.random() < 0.35:
            self._falar_reacao("voltou", anim="acenando", curto=True)
        else:
            self._enfileirar(Passo("anim", 1.0, "sentado"))
        self._enfileirar(Passo("chamar", acao=self._proxima))
        self.mudou.emit()

    def chamar(self) -> None:
        """Pelo painel ou pela bandeja: aparece agora, mesmo dormindo."""
        if self.estado == self.DORMINDO:
            self._acordar(mandar=True)
        elif self.estado == self.AUSENTE:
            self.aparecer()

    def saudar(self) -> None:
        """Saudação de quando o computador liga: oi, e alguma coisa trazida ou dita."""
        if self._alarme_na_tela():
            QTimer.singleShot(10_000, self.saudar)
            return
        texto = comp.texto_saudacao(datetime.now(), self.cerebro, self._acaso)
        self.aparecer(saudacao=texto)
        self._fila.pop()  # tira o "próxima" para pôr o presente antes
        self._enfileirar(Passo("chamar", acao=self._presente_do_boot))
        if self.cfg.dormindo(datetime.now()):
            self._enfileirar(Passo("falar", anim="falando", texto="Bom, era só isso. Vou voltar a dormir."))
            self._enfileirar(Passo("chamar", acao=self._ir_dormir))
        else:
            self._enfileirar(Passo("chamar", acao=self._proxima))

    def _presente_do_boot(self) -> None:
        for fonte in ("clima_agora", "clima_hoje", "proximo_feriado", "noticia_brasil", "hora"):
            if (fonte != "hora" and not self.cfg.internet) or not self.informante.tem(fonte):
                continue
            texto = self.informante.frase(fonte)
            if texto:
                categoria = rep.CLIMA if fonte.startswith("clima") else rep.COMPUTADOR if fonte == "hora" else rep.MUNDO
                self._enfileirar_frente(Passo("placa", texto=texto, titulo=TITULOS[categoria]))
                return
        if self.cfg.permite(rep.P_OBJETOS):
            item = self._acaso.choice(ITENS)
            self._enfileirar_frente(*self._passos_trazer(item, "Trouxe um presente pra começar o dia!"))

    def _proxima(self) -> None:
        if self.estado != self.ATIVO:
            return
        if time.monotonic() >= self._fim_visita:
            self._sair()
            return
        opcoes = comp.elegiveis(
            self._repertorio + comp.extras(self.cerebro, self.cfg), self.cfg, self.cerebro, self.informante.tem, self._possivel
        )
        plano = comp.planejar(opcoes, self.cfg, self.cerebro, self._acaso)
        if plano.desistiu is not None and self._acaso.random() < 0.5:
            self._falar_reacao("desistiu", curto=True)
        if plano.interacao is not None:
            if plano.teimosa:
                self._falar_reacao("teimoso", curto=True)
            self._executar(plano.interacao)
        pausa = comp.pausa_entre_interacoes(self.cfg.intensidade, self._acaso)
        self._enfileirar(Passo("anim", pausa, "sentado"))
        self._enfileirar(Passo("chamar", acao=self._proxima))

    def _sair(self) -> None:
        x0, _, x1, _ = self._area
        esquerda = self.x + LADO / 2 < (x0 + x1) / 2
        destino = (x0 - LADO * 0.8 if esquerda else x1 - LADO * 0.2, self.y)
        self._enfileirar(Passo("andar", destino=destino, anim="andando", vel=VEL_ANDAR * 1.4))
        self._enfileirar(Passo("chamar", acao=self._sumir_ja))

    def _sumir_ja(self, espera: float | None = None) -> None:
        self._limpar()
        self._desmutar()
        self.estado = self.AUSENTE
        if self._janela is not None:
            self._tela.esquecer()
            self._janela.hide()
        self.cerebro.salvar()
        self._agendar(espera)

    def _limpar(self) -> None:
        self._fila.clear()
        self._passo = None
        self._atual = None
        self._fechar_falas()

    def _fechar_falas(self) -> None:
        for widget in (self._balao, self._placa):
            if widget is not None and Shiboken.isValid(widget):
                widget.hide()
                Shiboken.delete(widget)
        self._balao = self._placa = None

    # ---- sono ----

    def dormir(self, ate: str) -> None:
        """ate: config.SEMPRE ou data ISO. Grava no config, que é o que o painel mostra."""
        self.cfg = self.cfg.com(dormir_ate=ate)
        self._gravar_config()
        if self.estado == self.ATIVO:
            self._ir_dormir()
        elif self.estado == self.AUSENTE and self.cfg.dormir_visivel:
            self.estado = self.DORMINDO
            self._atualizar_area()
            self._deitar_no_canto()
        self.mudou.emit()

    def acordar(self) -> None:
        self.cfg = self.cfg.com(dormir_ate="")
        self._gravar_config()
        if self.estado == self.DORMINDO:
            self._acordar(mandar=True)
        self.mudou.emit()

    def _gravar_config(self) -> None:
        if self._demo:
            return
        try:
            config.salvar(config.caminho_padrao(), self.cfg)
        except (OSError, ValueError):
            pass

    def _canto(self) -> tuple[float, float]:
        _, _, x1, y1 = self._area
        return x1 - LADO - 20, y1 - LADO + 30

    def _ir_dormir(self) -> None:
        self._limpar()
        self.estado = self.DORMINDO
        self._falar_reacao("dormir", curto=True)
        if self.cfg.dormir_visivel:
            self._enfileirar(Passo("andar", destino=self._canto(), anim="andando"))
            self._enfileirar(Passo("dormir", 1e9, "cochilando"))
        else:
            self._enfileirar(Passo("andar", destino=(self._area[2] + 10, self.y), anim="andando", vel=VEL_ANDAR * 1.5))
            self._enfileirar(Passo("chamar", acao=self._esconder_dormindo))

    def _deitar_no_canto(self) -> None:
        self.x, self.y = self._canto()
        self._esquerda = True
        self._mostrar()
        self._enfileirar(Passo("dormir", 1e9, "cochilando"))

    def _esconder_dormindo(self) -> None:
        self._fila.clear()
        self._passo = None
        if self._janela is not None:
            self._tela.esquecer()
            self._janela.hide()

    def _acordar(self, mandar: bool = False) -> None:
        self._limpar()
        if self._janela is not None and self._janela.isVisible():
            self.estado = self.ATIVO
            self._fim_visita = time.monotonic() + comp.duracao_visita(self.cfg.intensidade, self._acaso)
            self._falar_reacao("acordou", anim="acenando")
            self._enfileirar(Passo("chamar", acao=self._proxima))
        else:
            self.estado = self.AUSENTE
            if mandar:
                self.aparecer(saudacao=rep.preencher(self._acaso.choice(rep.REACOES["acordou"]), self.cerebro.fatos) or "")
            else:
                self._agendar(self._acaso.uniform(20, 90))
        self.mudou.emit()

    # ---- o que ele pode fazer ----

    def _possivel(self, permissao: str | None) -> bool:
        if permissao == rep.P_FECHAR_ABA:
            return acoes.pode_fechar_aba()
        if permissao == rep.P_MINIMIZAR:
            return acoes.pode_minimizar()
        if permissao == rep.P_CURSOR:
            return acoes.pode_mover_cursor()
        if permissao == rep.P_JANELAS:
            return sistema.mexe_em_outras_janelas()
        if permissao == rep.P_SITES:
            return time.monotonic() - self._ultimo_video >= VIDEO_A_CADA_S
        if permissao == rep.P_OBJETOS:
            return len(self._objetos) < MAX_OBJETOS
        return True

    def _executar(self, i: rep.Interacao) -> None:
        self._atual = i
        self.cerebro.lembrar(i.id, time.time())
        if i.tipo in (rep.FALA, rep.PERGUNTA):
            texto = rep.preencher(i.textos[0], self.cerebro.fatos) or i.textos[0]
            if i.id.startswith("ensinada:") and self._acaso.random() < 0.5:
                modelo = self._acaso.choice(rep.REACOES["ensinada"])
                texto = modelo.replace("{frase}", texto)
            if i.tipo == rep.PERGUNTA:
                self._enfileirar(Passo("falar", anim="falando", texto=texto, interacao=i, extra={"pergunta": i.fato}))
            elif i.animacao == "placa":
                self._enfileirar(Passo("placa", texto=texto, titulo=TITULOS.get(i.categoria, ""), interacao=i))
            else:
                self._enfileirar(Passo("falar", anim="falando", texto=texto, interacao=i))
        elif i.tipo == rep.INFO:
            texto = self.informante.frase(i.fonte)
            if not texto:
                return
            if i.animacao == "placa":
                self._enfileirar(Passo("placa", texto=texto, titulo=TITULOS.get(i.categoria, ""), interacao=i))
            else:
                self._enfileirar(Passo("falar", anim="falando", texto=texto, interacao=i))
        elif i.tipo == rep.BRINCADEIRA:
            self._brincar(i)
        elif i.tipo == rep.TRAVESSURA:
            self._aprontar(i)

    def _brincar(self, i: rep.Interacao) -> None:
        fala = i.textos[0] if i.textos else ""
        x0, y0, x1, y1 = self._area
        if i.id == "passear":
            self._enfileirar(Passo("andar", destino=self._local_aleatorio(), anim="andando"))
        elif i.id == "correr":
            if fala:
                self._enfileirar(Passo("falar", anim="feliz", texto=fala, dur=1.5))
            for _ in range(3):
                self._enfileirar(Passo("andar", destino=self._local_aleatorio(), anim="correndo", vel=VEL_CORRER))
        elif i.id == "seguir-cursor":
            self._enfileirar(Passo("falar", anim="falando", texto=fala, dur=2.0))
            self._enfileirar(Passo("seguir", 6.0, "andando"))
            self._enfileirar(Passo("anim", 2.0, "sentado"))
        elif i.id == "esconder":
            self._enfileirar(Passo("falar", anim="falando", texto=fala, dur=1.8))
            self._enfileirar(Passo("andar", destino=(x1 - LADO * 0.25, self.y), anim="correndo", vel=VEL_CORRER))
            self._enfileirar(Passo("anim", 4.0, "sentado", extra={"escondido": True}))
            self._enfileirar(Passo("chamar", acao=lambda: setattr(self, "x", self._local_aleatorio()[0])))
            self._enfileirar(Passo("anim", 1.0, "surgindo"))
            self._falar_reacao("voltou", anim="feliz", curto=True)
        elif i.id in ("pedir-carinho", "pedir-queijo"):
            self._enfileirar(Passo("placa", texto=fala, titulo=TITULOS[rep.BRINCADEIRA], interacao=i))
        elif i.id == "sentar-olhar":
            self._enfileirar(Passo("anim", self._acaso.uniform(4, 8), "sentado"))
        else:
            anim = {"cochilar": "cochilando", "comer": "comendo", "dancar": "feliz", "acenar": "acenando"}.get(i.id, "sentado")
            if fala:
                self._enfileirar(Passo("falar", anim=anim, texto=fala, dur=2.5, interacao=i))
            self._enfileirar(Passo("anim", 5.0 if anim == "cochilando" else 2.5, anim))

    def _aprontar(self, i: rep.Interacao) -> None:
        fala = i.textos[0] if i.textos else ""
        if i.id.startswith("trazer-"):
            self._enfileirar(*self._passos_trazer(i.id.split("-", 1)[1], fala, i))
        elif i.id == "migalhas":
            self._enfileirar(Passo("anim", 2.5, "comendo"))
            self._enfileirar(Passo("chamar", acao=lambda: self._largar("migalhas")))
            self._enfileirar(Passo("falar", anim="falando", texto=fala, interacao=i))
        elif i.id == "pegadas":
            for _ in range(3):
                destino = (self.x + self._acaso.uniform(-260, 260), self.y + self._acaso.uniform(-90, 90))
                self._enfileirar(Passo("andar", destino=self._dentro(destino), anim="andando"))
                self._enfileirar(Passo("chamar", acao=lambda: self._largar("pegadas")))
            self._enfileirar(Passo("falar", anim="falando", texto=fala, interacao=i))
        elif i.id == "arrastar-cursor":
            self._enfileirar(Passo("ir-ao-cursor", 6.0, "correndo", vel=VEL_CORRER))
            self._enfileirar(Passo("falar", anim="puxando", texto=fala, dur=1.2, interacao=i))
            self._enfileirar(Passo("arrastar", 3.0, "puxando"))
        elif i.id == "tremer-cursor":
            self._enfileirar(Passo("falar", anim="feliz", texto=fala, dur=1.5, interacao=i))
            self._enfileirar(Passo("tremer", 1.6, "feliz"))
        elif i.id in ("fechar-aba", "minimizar"):
            self._enfileirar(Passo("anim", 1.2, "feliz"))
            self._enfileirar(Passo("chamar", acao=lambda: self._em_segundo_plano(i)))
        elif i.id == "mutar":
            self._enfileirar(Passo("chamar", acao=self._mutar))
            self._enfileirar(Passo("falar", anim="falando", texto=fala, interacao=i))
        elif i.id == "video-queijo":
            self._ultimo_video = time.monotonic()
            self._enfileirar(Passo("falar", anim="feliz", texto=fala, dur=2.0, interacao=i))
            self._enfileirar(Passo("chamar", acao=travessuras.abrir_youtube))
        elif i.id == "notas":
            self._enfileirar(Passo("falar", anim="falando", texto=fala, dur=2.0, interacao=i))
            self._enfileirar(Passo("chamar", acao=self._abrir_notas))
        elif i.id == "mexer-janelas":
            self._enfileirar(Passo("chamar", acao=lambda: travessuras.mexer_janelas(os.getpid(), self._acaso)))
            self._enfileirar(Passo("falar", anim="feliz", texto=fala, interacao=i))
        elif i.id == "fechar-janela" and self.cfg.fechar_janela:
            self._enfileirar(Passo("chamar", acao=lambda: travessuras.fechar_janela(os.getpid(), self._acaso)))
            self._enfileirar(Passo("falar", anim="feliz", texto=fala, interacao=i))

    def _passos_trazer(self, item: str, fala: str, i: rep.Interacao | None = None) -> list[Passo]:
        """Sai pela beirada, volta com o item na boca, larga e comenta."""
        x0, _, x1, _ = self._area
        da_esquerda = self._acaso.random() < 0.5
        entrada = x0 - LADO * 0.6 if da_esquerda else x1 - LADO * 0.4
        alvo = self._dentro((self._acaso.uniform(x0 + 200, x1 - 400), self.y))
        return [
            Passo("andar", destino=(x1 - LADO * 0.3 if da_esquerda else x0 - LADO * 0.7, self.y), anim="correndo", vel=VEL_CORRER),
            Passo("chamar", acao=lambda: setattr(self, "x", entrada)),
            Passo("andar", destino=alvo, anim=f"andando-{item}"),
            Passo("chamar", acao=lambda: self._largar(item, fala if item == "bilhete" else "")),
            Passo("falar", anim="acenando" if i is None else "falando", texto=fala, interacao=i),
        ]

    def _dentro(self, ponto: tuple[float, float]) -> tuple[float, float]:
        x0, y0, x1, y1 = self._area
        return min(max(ponto[0], x0), x1 - LADO), min(max(ponto[1], y0 + 120), y1 - LADO)

    def _em_segundo_plano(self, i: rep.Interacao) -> None:
        fazer = acoes.fechar_aba if i.id == "fechar-aba" else acoes.minimizar
        threading.Thread(target=lambda: self._resultado.emit(i.id, bool(fazer())), daemon=True).start()

    def _depois_da_acao(self, ident: str, deu_certo: bool) -> None:
        if self.estado != self.ATIVO:
            return
        i = next((x for x in self._repertorio if x.id == ident), None)
        if i is None:
            return
        if deu_certo:
            self._enfileirar_frente(Passo("falar", anim="feliz", texto=i.textos[0], interacao=i))
        else:
            self._enfileirar_frente(Passo("falar", anim="falando", texto="Hmm, não achei nada pra aprontar aí.", dur=2.5))

    def _mutar(self) -> None:
        travessuras.mutar(self._marca_mudo)
        self._mudo_ate = time.monotonic() + MUDO_DURA_S

    def _desmutar(self) -> None:
        if self._mudo_ate:
            self._mudo_ate = 0.0
            travessuras.restaurar_som(self._marca_mudo)

    def _abrir_notas(self) -> None:
        from alarma.criatura import Notas

        if self._notas is not None:
            return
        self._notas = Notas(self._acaso.choice(DIARIO))
        self._notas.fechada.connect(lambda: setattr(self, "_notas", None))
        self._notas.show()

    def _largar(self, nome: str, recado: str = "") -> None:
        from alarma.balao import Objeto

        if len(self._objetos) >= MAX_OBJETOS:
            return
        anim = self._objetos_anim[nome]
        objeto = Objeto(nome, anim.esquerda if self._esquerda else anim.direita, anim.clipe.fps, recado)
        bx, by = self._ponto(BOCA)
        objeto.posicionar(bx - objeto.width() // 2, self.y + LADO - objeto.height() + 6)
        objeto.clicado.connect(self._objeto_clicado)
        objeto.destroyed.connect(lambda *_: self._objetos.remove(objeto) if objeto in self._objetos else None)
        objeto.show()
        objeto.posicionar(bx - objeto.width() // 2, self.y + LADO - objeto.height() + 6)
        self._objetos.append(objeto)

    def _objeto_clicado(self, objeto) -> None:
        if objeto.recado:
            from alarma.balao import Balao

            b = Balao(objeto.recado)
            b.show()
            b.posicionar(objeto.x() - b.width() // 2 + objeto.width() // 2, objeto.y() - b.height())
            QTimer.singleShot(5_000, b.fechar)
        if objeto in self._objetos:
            self._objetos.remove(objeto)
        objeto.close()

    def limpar_objetos(self) -> None:
        for objeto in list(self._objetos):
            objeto.close()
        self._objetos.clear()

    # ---- fala ----

    def _falar_reacao(self, chave: str, anim: str = "falando", curto: bool = False, **campos) -> None:
        modelo = self._acaso.choice(rep.REACOES[chave])
        texto = rep.preencher(modelo, {**self.cerebro.fatos, **{k: str(v) for k, v in campos.items()}}) or modelo
        self._enfileirar(Passo("falar", dur=1.8 if curto else 0.0, anim=anim, texto=texto))

    def _enfileirar(self, *passos: Passo) -> None:
        self._fila.extend(passos)

    def _enfileirar_frente(self, *passos: Passo) -> None:
        for passo in reversed(passos):
            self._fila.appendleft(passo)

    def _duracao_fala(self, texto: str) -> float:
        return min(12.0, 2.2 + len(texto) * 0.055)

    def _abrir_balao(self, passo: Passo) -> None:
        from alarma.balao import Balao

        self._fechar_falas()
        pergunta = passo.extra.get("pergunta")
        votar = passo.interacao is not None and passo.interacao.tipo in (rep.FALA, rep.INFO)
        b = Balao(passo.texto, votar=votar, pergunta=bool(pergunta))
        i = passo.interacao
        if i is not None:
            b.gostei.connect(lambda: self._votar(i, True))
            b.nao_gostei.connect(lambda: self._votar(i, False))
        if pergunta:
            b.respondido.connect(lambda texto: self._respondeu(pergunta, texto))
            b.fechado.connect(lambda: self._pergunta_fechada(b))
            passo.dur = 25.0
        b.show()
        if pergunta:
            b.activateWindow()
            b.campo.setFocus()
        self._balao = b
        self._seguir_falas()
        self._dizer_alto(passo.texto)

    def _abrir_placa(self, passo: Passo) -> None:
        from alarma.balao import Placa

        self._fechar_falas()
        self._esquerda = False
        p = Placa(passo.titulo, passo.texto)
        p.clicada.connect(self._placa_clicada)
        p.show()
        self._placa = p
        self._seguir_falas()
        self._dizer_alto(passo.texto)

    def _placa_clicada(self) -> None:
        if self._passo is not None and self._passo.tipo == "placa":
            self._passo.dur = 0.0

    def _dizer_alto(self, texto: str) -> None:
        if self.cfg.falar_alto:
            acoes.falar(texto)

    def _seguir_falas(self) -> None:
        if self._balao is not None:
            cx, cy = self._ponto(CABECA)
            ponta = self._balao.ponta()
            self._balao.posicionar(cx - ponta.x(), cy - ponta.y())
        if self._placa is not None:
            bx, by = self._ponto(CABO)
            base = self._placa.base()
            self._placa.posicionar(bx - base.x(), by - base.y() + 4)

    def _votar(self, i: rep.Interacao, gostou: bool) -> None:
        agora = time.time()
        if gostou:
            self._recompensa(agora, acao=i.id, forca=1.3, reacao="aprendeu")
        else:
            self.cerebro.punir(agora, acao=i.id, forca=1.2)
            self.cerebro.salvar()
            self._enfileirar_frente(Passo("falar", dur=1.8, anim="falando", texto=self._acaso.choice(rep.REACOES["nao_gostou"])))
        if self._passo is not None and self._passo.tipo == "falar":
            self._passo.dur = 0.0

    def _respondeu(self, fato: str, texto: str) -> None:
        self.cerebro.aprender_fato(fato, texto)
        self.cerebro.xp += 2
        self.cerebro.salvar()
        if self._passo is not None:
            self._passo.dur = 0.0
        self._enfileirar_frente(Passo("falar", dur=2.2, anim="feliz", texto=self._acaso.choice(rep.REACOES["resposta"])))

    def _pergunta_fechada(self, balao) -> None:
        if not balao.respondeu and self._passo is not None and self._passo.tipo == "falar":
            self._passo.dur = 0.0
            self._enfileirar_frente(Passo("falar", dur=1.8, anim="falando", texto=self._acaso.choice(rep.REACOES["sem_resposta"])))

    # ---- carinho, queijo e tapa ----

    def _recompensa(self, agora: float, acao: str | None = None, forca: float = 1.0, queijo: bool = False, reacao: str = "carinho") -> None:
        nivel = self.cerebro.nivel
        self.cerebro.recompensar(agora, forca=forca, acao=acao, queijo=queijo)
        self.cerebro.notar_atividade(datetime.now().hour)
        self._enfileirar_frente(Passo("falar", dur=2.2, anim="comendo" if queijo else "feliz", texto=self._acaso.choice(rep.REACOES[reacao])))
        if self.cerebro.nivel > nivel:
            novo = f"segredo-{(self.cerebro.nivel - 2) % len(rep.SEGREDOS)}"
            self.cerebro.desbloquear(novo)
            segredo = rep.preencher(rep.segredo(int(novo.split("-")[1])), self.cerebro.fatos) or ""
            texto = rep.preencher(self._acaso.choice(rep.REACOES["nivel"]), {"nivel": str(self.cerebro.nivel)}) or ""
            self._fila.insert(1, Passo("falar", anim="feliz", texto=f"{texto} {segredo}".strip()))
        self.cerebro.salvar()
        self.mudou.emit()

    def dar_queijo(self) -> None:
        if self.estado == self.AUSENTE:
            self.aparecer()
        if self.estado == self.ATIVO:
            self._interromper()
            self._recompensa(time.time(), queijo=True, reacao="queijo")

    def fazer_carinho(self) -> None:
        if self.estado == self.ATIVO:
            self._interromper()
            self._recompensa(time.time())

    def _interromper(self) -> None:
        """Para o passo atual sem perder o resto da fila."""
        if self._passo is not None and self._passo.tipo in ("falar", "placa", "anim", "seguir", "arrastar", "tremer", "ir-ao-cursor"):
            self._passo = None
            self._fechar_falas()

    def tapa(self) -> None:
        if self.estado == self.AUSENTE:
            return
        agora_mono, agora = time.monotonic(), time.time()
        if self.estado == self.DORMINDO:
            self._enfileirar_frente(Passo("falar", dur=1.5, anim="cochilando", texto="Zzz... me deixa dormir..."))
            self._passo = None
            return
        self._desmutar()
        expulso = self._tapas.bater(agora_mono)
        self.cerebro.punir(agora, forca=1.5 if expulso else 1.0)
        self.cerebro.notar_atividade(datetime.now().hour)
        self.cerebro.salvar()
        self._limpar()
        self._enfileirar(Passo("anim", 0.45, "acerto"))
        cursor = self._tela.cursor() if self._tela else None
        if expulso:
            self._falar_reacao("expulso", curto=True)
            self._sair_correndo()
            self._enfileirar(Passo("chamar", acao=lambda: self._sumir_ja(comp.espera_depois_de_expulso(self.cfg.intensidade, self._acaso))))
        else:
            self._falar_reacao("tapa", curto=True)
            self._enfileirar(Passo("andar", destino=self._longe_de(cursor), anim="correndo", vel=VEL_CORRER))
            self._enfileirar(Passo("anim", 1.5, "sentado"))
            self._enfileirar(Passo("chamar", acao=self._proxima))
        self.mudou.emit()

    def _sair_correndo(self) -> None:
        x0, _, x1, _ = self._area
        esquerda = self.x + LADO / 2 < (x0 + x1) / 2
        self._enfileirar(Passo("andar", destino=(x0 - LADO if esquerda else x1, self.y), anim="correndo", vel=VEL_CORRER * 1.3))

    def mandar_embora(self) -> None:
        if self.estado == self.ATIVO:
            self._limpar()
            self._enfileirar(Passo("falar", dur=1.5, anim="acenando", texto="Tá bom, tchau! Até mais."))
            self._sair()

    def _longe_de(self, cursor: tuple[int, int] | None) -> tuple[float, float]:
        if cursor is None:
            return self._local_aleatorio()
        cx, cy = self.x + LADO / 2, self.y + LADO / 2
        dx, dy = cx - cursor[0], cy - cursor[1]
        d = max(1.0, (dx * dx + dy * dy) ** 0.5)
        return self._dentro((self.x + dx / d * 320, self.y + dy / d * 200))

    def _menu(self, onde: QPoint) -> None:
        menu = QMenu()
        itens = [
            ("🧀  Dar queijo", self.dar_queijo),
            ("💗  Fazer carinho", self.fazer_carinho),
            (None, None),
            ("👍  Gostei do que você fez", lambda: self._recompensa(time.time(), forca=1.5, reacao="aprendeu")),
            ("👎  Não gostei do que você fez", self._nao_gostei),
            (None, None),
            ("💤  Dormir por 1 hora", lambda: self.dormir((datetime.now() + timedelta(hours=1)).isoformat(timespec="minutes"))),
            ("👋  Ir embora por agora", self.mandar_embora),
            ("⚙️  Painel de controle", self.abrir_painel.emit),
        ]
        for texto, acao in itens:
            if texto is None:
                menu.addSeparator()
                continue
            a = QAction(texto, menu)
            a.triggered.connect(acao)
            menu.addAction(a)
        menu.exec(onde)

    def _nao_gostei(self) -> None:
        self.cerebro.punir(time.time(), forca=1.5)
        self.cerebro.salvar()
        self._interromper()
        self._enfileirar_frente(Passo("falar", dur=2.0, anim="falando", texto=self._acaso.choice(rep.REACOES["nao_gostou"])))

    def esquecer(self) -> None:
        self.cerebro.esquecer_tudo()
        self.mudou.emit()

    # ---- quadro a quadro ----

    def _ponto(self, ponto: tuple[int, int]) -> tuple[int, int]:
        px = ponto[0] * ESCALA
        if self._esquerda:
            px = LADO - px
        return int(self.x + px), int(self.y + ponto[1] * ESCALA)

    def _mover(self) -> None:
        if self._tela is not None and self._tela.pronta():
            self._tela.mover(round(self.x), round(self.y))

    def _usar(self, anim: str, agora: float) -> None:
        if anim != self._anim:
            self._anim = anim
            self._anim_desde = agora

    def _quadro(self) -> None:
        agora = time.monotonic()
        dt = min(0.2, agora - self._ultimo)
        self._ultimo = agora
        if self._janela is None or not self._janela.isVisible():
            return
        if self._passo is None:
            self._comecar_proximo(agora)
        passo = self._passo
        if passo is not None:
            self._rodar(passo, agora, dt)
        self._sentir_carinho(agora)
        self._desenhar(agora)
        self._mover()
        self._seguir_falas()

    def _comecar_proximo(self, agora: float) -> None:
        while self._fila:
            passo = self._fila.popleft()
            if passo.tipo == "chamar":
                passo.acao()
                if self._passo is not None or not self._janela.isVisible():
                    return
                continue
            self._passo = passo
            self._inicio_passo = agora
            if passo.tipo == "falar":
                if not passo.dur:
                    passo.dur = self._duracao_fala(passo.texto)
                self._abrir_balao(passo)
            elif passo.tipo == "placa":
                passo.anim = "placa"
                passo.dur = passo.dur or max(7.0, self._duracao_fala(passo.texto) + 3)
                self._abrir_placa(passo)
            return
        self._passo = None

    def _terminar(self) -> None:
        if self._passo is not None and self._passo.tipo in ("falar", "placa"):
            self._fechar_falas()
        self._passo = None

    def _rodar(self, passo: Passo, agora: float, dt: float) -> None:
        idade = agora - self._inicio_passo
        anim = passo.anim
        if passo.tipo in ("andar", "seguir", "ir-ao-cursor"):
            alvo = passo.destino
            cursor = self._tela.cursor() if self._tela else None
            if passo.tipo in ("seguir", "ir-ao-cursor") and cursor is not None:
                bx, by = BOCA[0] * ESCALA, BOCA[1] * ESCALA
                distancia = 90 if passo.tipo == "seguir" else 0
                lado = -1 if cursor[0] < self.x + LADO / 2 else 1
                alvo = (cursor[0] - (LADO - bx if lado < 0 else bx) - lado * distancia, cursor[1] - by)
            if alvo is None:
                self._terminar()
                return
            dx, dy = alvo[0] - self.x, alvo[1] - self.y
            d = (dx * dx + dy * dy) ** 0.5
            passo_px = passo.vel * dt
            if d <= max(2.0, passo_px):
                self.x, self.y = alvo
                if passo.tipo != "seguir":
                    self._terminar()
                anim = "sentado" if passo.tipo == "seguir" else anim
            else:
                self.x += dx / d * passo_px
                self.y += dy / d * passo_px
                if abs(dx) > 1:
                    self._esquerda = dx < 0
                if anim == "correndo":
                    anim = self._direcao_corrida(dx, dy)
            if passo.dur and idade >= passo.dur:
                self._terminar()
        elif passo.tipo == "arrastar":
            sentido = 1 if self._esquerda else -1  # anda de ré, puxando
            self.x += sentido * VEL_ARRASTAR * dt
            self.x = min(max(self.x, self._area[0]), self._area[2] - LADO)
            bx, by = self._ponto(BOCA)
            QCursor.setPos(bx, by)
            if idade >= passo.dur:
                self._terminar()
        elif passo.tipo == "tremer":
            cursor = self._tela.cursor() if self._tela else None
            if cursor is not None:
                QCursor.setPos(cursor[0] + self._acaso.randint(-5, 5), cursor[1] + self._acaso.randint(-5, 5))
            if idade >= passo.dur:
                self._terminar()
        else:
            if passo.extra.get("escondido"):
                self.x = self._area[2] - LADO * 0.25
            if idade >= passo.dur:
                self._terminar()
        self._usar(anim, agora)

    def _direcao_corrida(self, dx: float, dy: float) -> str:
        if abs(dy) < abs(dx) * 0.4:
            return "correndo"
        if abs(dx) < abs(dy) * 0.4:
            return "correndo-cima" if dy < 0 else "correndo-baixo"
        return "correndo-cima-lado" if dy < 0 else "correndo-baixo-lado"

    def _sentir_carinho(self, agora: float) -> None:
        if self.estado != self.ATIVO or self._tela is None:
            return
        if self._passo is not None and self._passo.tipo in ("arrastar", "tremer"):
            return
        cursor = self._tela.cursor()
        em_cima = cursor is not None and self.x + 30 <= cursor[0] <= self.x + LADO - 20 and self.y + 60 <= cursor[1] <= self.y + LADO
        if self._carinho.notar(agora, cursor, em_cima) and agora - self._ultimo_carinho > 5:
            self._ultimo_carinho = agora
            self._interromper()
            self._recompensa(time.time())

    def _desenhar(self, agora: float) -> None:
        animacao = self._anims.get(self._anim) or self._anims["sentado"]
        quadros = animacao.esquerda if self._esquerda else animacao.direita
        self._janela.setPixmap(quadros[animacao.clipe.indice(agora - self._anim_desde)])

    # ---- para o painel ----

    def resumo(self) -> str:
        if not self.cfg.pet_ligado:
            return "Pet desligado"
        if self.cfg.dormindo(datetime.now()) or self.estado == self.DORMINDO:
            if self.cfg.dormir_ate == config.SEMPRE:
                return "Dormindo até você acordar ele"
            try:
                return f"Dormindo até {datetime.fromisoformat(self.cfg.dormir_ate):%H:%M}"
            except ValueError:
                return "Dormindo"
        if self._alarme_na_tela():
            return "Fugindo do alarme"
        if self.estado == self.ATIVO:
            return "Na tela agora"
        minutos = round(self.segundos_ate_voltar() / 60)
        return "Volta a qualquer momento" if minutos < 1 else f"Volta em uns {minutos} min"
