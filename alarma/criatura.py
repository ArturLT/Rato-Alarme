"""O rato do alarme: sai da gaiola, foge do cursor e volta para ela quando é pego."""

import os
import random
import sys
import time

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, GLib, Gtk

from alarma import config, hypr, sprites, travessuras
from alarma.animacao import CORRENDO, CORRIDA, DUR_ACERTO, depois_de_pego, escolher
from alarma.caca import FECHAR, JANELAS, LADO_RATO, MUDO, NOTAS, YOUTUBE, Caca, Fase
from alarma.logica import Alarme, Decisao, decidir, pendente
from alarma.registro import DISPARADO, PEGO, Registro, caminho_mudo, caminho_padrao
from alarma.som import tocar

from datetime import datetime

APP_ID = "meme.alarma"
TITULO = "alarma"
TITULO_NOTAS = "bloco do rato"
REAVALIAR_S = 2
PASSO_MS = 100
LETRA_MS = 70
QUADRO_MS = 50
AREA_RESERVA = (0, 0, 1920, 1080)

_CSS = "window.mascote { background: transparent; }"


class Criatura(Gtk.Application):
    def __init__(self, demo: bool = False) -> None:
        super().__init__(application_id=APP_ID)
        self._demo = demo
        self._registro = Registro(None if demo else caminho_padrao())
        self._acaso = random.Random()
        self._config = self._ler_config()
        self.decisao = self._decidir()
        self._caca: Caca | None = None
        self._janela: Gtk.ApplicationWindow | None = None
        self._imagem: Gtk.Picture | None = None
        self._animacoes: dict[str, sprites.Animacao] = {}
        self._nome_atual = ""
        self._inicio_clipe = 0.0
        self._acerto_ate = 0.0
        self._capturado_em: float | None = None
        self._oculto = True
        self._endereco: str | None = None
        self._area = AREA_RESERVA
        self._notas: Gtk.Window | None = None
        self._marca_mudo = caminho_mudo()

    def _ler_config(self) -> config.Config:
        return config.Config() if self._demo else config.carregar(config.caminho_padrao())

    def _decidir(self) -> Decisao:
        agora = datetime.now().astimezone()
        if self._demo:
            return Decisao(Alarme.MANHA, True, agora)
        return decidir(agora, self._config.entrada, self._config.saida)

    @property
    def _dia(self) -> str:
        return self.decisao.agora.date().isoformat()

    def do_activate(self) -> None:
        if self._janela is not None:
            if not self._oculto:
                self._janela.present()
            return

        travessuras.restaurar_som(self._marca_mudo)

        css = Gtk.CssProvider()
        css.load_from_string(_CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        janela = Gtk.ApplicationWindow(application=self, title=TITULO)
        janela.set_decorated(False)
        janela.set_resizable(False)
        janela.set_default_size(LADO_RATO, LADO_RATO)
        janela.connect("close-request", self._recusar_fechar)

        clique = Gtk.GestureClick()
        clique.connect("pressed", self._clicado)
        janela.add_controller(clique)

        imagem = Gtk.Picture()
        imagem.set_size_request(LADO_RATO, LADO_RATO)
        janela.set_child(imagem)
        janela.set_css_classes(["mascote"])

        self._janela = janela
        self._imagem = imagem
        self._animacoes = sprites.carregar(LADO_RATO)
        self._sincronizar()
        self._quadro()
        if not self._oculto:
            janela.present()

        GLib.timeout_add(QUADRO_MS, self._quadro)
        GLib.timeout_add(700, self._bip_inicial)
        GLib.timeout_add(PASSO_MS, self._passo)
        GLib.timeout_add_seconds(4, self._bip)
        GLib.timeout_add_seconds(REAVALIAR_S, self._reavaliar)

    def _recusar_fechar(self, *_args: object) -> bool:
        return True

    def _sincronizar(self) -> None:
        self._config = self._ler_config()
        self.decisao = self._decidir()
        alarme = self.decisao.alarme
        pego = self._registro.tem(self._dia, alarme, PEGO)
        disparado = self._registro.tem(self._dia, alarme, DISPARADO)
        solto = pendente(self.decisao, self._config.alarme_ligado, pego, disparado)
        if solto and self._caca is None:
            if not disparado:
                self._registro.marcar(self._dia, alarme, DISPARADO)
            feito = self._registro.tem(self._dia, alarme, YOUTUBE)
            self._caca = Caca(self._acaso, time.monotonic(), youtube_feito=feito)
            self._mostrar()
        elif not solto:
            self._encerrar()
        if not self._config.alarme_ligado:
            self._capturado_em = None
        if not solto and not self._oculto and self._capturado_em is None:
            self._esconder()

    def _encerrar(self) -> None:
        self._caca = None
        travessuras.restaurar_som(self._marca_mudo)
        if self._notas is not None:
            self._notas.destroy()
            self._notas = None

    def _mostrar(self) -> None:
        self._capturado_em = None
        if self._oculto and self._janela is not None:
            self._oculto = False
            self._endereco = None
            self._janela.present()

    def _esconder(self) -> None:
        """Some da tela até o próximo alarme. O processo continua vivo."""
        self._oculto = True
        self._endereco = None
        if self._janela is not None:
            self._janela.set_visible(False)

    def _quadro(self) -> bool:
        if self._imagem is None or self._oculto:
            return True
        agora = time.monotonic()
        caca = self._caca
        depois = None
        if self._capturado_em is not None:
            depois = depois_de_pego(agora - self._capturado_em)
            if depois is None:
                self._capturado_em = None
                self._esconder()
                return True
        nome = escolher(
            caca.fase if caca else None,
            caca.cansado(agora) if caca else False,
            agora < self._acerto_ate,
            depois,
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
        self._imagem.set_paintable(quadros[indice])
        return True

    def _clicado(self, *_args: object) -> None:
        agora = time.monotonic()
        if self._caca is None:
            return
        if not self._caca.clique(agora):
            self._acerto_ate = agora + DUR_ACERTO
            self._nome_atual = ""
            return
        self._capturado_em = agora
        self._registro.marcar(self._dia, self.decisao.alarme, PEGO)
        self._encerrar()

    def _bip(self) -> bool:
        if self._caca is not None:
            tocar(self.decisao.alarme)
        return True

    def _bip_inicial(self) -> bool:
        self._bip()
        return False

    def _reavaliar(self) -> bool:
        self._sincronizar()
        return True

    def _passo(self) -> bool:
        if self._oculto:
            return True
        if self._endereco is None:
            self._endereco = hypr.endereco(os.getpid(), TITULO)
            if self._endereco is None:
                return True
            hypr.preparar(self._endereco)
        if self._caca is None:
            return True

        agora = time.monotonic()
        cursor = hypr.cursor()
        self._area = hypr.area_do_cursor(cursor) or self._area
        posicao = self._caca.passo(agora, cursor, self._area)
        if posicao is not None:
            hypr.mover(self._endereco, *posicao)

        proibidas = () if self._config.fechar_janela else (FECHAR,)
        travessura = self._caca.travessura(agora, proibidas)
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
        return True

    def _abrir_notas(self) -> None:
        if self._notas is not None:
            return
        notas = Gtk.Window(application=self, title=TITULO_NOTAS)
        notas.set_default_size(420, 300)
        notas.connect("destroy", self._notas_fechadas)
        texto = Gtk.TextView(editable=False, cursor_visible=False)
        texto.set_wrap_mode(Gtk.WrapMode.WORD)
        notas.set_child(texto)
        self._notas = notas
        notas.present()
        GLib.timeout_add(LETRA_MS, self._escrever, notas, texto, iter(travessuras.TEXTO_NOTAS))

    def _notas_fechadas(self, notas: Gtk.Window) -> None:
        if self._notas is notas:
            self._notas = None

    def _escrever(self, notas: Gtk.Window, texto: Gtk.TextView, letras) -> bool:
        letra = next(letras, None)
        if letra is None or self._notas is not notas:
            return False
        buffer = texto.get_buffer()
        buffer.insert(buffer.get_end_iter(), letra)
        return True


def main() -> int:
    return Criatura(demo="--demo" in sys.argv).run(None)
