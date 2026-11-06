"""O rato de estimação: aparece do nada, senta, fala, segura placas, carrega coisas,
apronta, sente fome e tédio, e aprende com carinho, queijo e tapa.

O pet roda uma fila de passos (surgir, andar, falar, arrastar o cursor...). Cada
interação do repertório vira alguns passos. Enquanto o rato do alarme está na
tela, o pet sai de cena. Ele anda por todos os monitores: o mapa (telas.py) diz
por onde passar de um para o outro.
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

from alarma import acoes, aparencia, config, janela, lembretes, necessidades, sistema, sprites, telas, travessuras
from alarma import comportamento as comp
from alarma import repertorio as rep
from alarma.cerebro import Cerebro, caminho_padrao as caminho_cerebro
from alarma.informacoes import Informante
from alarma.logica import Alarme
from alarma.registro import caminho_mudo

LADO = 196
ESCALA = LADO / 48
QUADRO_MS = 40
DECIDIR_MS = 1_000
RELER_MS = 3_000
CUIDAR_MS = 30_000
LEMBRETES_MS = 15_000
BUSCAR_MS = 20 * 60 * 1000
VEL_ANDAR = 110.0
VEL_CORRER = 420.0
VEL_ARRASTAR = 140.0
VEL_BOLA = 900.0
MAX_OBJETOS = 10
ESPERA_BOOT_MS = 4_000
VIDEO_A_CADA_S = 3600.0
MUDO_DURA_S = 25.0
VOLUME_DURA_S = 20.0
ARRASTO_MIN_PX = 6

ITENS = ("queijo", "meia", "bilhete", "moeda", "flor", "presente", "bolinha", "biscoito", "maca", "clipe", "lapis",
         "pena", "folha", "estrela", "cogumelo", "botao", "papel")
COMIDAS = {"queijo": ("Queijo", 35), "biscoito": ("Biscoito", 25), "maca": ("Maçã", 20)}
ANIMACOES = (
    "sentado", "falando", "placa", "acenando", "comendo", "feliz", "cochilando", "andando", "puxando", "surgindo",
    "triste", "morto", "pendurado",
    "acerto", "correndo", "correndo-cima", "correndo-baixo", "correndo-cima-lado", "correndo-baixo-lado",
    *(f"andando-{i}" for i in ITENS),
)
OBJETOS = (*ITENS, "migalhas", "pegadas", "lapide")
# Pontos no quadro de 48 px, rato virado para a direita: origem (24, 44).
BOCA = (39, 37)
CABECA = (29, 13)
CABO = (41, 1)
CANGOTE = (22, 19)  # onde a gente segura quando pega no colo: a nuca, no quadro "pendurado"
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
BILHETES = [
    "Você é incrível. Assinado: o rato.",
    "Lembrete: beber água e me dar queijo.",
    "Hoje vai dar tudo certo!",
    "Eu tava aqui o tempo todo. 👀",
    "Vale um carinho no rato. Válido hoje.",
    "Se achar meu queijo, me avisa.",
]
NECESSIDADE_FALA = {"barriga": "fome", "diversao": "tedio", "felicidade": "triste"}


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
    """A janela que é o rato. Clique é tapa; clicar e arrastar pega no colo; botão direito abre o menu."""

    tapa = Signal()
    menu = Signal(QPoint)
    pegou = Signal(QPoint)
    arrastou = Signal(QPoint)
    soltou = Signal(QPoint)

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
        self.setToolTip("Clique: tapa. Clique e arraste: colo. Botão direito: comida, bolinha e mais.")
        self._apertou: QPoint | None = None
        self._arrastando = False

    def mousePressEvent(self, evento: QMouseEvent) -> None:
        if evento.button() == Qt.MouseButton.RightButton:
            self.menu.emit(evento.globalPosition().toPoint())
        elif evento.button() == Qt.MouseButton.LeftButton:
            self._apertou = evento.globalPosition().toPoint()
            self._arrastando = False

    def mouseMoveEvent(self, evento: QMouseEvent) -> None:
        if self._apertou is None:
            return
        onde = evento.globalPosition().toPoint()
        if not self._arrastando and (onde - self._apertou).manhattanLength() >= ARRASTO_MIN_PX:
            self._arrastando = True
            self.pegou.emit(onde)
        if self._arrastando:
            self.arrastou.emit(onde)

    def mouseReleaseEvent(self, evento: QMouseEvent) -> None:
        if evento.button() != Qt.MouseButton.LeftButton or self._apertou is None:
            return
        if self._arrastando:
            self.soltou.emit(evento.globalPosition().toPoint())
        else:
            self.tapa.emit()
        self._apertou = None
        self._arrastando = False

    def contextMenuEvent(self, evento) -> None:
        evento.accept()

    def closeEvent(self, evento: QCloseEvent) -> None:
        if sistema.tem_hyprland():
            evento.ignore()


class Pet(QObject):
    mudou = Signal()
    aviso = Signal(str, str)  # título e texto de uma notificação do sistema
    _resultado = Signal(str, bool)
    abrir_painel = Signal()

    AUSENTE = "ausente"
    ATIVO = "ativo"
    DORMINDO = "dormindo"
    MORTO = "morto"

    def __init__(self, criatura=None, demo: bool = False, acaso: random.Random | None = None) -> None:
        super().__init__()
        self._demo = demo
        self._criatura = criatura
        self._acaso = acaso or random.Random()
        self.cerebro = Cerebro(None if demo else caminho_cerebro())
        self.informante = Informante(self._acaso)
        self.cfg = self._ler_config()
        self.aparencia = aparencia.Aparencia(adotado_em=datetime.now().date().isoformat()) if demo else aparencia.carregar()
        self.nec = necessidades.Necessidades() if demo else necessidades.carregar()
        self.estado = self.MORTO if self.nec.morto else self.AUSENTE
        self._fila: deque[Passo] = deque()
        self._passo: Passo | None = None
        self._inicio_passo = 0.0
        self._ultimo = time.monotonic()
        self._proxima_visita = time.monotonic() + comp.espera_ate_aparecer(self.cfg.intensidade, self._acaso)
        self._fim_visita = 0.0
        self._janela: MascotePet | None = None
        self._tela = None
        self.mapa = telas.Mapa([], LADO)
        self._anims: dict[str, sprites.Animacao] = {}
        self._objetos_anim: dict[str, sprites.Animacao] = {}
        self._anim = "sentado"
        self._anim_desde = 0.0
        self._esquerda = False
        self.x, self.y = 400.0, 400.0
        self._balao = None
        self._placa = None
        self._objetos: list = []
        self._notas = None
        self._bola = None
        self._bola_voo: tuple | None = None
        self._colo = False
        self._tapas = comp.Tapas()
        self._carinho = comp.Carinho()
        self._ultimo_carinho = 0.0
        self._ultimo_video = -VIDEO_A_CADA_S
        self._mudo_ate = 0.0
        self._volume_ate = 0.0
        self._volume_antes: int | None = None
        self._marca_mudo = caminho_mudo()
        self._atual: rep.Interacao | None = None
        self._repertorio = rep.todas()
        self._relogios: list[QTimer] = []
        self._tocados = set() if demo else lembretes.ler_tocados()
        self._pedidos: dict[str, float] = {}
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
        self._janela.pegou.connect(self._pegar)
        self._janela.arrastou.connect(self._arrastar)
        self._janela.soltou.connect(self._soltar)
        self._tela = janela.nova(self._janela)
        self._carregar_sprites()
        self._atualizar_mapa()
        self.cerebro.ligacoes += 1 if boot else 0
        self.cerebro.salvar()
        self.nec.atualizado = self.nec.atualizado or time.time()
        self.informante.buscar(self.cfg.cidade, self.cfg.internet)
        for intervalo, acao in (
            (QUADRO_MS, self._quadro),
            (DECIDIR_MS, self._decidir),
            (RELER_MS, self._reler),
            (CUIDAR_MS, self._cuidar),
            (LEMBRETES_MS, self._lembretes),
            (BUSCAR_MS, self._buscar),
        ):
            relogio = QTimer(self, interval=intervalo)
            relogio.timeout.connect(acao)
            relogio.start()
            self._relogios.append(relogio)
        if self.estado == self.MORTO:
            pass
        elif self._demo or (boot and self.cfg.saudacao_boot and self.cfg.pet_ligado):
            QTimer.singleShot(ESPERA_BOOT_MS if boot else 800, self.saudar)
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.desligar)

    def _buscar(self) -> None:
        self.informante.buscar(self.cfg.cidade, self.cfg.internet)

    def _carregar_sprites(self) -> None:
        montador = aparencia.Montador(self.aparencia)
        self._anims = sprites.carregar(LADO, ANIMACOES, montador=montador)
        self._objetos_anim = sprites.carregar(LADO, OBJETOS, prefixo="objeto-")

    def vestir(self, nova: aparencia.Aparencia) -> None:
        """Troca a aparência (pelo painel). Remonta os sprites na hora."""
        mudou_visual = nova.chave() != self.aparencia.chave()
        self.aparencia = aparencia.validar(nova)
        if not self._demo:
            aparencia.salvar(self.aparencia)
        if mudou_visual and self._janela is not None:
            self._carregar_sprites()
        self.mudou.emit()

    def desligar(self) -> None:
        """Fecha as janelas do pet antes do Qt fechar: janela destruída depois do Qt derruba o programa."""
        for relogio in self._relogios:
            relogio.stop()
        self._relogios.clear()
        self._desmutar()
        self._devolver_volume()
        self.cerebro.salvar()
        self._salvar_nec()
        self._fechar_falas()
        janelas = [*self._objetos, self._notas, self._janela]
        self._objetos.clear()
        self._notas = self._janela = self._bola = None
        self._anims, self._objetos_anim = {}, {}  # QPixmap solto depois do Qt também derruba
        if self.estado != self.MORTO:
            self.estado = self.AUSENTE
        for widget in janelas:
            if widget is not None and Shiboken.isValid(widget):
                widget.hide()
                Shiboken.delete(widget)

    def _salvar_nec(self) -> None:
        if not self._demo:
            necessidades.salvar(self.nec)

    def _reler(self) -> None:
        antes = self.cfg
        self.cfg = self._ler_config()
        if antes.intensidade != self.cfg.intensidade and self.estado == self.AUSENTE:
            self._agendar()
        if not self.cfg.pet_ligado and self.estado in (self.ATIVO, self.DORMINDO):
            self._sumir_ja()
        self.mudou.emit()

    def _alarme_na_tela(self) -> bool:
        return bool(self._criatura is not None and self._criatura.ativa)

    def _agendar(self, espera: float | None = None) -> None:
        if espera is None:
            espera = comp.espera_ate_aparecer(self.cfg.intensidade, self._acaso)
            if self.aparencia.personalidade == "preguicoso":
                espera *= 1.4
        self._proxima_visita = time.monotonic() + espera
        self.mudou.emit()

    def segundos_ate_voltar(self) -> float:
        return max(0.0, self._proxima_visita - time.monotonic())

    def _decidir(self) -> None:
        agora = time.monotonic()
        self._atualizar_mapa()
        if self.estado == self.MORTO:
            return
        if self._alarme_na_tela():
            if self.estado != self.AUSENTE:
                self._sumir_ja()
            return
        if self._mudo_ate and agora > self._mudo_ate:
            self._desmutar()
        if self._volume_ate and agora > self._volume_ate:
            self._devolver_volume()
        dormindo = self.cfg.dormindo(datetime.now())
        if self._colo:
            return
        if dormindo and self.estado == self.ATIVO and (self._passo is None or self._passo.tipo not in ("dormir", "placa")):
            if not any(p.extra.get("lembrete") for p in self._fila):
                self._ir_dormir()
        elif not dormindo and self.estado == self.DORMINDO:
            self._acordar()
        elif self.estado == self.AUSENTE and not dormindo and self.cfg.pet_ligado and agora >= self._proxima_visita:
            self.aparecer()

    def _atualizar_mapa(self) -> None:
        if self._tela is None:
            return
        try:
            retangulos = self._tela.telas()
        except Exception:
            retangulos = []
        if not retangulos:
            area = self._tela.area(self._tela.cursor())
            retangulos = [area] if area else []
        if retangulos and retangulos != self.mapa.telas:
            self.mapa = telas.Mapa(retangulos, LADO)

    def _tela_do_cursor(self) -> int | None:
        cursor = self._tela.cursor() if self._tela else None
        if cursor is None:
            return None
        return self.mapa.indice((cursor[0] - LADO / 2, cursor[1] - LADO / 2))

    # ---- necessidades e morte ----

    def _cuidar(self) -> None:
        if self.estado == self.MORTO:
            return
        dormindo = self.estado == self.DORMINDO or self.cfg.dormindo(datetime.now())
        avisos = self.nec.atualizar(time.time(), dormindo=dormindo, pode_morrer=self.cfg.pode_morrer)
        self._salvar_nec()
        if "morreu" in avisos:
            self._morrer()
            return
        nome = self.aparencia.nome
        for chave in avisos:
            if chave in ("fome", "tedio", "triste", "fraco"):
                texto = rep.preencher(self._acaso.choice(rep.REACOES[chave]), self.cerebro.fatos) or ""
                self.aviso.emit(f"{nome} precisa de você", texto)
                if self.estado == self.AUSENTE and not dormindo and self.cfg.pet_ligado:
                    self._agendar(self._acaso.uniform(20, 60))
        self.mudou.emit()

    def _morrer(self) -> None:
        nome = self.aparencia.nome
        self.aviso.emit(f"{nome} morreu de {self.nec.causa}", "Abra o painel para se despedir ou adotar outro rato.")
        visivel = self._janela is not None and self._janela.isVisible()
        self._limpar()
        self._devolver_volume()
        self._desmutar()
        if visivel and not self._alarme_na_tela():
            self.estado = self.MORTO
            self._enfileirar(Passo("anim", 6.0, "morto"))
            self._enfileirar(Passo("chamar", acao=lambda: self._largar("lapide", f"Aqui jaz {nome}. Morreu de {self.nec.causa}.", forcar=True)))
            self._enfileirar(Passo("chamar", acao=self._esconder_morto))
        else:
            self.estado = self.MORTO
            self._esconder_morto()
        self.mudou.emit()

    def _esconder_morto(self) -> None:
        self._fila.clear()
        self._passo = None
        if self._janela is not None:
            self._tela.esquecer()
            self._janela.hide()

    def adotar(self, nova: aparencia.Aparencia | None = None) -> None:
        """Um rato novo: aprende tudo de novo e chega com fome de carinho."""
        self.nec.adotar(time.time())
        self._salvar_nec()
        self.cerebro.esquecer_tudo()
        base = nova or self.aparencia
        self.vestir(base.com(adotado_em=datetime.now().date().isoformat()))
        self.estado = self.AUSENTE
        if self._janela is not None:
            texto = rep.preencher(self._acaso.choice(rep.REACOES["nasceu"]), {"rato": self.aparencia.nome}) or ""
            self.aparecer(saudacao=texto)
        self.mudou.emit()

    def _pedir_cuidado(self) -> bool:
        """Antes de cada interação: se alguma necessidade está baixa, ele pede (no máximo uma vez a cada 3 min)."""
        pior = self.nec.pior()
        if pior is None:
            return False
        agora = time.monotonic()
        if agora - self._pedidos.get(pior, -1e9) < 180:
            return False
        self._pedidos[pior] = agora
        chave = "fraco" if self.nec.fraco else NECESSIDADE_FALA[pior]
        texto = rep.preencher(self._acaso.choice(rep.REACOES[chave]), self.cerebro.fatos) or ""
        titulo = {"barriga": "Fome!", "diversao": "Tédio...", "felicidade": "Tristeza..."}[pior]
        self._enfileirar(Passo("placa", texto=texto, titulo=titulo, extra={"anim": "triste" if pior == "felicidade" else "placa"}))
        return True

    def _ocioso(self) -> str:
        """A pose de quando ele está parado: triste se estiver mal."""
        return "triste" if self.nec.fraco or self.nec.felicidade < 25 else "sentado"

    # ---- visitas ----

    def _local_aleatorio(self) -> tuple[float, float]:
        return self.mapa.aleatorio(self._acaso, self._tela_do_cursor())

    def _dentro(self, ponto: tuple[float, float]) -> tuple[float, float]:
        return self.mapa.dentro(ponto)

    def _mostrar(self) -> None:
        if self._janela is not None and not self._janela.isVisible():
            self._tela.esquecer()
            self._janela.show()
            self._mover()

    def aparecer(self, saudacao: str = "") -> None:
        """Surge do nada num canto qualquer e começa uma visita."""
        if self._janela is None or self._alarme_na_tela() or self.estado == self.MORTO:
            return
        self._atualizar_mapa()
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
            self._enfileirar(Passo("anim", 1.0, self._ocioso()))
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
        if self.estado == self.MORTO:
            return
        if self._alarme_na_tela():
            QTimer.singleShot(10_000, self.saudar)
            return
        texto = comp.texto_saudacao(datetime.now(), self.cerebro, self._acaso)
        self.aparecer(saudacao=texto)
        if self.estado != self.ATIVO:
            return
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
            item = self._acaso.choice(("queijo", "flor", "presente", "estrela"))
            self._enfileirar_frente(*self._passos_trazer(item, "Trouxe um presente pra começar o dia!"))

    def _proxima(self) -> None:
        if self.estado != self.ATIVO:
            return
        if time.monotonic() >= self._fim_visita:
            self._sair()
            return
        if not self._pedir_cuidado():
            opcoes = comp.elegiveis(
                self._repertorio + comp.extras(self.cerebro, self.cfg), self.cfg, self.cerebro, self.informante.tem, self._possivel
            )
            plano = comp.planejar(opcoes, self.cfg, self.cerebro, self._acaso, self.aparencia.personalidade)
            if plano.desistiu is not None and self._acaso.random() < 0.5:
                self._falar_reacao("desistiu", curto=True)
            if plano.interacao is not None:
                if plano.teimosa:
                    self._falar_reacao("teimoso", curto=True)
                self._executar(plano.interacao)
        pausa = comp.pausa_entre_interacoes(self.cfg.intensidade, self._acaso)
        self._enfileirar(Passo("anim", pausa, self._ocioso()))
        self._enfileirar(Passo("chamar", acao=self._proxima))

    def _sair(self) -> None:
        self._enfileirar(Passo("andar", destino=self.mapa.saida((self.x, self.y)), anim="andando", vel=VEL_ANDAR * 1.4, extra={"livre": True}))
        self._enfileirar(Passo("chamar", acao=self._sumir_ja))

    def _sumir_ja(self, espera: float | None = None) -> None:
        self._limpar()
        self._desmutar()
        self._devolver_volume()
        if self.estado != self.MORTO:
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

    # ---- lembretes ----

    def _lembretes(self) -> None:
        if self.estado == self.MORTO and not self.cfg.lembretes:
            return
        agora = datetime.now()
        for l in lembretes.devidos(self.cfg.lembretes, agora, self._tocados):
            self._tocados.add(f"{agora.date().isoformat()}/{l.id}")
            if not self._demo:
                lembretes.gravar_tocados(self._tocados)
            self.tocar_lembrete(l)

    def tocar_lembrete(self, l: lembretes.Lembrete) -> None:
        extras = {
            "clima": self.informante.frase("clima_hoje") or self.informante.frase("clima_agora"),
            "noticia": self.informante.frase("noticia_brasil") or self.informante.frase("noticia_mundo"),
        }
        titulo, texto = lembretes.texto_do_aviso(l, self.cerebro.fatos, extras, self._acaso)
        self.aviso.emit(f"{self.aparencia.nome}: {titulo}", texto)
        if l.som:
            from alarma import som

            som.tocar(Alarme.MANHA)
        if self.estado == self.MORTO or self._alarme_na_tela() or self._janela is None:
            return
        dormindo = self.estado == self.DORMINDO
        if dormindo and not l.acordar:
            return
        passo = Passo("placa", texto=texto, titulo=titulo, dur=max(10.0, self._duracao_fala(texto) + 5), extra={"lembrete": True})
        if self.estado == self.ATIVO:
            self._interromper()
            self._enfileirar_frente(passo)
        else:
            volta_a_dormir = dormindo
            self.aparecer()
            self._fila.clear()
            self._enfileirar(Passo("anim", 1.0, "surgindo"), passo)
            if volta_a_dormir:
                self._enfileirar(Passo("chamar", acao=self._ir_dormir))
            else:
                self._enfileirar(Passo("chamar", acao=self._proxima))

    # ---- sono ----

    def dormir(self, ate: str) -> None:
        """ate: config.SEMPRE ou data ISO. Grava no config, que é o que o painel mostra."""
        self.cfg = self.cfg.com(dormir_ate=ate)
        self._gravar_config()
        if self.estado == self.ATIVO:
            self._ir_dormir()
        elif self.estado == self.AUSENTE and self.cfg.dormir_visivel and self._janela is not None:
            self.estado = self.DORMINDO
            self._atualizar_mapa()
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
        x0, y0, x1, y1 = self.mapa.tela((self.x, self.y))
        return x1 - LADO - 20, y1 - LADO + 30

    def _ir_dormir(self) -> None:
        self._limpar()
        self.estado = self.DORMINDO
        self._falar_reacao("dormir", curto=True)
        if self.cfg.dormir_visivel:
            self._enfileirar(Passo("andar", destino=self._canto(), anim="andando", extra={"livre": True}))
            self._enfileirar(Passo("dormir", 1e9, "cochilando"))
        else:
            self._enfileirar(Passo("andar", destino=self.mapa.saida((self.x, self.y)), anim="andando", vel=VEL_ANDAR * 1.5, extra={"livre": True}))
            self._enfileirar(Passo("chamar", acao=self._esconder_dormindo))

    def _deitar_no_canto(self) -> None:
        cursor = self._tela_do_cursor()
        x0, y0, x1, y1 = self.mapa.telas[cursor or 0]
        self.x, self.y = x1 - LADO - 20, y1 - LADO + 30
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
        if permissao == rep.P_EMPURRAR:
            return acoes.pode_empurrar()
        if permissao == rep.P_VOLUME:
            return acoes.pode_mexer_volume() and not self._volume_ate
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
            self.nec.divertir(3)
            self._brincar(i)
        elif i.tipo == rep.TRAVESSURA:
            self.nec.divertir(4)
            self._aprontar(i)

    def _brincar(self, i: rep.Interacao) -> None:
        fala = i.textos[0] if i.textos else ""
        lento = 0.7 if self.aparencia.personalidade == "preguicoso" else 1.0
        if i.id == "passear":
            self._enfileirar(Passo("andar", destino=self._local_aleatorio(), anim="andando", vel=VEL_ANDAR * lento))
        elif i.id == "farejar":
            self._enfileirar(Passo("falar", anim="falando", texto=fala, dur=2.0))
            for _ in range(2):
                alvo = self._dentro((self.x + self._acaso.uniform(-200, 200), self.y))
                self._enfileirar(Passo("andar", destino=alvo, anim="andando", vel=VEL_ANDAR * 0.6))
        elif i.id == "correr":
            if fala:
                self._enfileirar(Passo("falar", anim="feliz", texto=fala, dur=1.5))
            for _ in range(3):
                self._enfileirar(Passo("andar", destino=self._local_aleatorio(), anim="correndo", vel=VEL_CORRER * lento))
        elif i.id == "seguir-cursor":
            self._enfileirar(Passo("falar", anim="falando", texto=fala, dur=2.0))
            self._enfileirar(Passo("seguir", 6.0, "andando"))
            self._enfileirar(Passo("anim", 2.0, "sentado"))
        elif i.id == "esconder":
            self._enfileirar(Passo("falar", anim="falando", texto=fala, dur=1.8))
            saida = self.mapa.saida((self.x, self.y))
            self._enfileirar(Passo("andar", destino=saida, anim="correndo", vel=VEL_CORRER, extra={"livre": True}))
            self._enfileirar(Passo("anim", 4.0, "sentado", extra={"escondido": True}))
            self._enfileirar(Passo("chamar", acao=self._reaparecer_perto))
            self._enfileirar(Passo("anim", 1.0, "surgindo"))
            self._falar_reacao("voltou", anim="feliz", curto=True)
        elif i.id == "bolinha-sozinho":
            self._enfileirar(Passo("falar", anim="feliz", texto=fala, dur=2.0))
            self._enfileirar(Passo("chamar", acao=lambda: self.brincar_bolinha(sozinho=True)))
        elif i.id in ("pedir-carinho", "pedir-queijo", "pedir-colo"):
            self._enfileirar(Passo("placa", texto=fala, titulo=TITULOS[rep.BRINCADEIRA], interacao=i))
        elif i.id == "sentar-olhar":
            self._enfileirar(Passo("anim", self._acaso.uniform(4, 8), self._ocioso()))
        else:
            anim = {"cochilar": "cochilando", "espreguicar": "cochilando", "comer": "comendo", "dancar": "feliz",
                    "pular": "feliz", "acenar": "acenando"}.get(i.id, "sentado")
            if fala:
                self._enfileirar(Passo("falar", anim=anim, texto=fala, dur=2.5, interacao=i))
            dur = 5.0 if anim == "cochilando" else 2.5
            if self.aparencia.personalidade == "preguicoso" and anim == "cochilando":
                dur *= 2
            self._enfileirar(Passo("anim", dur, anim))

    def _reaparecer_perto(self) -> None:
        self.x, self.y = self._local_aleatorio()

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
        elif i.id in ("fechar-aba", "minimizar", "empurrar-janela"):
            self._enfileirar(Passo("anim", 1.2, "feliz"))
            self._enfileirar(Passo("chamar", acao=lambda: self._em_segundo_plano(i)))
        elif i.id in ("abrir-calculadora", "abrir-recado"):
            self._enfileirar(Passo("anim", 1.0, "feliz"))
            self._enfileirar(Passo("chamar", acao=lambda: acoes.abrir_app("calculadora" if i.id == "abrir-calculadora" else "notas")))
            self._enfileirar(Passo("falar", anim="falando", texto=fala, interacao=i))
        elif i.id == "baixar-volume":
            self._enfileirar(Passo("chamar", acao=self._baixar_volume))
            self._enfileirar(Passo("falar", anim="falando", texto=fala, interacao=i))
        elif i.id == "notificacao":
            recado = rep.preencher(self._acaso.choice(BILHETES), self.cerebro.fatos) or BILHETES[0]
            self._enfileirar(Passo("chamar", acao=lambda: self.aviso.emit(f"Recado do {self.aparencia.nome}", recado)))
            self._enfileirar(Passo("falar", anim="acenando", texto=fala, interacao=i))
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
        saida = self.mapa.saida((self.x, self.y))
        tela = self.mapa.tela((self.x, self.y))
        alvo = self._dentro((self._acaso.uniform(tela[0] + 150, max(tela[0] + 151, tela[2] - 350)), self.y))
        recado = self._acaso.choice(BILHETES) if item in ("bilhete", "papel") else ""
        return [
            Passo("andar", destino=saida, anim="correndo", vel=VEL_CORRER, extra={"livre": True}),
            Passo("anim", 0.6, "sentado", extra={"invisivel": True}),
            Passo("andar", destino=alvo, anim=f"andando-{item}"),
            Passo("chamar", acao=lambda: self._largar(item, recado)),
            Passo("falar", anim="acenando" if i is None else "falando", texto=fala, interacao=i),
        ]

    def _em_segundo_plano(self, i: rep.Interacao) -> None:
        if i.id == "fechar-aba":
            fazer = acoes.fechar_aba
        elif i.id == "minimizar":
            fazer = acoes.minimizar
        else:
            dx = self._acaso.choice((-1, 1)) * self._acaso.randint(60, 140)
            fazer = lambda: acoes.empurrar_janela(dx, self._acaso.randint(-30, 30))  # noqa: E731
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

    def _baixar_volume(self) -> None:
        atual = acoes.volume()
        if atual is None or atual <= 15:
            return
        self._volume_antes = atual
        self._volume_ate = time.monotonic() + VOLUME_DURA_S
        acoes.definir_volume(max(10, atual // 3))

    def _devolver_volume(self) -> None:
        if self._volume_ate and self._volume_antes is not None:
            acoes.definir_volume(self._volume_antes)
        self._volume_ate = 0.0
        self._volume_antes = None

    def _abrir_notas(self) -> None:
        from alarma.criatura import Notas

        if self._notas is not None:
            return
        self._notas = Notas(self._acaso.choice(DIARIO))
        self._notas.fechada.connect(self._notas_fechadas)
        self._notas.show()

    def _notas_fechadas(self) -> None:
        self._notas = None

    # ---- coisas na tela ----

    def _largar(self, nome: str, recado: str = "", forcar: bool = False, onde: tuple[int, int] | None = None):
        from alarma.balao import Objeto

        if (len(self._objetos) >= MAX_OBJETOS and not forcar) or nome not in self._objetos_anim:
            return None
        anim = self._objetos_anim[nome]
        objeto = Objeto(nome, anim.esquerda if self._esquerda else anim.direita, anim.clipe.fps, recado)
        if onde is None:
            bx, _ = self._ponto(BOCA)
            onde = (bx - objeto.width() // 2, int(self.y + LADO - objeto.height() + 6))
        objeto.clicado.connect(self._objeto_clicado)
        objeto.show()
        objeto.posicionar(*onde)
        self._objetos.append(objeto)
        return objeto

    def _objeto_clicado(self, objeto) -> None:
        from alarma.balao import Balao

        self.nec.divertir(4)
        if objeto is self._bola:
            self._chutar_bola(humano=True)
            return
        texto = objeto.recado
        if objeto.nome == "presente":
            curiosas = [i for i in self._repertorio if i.categoria in (rep.CURIOSIDADES, rep.PIADAS)]
            texto = f"🎁 {self._acaso.choice(curiosas).textos[0]}"
            self.cerebro.xp += 2
        elif objeto.nome == "estrela":
            self.cerebro.xp += 5
            texto = self._acaso.choice(rep.REACOES["estrela"])
        elif objeto.nome in COMIDAS and self.estado == self.ATIVO:
            self._ir_comer(objeto)
            return
        if texto:
            b = Balao(texto)
            b.show()
            b.posicionar(objeto.x() - b.width() // 2 + objeto.width() // 2, objeto.y() - b.height())
            QTimer.singleShot(6_000, b.fechar)
        self._tirar_objeto(objeto)
        self.mudou.emit()

    def _tirar_objeto(self, objeto) -> None:
        if objeto in self._objetos:
            self._objetos.remove(objeto)
        if objeto is self._bola:
            self._bola = None
            self._bola_voo = None
        if Shiboken.isValid(objeto):
            objeto.close()

    def limpar_objetos(self) -> None:
        for objeto in list(self._objetos):
            self._tirar_objeto(objeto)
        self._objetos.clear()

    # ---- comida e bolinha ----

    def dar_comida(self, tipo: str = "queijo") -> None:
        """Larga a comida perto do cursor; o rato vai até ela e come."""
        if self.estado == self.MORTO or self._janela is None:
            return
        if self.estado != self.ATIVO:
            if self.estado == self.DORMINDO:
                self._acordar(mandar=True)
            else:
                self.aparecer()
        if self.estado != self.ATIVO:
            return
        cursor = self._tela.cursor() or (int(self.x + LADO), int(self.y + LADO))
        objeto = self._largar(tipo, forcar=True, onde=(cursor[0] - 48, cursor[1] - 48))
        if objeto is not None:
            self._interromper()
            self._ir_comer(objeto)

    def dar_queijo(self) -> None:
        self.dar_comida("queijo")

    def _ir_comer(self, objeto) -> None:
        alvo = self._dentro((objeto.x() + objeto.width() / 2 - BOCA[0] * ESCALA, objeto.y() + objeto.height() - LADO))
        self._fila.clear()
        self._enfileirar(
            Passo("andar", destino=alvo, anim="correndo", vel=VEL_CORRER * 0.8),
            Passo("chamar", acao=lambda: self._comer(objeto)),
            Passo("anim", 3.0, "comendo"),
            Passo("chamar", acao=self._proxima),
        )

    def _comer(self, objeto) -> None:
        nome = getattr(objeto, "nome", "queijo") if Shiboken.isValid(objeto) else "queijo"
        quanto = COMIDAS.get(nome, ("", 25))[1]
        if Shiboken.isValid(objeto):
            self._tirar_objeto(objeto)
        self.nec.alimentar(quanto)
        self._recompensa(time.time(), queijo=True, reacao="comida", frente=False)
        self._salvar_nec()

    def brincar_bolinha(self, sozinho: bool = False) -> None:
        """Larga uma bolinha: o rato corre atrás. Clicar nela chuta para longe."""
        if self.estado == self.MORTO or self._janela is None:
            return
        if self.estado != self.ATIVO:
            if self.estado == self.DORMINDO:
                self._acordar(mandar=True)
            else:
                self.aparecer()
        if self.estado != self.ATIVO:
            return
        if self._bola is None or not Shiboken.isValid(self._bola):
            perto = (int(self.x + LADO * (0.2 if self._esquerda else 0.9)), int(self.y + LADO - 80))
            self._bola = self._largar("bolinha", forcar=True, onde=perto)
            if self._bola is not None:
                self._bola.setToolTip("Clique para chutar a bolinha")
        if self._bola is None:
            return
        self._interromper()
        self._fila.clear()
        self._enfileirar(Passo("bola", 25.0, "correndo", vel=VEL_CORRER, extra={"chutes": 0, "sozinho": sozinho}))
        self._enfileirar(Passo("chamar", acao=self._fim_da_bola))

    def _chutar_bola(self, humano: bool = False) -> None:
        """A bola voa para um lugar qualquer, na mesma tela ou em outra."""
        if self._bola is None or not Shiboken.isValid(self._bola):
            return
        destino = self.mapa.aleatorio(self._acaso, None if humano else self.mapa.indice((self.x, self.y)), chao=0.8)
        origem = (self._bola.x(), self._bola.y())
        fim = (destino[0] + LADO / 2 - 48, destino[1] + LADO - 96)
        self._bola_voo = (origem, fim, time.monotonic(), max(0.35, ((fim[0] - origem[0]) ** 2 + (fim[1] - origem[1]) ** 2) ** 0.5 / VEL_BOLA))
        if humano:
            self.nec.brincar(8)
            if self.estado == self.ATIVO and (self._passo is None or self._passo.tipo != "bola"):
                self.brincar_bolinha()

    def _fim_da_bola(self) -> None:
        self.nec.brincar(20)
        self._salvar_nec()
        self._recompensa(time.time(), reacao="bolinha", frente=False)
        if self._bola is not None:
            self._tirar_objeto(self._bola)
        self._enfileirar(Passo("chamar", acao=self._proxima))

    def _voar_bola(self) -> None:
        if self._bola_voo is None or self._bola is None or not Shiboken.isValid(self._bola):
            return
        (x0, y0), (x1, y1), inicio, dura = self._bola_voo
        k = min(1.0, (time.monotonic() - inicio) / dura)
        altura = -4 * 90 * k * (1 - k)
        self._bola.posicionar(int(x0 + (x1 - x0) * k), int(y0 + (y1 - y0) * k + altura))
        if k >= 1:
            self._bola_voo = None

    # ---- colo ----

    def _pegar(self, onde: QPoint) -> None:
        if self.estado not in (self.ATIVO, self.DORMINDO) or self._janela is None:
            return
        self._colo = True
        self._fechar_falas()
        self._fila.clear()
        self._passo = Passo("colo", 1e9, "pendurado")
        self._inicio_passo = time.monotonic()
        self._arrastar(onde)
        gosta = self.nec.felicidade >= 40 and self.aparencia.personalidade != "preguicoso"
        self._mostrar_fala(self._acaso.choice(rep.REACOES["colo_bom" if gosta else "colo_ruim"]), 1.5)

    def _arrastar(self, onde: QPoint) -> None:
        if not self._colo:
            return
        px = (LADO - CANGOTE[0] * ESCALA) if self._esquerda else CANGOTE[0] * ESCALA
        self.x, self.y = onde.x() - px, onde.y() - CANGOTE[1] * ESCALA
        self._mover()
        self._seguir_falas()

    def _soltar(self, _onde: QPoint) -> None:
        if not self._colo:
            return
        self._colo = False
        self._passo = None
        self.nec.carinho(4)
        self.nec.brincar(6)
        self.estado = self.ATIVO
        chao = self._dentro((self.x, self.y))
        self._enfileirar(Passo("andar", destino=chao, anim="pendurado", vel=700, extra={"livre": True}))
        self._enfileirar(Passo("falar", anim="feliz", texto=self._acaso.choice(rep.REACOES["solto"]), dur=1.6))
        self._fim_visita = max(self._fim_visita, time.monotonic() + 30)
        self._enfileirar(Passo("chamar", acao=self._proxima))
        self.mudou.emit()

    def _mostrar_fala(self, texto: str, dur: float) -> None:
        from alarma.balao import Balao

        self._fechar_falas()
        b = Balao(texto)
        b.show()
        self._balao = b
        self._seguir_falas()
        QTimer.singleShot(int(dur * 1000), self._fechar_balao_solto)

    def _fechar_balao_solto(self) -> None:
        if self._passo is None or self._passo.tipo in ("colo", "anim", "andar", "bola"):
            if self._balao is not None and self._placa is None:
                self._fechar_falas()

    # ---- fala ----

    def _falar_reacao(self, chave: str, anim: str = "falando", curto: bool = False, **campos) -> None:
        modelo = self._acaso.choice(rep.REACOES[chave])
        texto = rep.preencher(modelo, {**self.cerebro.fatos, "rato": self.aparencia.nome, **{k: str(v) for k, v in campos.items()}}) or modelo
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
        self.nec.carinho(6)
        self.cerebro.salvar()
        if self._passo is not None:
            self._passo.dur = 0.0
        self._enfileirar_frente(Passo("falar", dur=2.2, anim="feliz", texto=self._acaso.choice(rep.REACOES["resposta"])))

    def _pergunta_fechada(self, balao) -> None:
        if not balao.respondeu and self._passo is not None and self._passo.tipo == "falar":
            self._passo.dur = 0.0
            self._enfileirar_frente(Passo("falar", dur=1.8, anim="falando", texto=self._acaso.choice(rep.REACOES["sem_resposta"])))

    # ---- carinho, queijo e tapa ----

    def _recompensa(self, agora: float, acao: str | None = None, forca: float = 1.0, queijo: bool = False,
                    reacao: str = "carinho", frente: bool = True) -> None:
        nivel = self.cerebro.nivel
        self.cerebro.recompensar(agora, forca=forca, acao=acao, queijo=queijo)
        self.cerebro.notar_atividade(datetime.now().hour)
        if reacao == "carinho":
            self.nec.carinho(10)
        passo = Passo("falar", dur=2.2, anim="comendo" if queijo else "feliz", texto=self._acaso.choice(rep.REACOES[reacao]))
        if frente:
            self._enfileirar_frente(passo)
        else:
            self._enfileirar(passo)
        if self.cerebro.nivel > nivel:
            novo = f"segredo-{(self.cerebro.nivel - 2) % len(rep.SEGREDOS)}"
            self.cerebro.desbloquear(novo)
            segredo = rep.preencher(rep.segredo(int(novo.split("-")[1])), self.cerebro.fatos) or ""
            texto = rep.preencher(self._acaso.choice(rep.REACOES["nivel"]), {"nivel": str(self.cerebro.nivel)}) or ""
            nivel_passo = Passo("falar", anim="feliz", texto=f"{texto} {segredo}".strip())
            if frente:
                self._fila.insert(1, nivel_passo)
            else:
                self._enfileirar(nivel_passo)
        self.cerebro.salvar()
        self._salvar_nec()
        self.mudou.emit()

    def fazer_carinho(self) -> None:
        if self.estado == self.ATIVO:
            self._interromper()
            self._recompensa(time.time())

    def _interromper(self) -> None:
        """Para o passo atual sem perder o resto da fila."""
        if self._passo is not None and self._passo.tipo in ("falar", "placa", "anim", "seguir", "arrastar", "tremer", "ir-ao-cursor", "bola"):
            self._passo = None
            self._fechar_falas()

    def tapa(self) -> None:
        if self.estado in (self.AUSENTE, self.MORTO) or self._colo:
            return
        agora_mono, agora = time.monotonic(), time.time()
        if self.estado == self.DORMINDO:
            self._enfileirar_frente(Passo("falar", dur=1.5, anim="cochilando", texto="Zzz... me deixa dormir..."))
            self._passo = None
            return
        self._desmutar()
        self._devolver_volume()
        expulso = self._tapas.bater(agora_mono)
        self.cerebro.punir(agora, forca=1.5 if expulso else 1.0)
        self.cerebro.notar_atividade(datetime.now().hour)
        self.cerebro.salvar()
        self.nec.tapa(18 if expulso else 10)
        self._salvar_nec()
        self._limpar()
        self._enfileirar(Passo("anim", 0.45, "acerto"))
        cursor = self._tela.cursor() if self._tela else None
        if expulso:
            self._falar_reacao("expulso", curto=True)
            self._enfileirar(Passo("andar", destino=self.mapa.saida((self.x, self.y)), anim="correndo", vel=VEL_CORRER * 1.3, extra={"livre": True}))
            self._enfileirar(Passo("chamar", acao=lambda: self._sumir_ja(comp.espera_depois_de_expulso(self.cfg.intensidade, self._acaso))))
        else:
            self._falar_reacao("tapa", curto=True)
            self._enfileirar(Passo("andar", destino=self._longe_de(cursor), anim="correndo", vel=VEL_CORRER))
            self._enfileirar(Passo("anim", 1.5, self._ocioso()))
            self._enfileirar(Passo("chamar", acao=self._proxima))
        self.mudou.emit()

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
        from alarma import pixelui

        menu = QMenu()
        pixelui.estilizar_menu(menu)
        comer = QMenu("Dar comida", menu)
        pixelui.estilizar_menu(comer)
        for tipo, (nome, _) in COMIDAS.items():
            a = QAction(pixelui.icone_item(tipo), nome, comer)
            a.triggered.connect(lambda _=False, t=tipo: self.dar_comida(t))
            comer.addAction(a)
        menu.addMenu(comer).setIcon(pixelui.icone("queijo"))
        itens = [
            ("bola", "Brincar de bolinha", self.brincar_bolinha),
            ("coracao", "Fazer carinho", self.fazer_carinho),
            None,
            ("joia", "Gostei do que você fez", lambda: self._recompensa(time.time(), forca=1.5, reacao="aprendeu")),
            ("nao", "Não gostei do que você fez", self._nao_gostei),
            None,
            ("lua", "Dormir por 1 hora", lambda: self.dormir((datetime.now() + timedelta(hours=1)).isoformat(timespec="minutes"))),
            ("tchau", "Ir embora por agora", self.mandar_embora),
            ("engrenagem", "Painel do rato", self.abrir_painel.emit),
        ]
        for item in itens:
            if item is None:
                menu.addSeparator()
                continue
            nome, texto, acao = item
            a = QAction(pixelui.icone(nome), texto, menu)
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
        self._voar_bola()
        if self._janela is None or not self._janela.isVisible():
            return
        if self._passo is None:
            self._comecar_proximo(agora)
        passo = self._passo
        if passo is not None:
            self._rodar(passo, agora, dt)
        self._sentir_carinho(agora)
        self._desenhar(agora)
        if not self._colo:
            self._mover()
        self._seguir_falas()

    def _comecar_proximo(self, agora: float) -> None:
        while self._fila:
            passo = self._fila.popleft()
            if passo.tipo == "chamar":
                passo.acao()
                if self._passo is not None or self._janela is None or not self._janela.isVisible():
                    return
                continue
            if passo.tipo in ("falar", "placa", "anim") and not (passo.extra.get("invisivel") or passo.extra.get("escondido")) \
                    and passo.anim != "morto" and not self.mapa.valido((self.x, self.y)):
                # ficou meio fora da tela (apanhou saindo, por exemplo): volta para dentro antes de parar
                self._fila.appendleft(passo)
                passo = Passo("andar", destino=self.mapa.dentro((self.x, self.y)), anim="correndo", vel=VEL_CORRER, extra={"livre": True})
            self._passo = passo
            self._inicio_passo = agora
            if passo.tipo == "falar":
                if not passo.dur:
                    passo.dur = self._duracao_fala(passo.texto)
                self._abrir_balao(passo)
            elif passo.tipo == "placa":
                passo.anim = passo.extra.get("anim", "placa")
                passo.dur = passo.dur or max(7.0, self._duracao_fala(passo.texto) + 3)
                self._abrir_placa(passo)
            elif passo.tipo == "andar" and passo.destino is not None:
                if passo.extra.get("livre"):
                    passo.extra["rota"] = [passo.destino]
                else:
                    passo.extra["rota"] = self.mapa.caminho((self.x, self.y), passo.destino)
            return
        self._passo = None

    def _terminar(self) -> None:
        if self._passo is not None and self._passo.tipo in ("falar", "placa"):
            self._fechar_falas()
        self._passo = None

    def _andar_ate(self, alvo: tuple[float, float], vel: float, dt: float) -> tuple[bool, float, float]:
        """Um passo na direção do alvo. Retorna (chegou, dx, dy)."""
        dx, dy = alvo[0] - self.x, alvo[1] - self.y
        d = (dx * dx + dy * dy) ** 0.5
        passo_px = vel * dt
        if d <= max(2.0, passo_px):
            self.x, self.y = alvo
            return True, dx, dy
        self.x += dx / d * passo_px
        self.y += dy / d * passo_px
        if abs(dx) > 1:
            self._esquerda = dx < 0
        return False, dx, dy

    def _rodar(self, passo: Passo, agora: float, dt: float) -> None:
        idade = agora - self._inicio_passo
        anim = passo.anim
        if passo.tipo == "andar":
            rota = passo.extra.get("rota") or ([passo.destino] if passo.destino else [])
            if not rota:
                self._terminar()
                return
            chegou, dx, dy = self._andar_ate(rota[0], passo.vel, dt)
            if chegou:
                rota.pop(0)
                if not rota:
                    self._terminar()
            elif anim == "correndo":
                anim = self._direcao_corrida(dx, dy)
            if passo.dur and idade >= passo.dur:
                self._terminar()
        elif passo.tipo in ("seguir", "ir-ao-cursor", "bola"):
            alvo = self._alvo_movel(passo)
            if alvo is None:
                if passo.tipo != "bola" or self._bola is None:
                    self._terminar()
                    return
            else:
                chegou, dx, dy = self._andar_ate(alvo, passo.vel, dt)
                if chegou:
                    if passo.tipo == "ir-ao-cursor":
                        self._terminar()
                    elif passo.tipo == "bola" and self._bola_voo is None:
                        self._pegou_bola(passo)
                    anim = "sentado" if passo.tipo != "bola" else "feliz"
                elif anim == "correndo":
                    anim = self._direcao_corrida(dx, dy)
            if self._passo is passo and passo.dur and idade >= passo.dur:
                self._terminar()
        elif passo.tipo == "arrastar":
            sentido = 1 if self._esquerda else -1  # anda de ré, puxando
            tela = self.mapa.tela((self.x, self.y))
            self.x = min(max(self.x + sentido * VEL_ARRASTAR * dt, tela[0]), tela[2] - LADO)
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
            if passo.extra.get("invisivel") and self._janela is not None:
                self._janela.setWindowOpacity(0.0)
            if idade >= passo.dur:
                if passo.extra.get("invisivel") and self._janela is not None:
                    self._janela.setWindowOpacity(1.0)
                self._terminar()
        self._usar(anim, agora)

    def _alvo_movel(self, passo: Passo) -> tuple[float, float] | None:
        """Para onde ir quando o alvo se mexe (cursor ou bolinha), passando pelas telas certas."""
        bx, by = BOCA[0] * ESCALA, BOCA[1] * ESCALA
        if passo.tipo == "bola":
            if self._bola is None or not Shiboken.isValid(self._bola):
                return None
            ponto = (self._bola.x() + self._bola.width() / 2, self._bola.y() + self._bola.height() / 2)
            distancia = 0
        else:
            ponto = self._tela.cursor() if self._tela else None
            if ponto is None:
                return None
            distancia = 90 if passo.tipo == "seguir" else 0
        lado = -1 if ponto[0] < self.x + LADO / 2 else 1
        alvo = (ponto[0] - (LADO - bx if lado < 0 else bx) - lado * distancia, ponto[1] - by)
        alvo = self.mapa.dentro(alvo, self.mapa.indice(alvo))
        return self.mapa.caminho((self.x, self.y), alvo)[0]

    def _pegou_bola(self, passo: Passo) -> None:
        passo.extra["chutes"] = passo.extra.get("chutes", 0) + 1
        self.nec.brincar(5)
        if passo.extra["chutes"] >= self._acaso.randint(3, 5):
            self._terminar()
            return
        if passo.extra["chutes"] % 2 == 0 or passo.extra.get("sozinho"):
            self._chutar_bola()
        else:
            self._mostrar_fala(self._acaso.choice(rep.REACOES["bolinha"]), 1.2)
            self._chutar_bola()

    def _direcao_corrida(self, dx: float, dy: float) -> str:
        if abs(dy) < abs(dx) * 0.4:
            return "correndo"
        if abs(dx) < abs(dy) * 0.4:
            return "correndo-cima" if dy < 0 else "correndo-baixo"
        return "correndo-cima-lado" if dy < 0 else "correndo-baixo-lado"

    def _sentir_carinho(self, agora: float) -> None:
        if self.estado != self.ATIVO or self._tela is None or self._colo:
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
        animacao = self._anims.get(self._anim) or self._anims.get("sentado")
        if animacao is None:
            return
        quadros = animacao.esquerda if self._esquerda else animacao.direita
        self._janela.setPixmap(quadros[animacao.clipe.indice(agora - self._anim_desde)])

    # ---- para o painel ----

    def retrato(self, lado: int = 96, anim: str = "sentado", quadro: int = 0):
        """Um quadro do rato (já vestido) para o painel."""
        animacao = self._anims.get(anim) or self._anims.get("sentado")
        if animacao is None:
            return None
        pixmap = animacao.direita[quadro % len(animacao.direita)]
        return pixmap.scaled(lado, lado, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)

    def resumo(self) -> str:
        if self.estado == self.MORTO or self.nec.morto:
            return f"{self.aparencia.nome} morreu de {self.nec.causa}"
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
