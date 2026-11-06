"""Painel do rato, em pixel art: HUD com retrato, vida e atributos no topo, menu de
páginas à esquerda. Grava o arquivo de configuração (o rato e a bandeja releem) e
conversa direto com o pet para dormir, chamar, dar comida, vestir e ensinar."""

import random
import time as relogio
from datetime import date, datetime, time, timedelta

from PySide6.QtCore import QRect, Qt, QTime, QTimer
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QScrollArea,
    QStackedWidget,
    QTimeEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from alarma import acoes, aparencia, config, inicio, lembretes, necessidades, sistema, sprites
from alarma import pixelui as px
from alarma import repertorio as rep
from alarma.cerebro import DESISTIU_TXT, EVITA_TXT, GOSTA, Cerebro, caminho_padrao as caminho_cerebro
from alarma.versao import VERSAO

SONOS = [
    ("30 minutos", timedelta(minutes=30)),
    ("1 hora", timedelta(hours=1)),
    ("3 horas", timedelta(hours=3)),
    ("Até amanhã", None),
    ("Até eu acordar ele", config.SEMPRE),
]
FATOS = {
    "nome": "Seu nome", "comida": "Comida favorita", "cor": "Cor favorita", "animal": "Animal favorito",
    "musica": "Música", "time": "Time", "bebida": "Bebida", "lugar": "Lugar dos sonhos", "filme": "Filme favorito",
    "hobby": "Hobby",
}
OPINIAO = {GOSTA: "gosta 😊", EVITA_TXT: "evita 😬", DESISTIU_TXT: "parou de fazer 🙅", "neutro": "tanto faz"}
POSES = ["sentado", "andando", "acenando", "correndo", "placa", "feliz", "comendo", "triste"]
HUMOR = {
    "radiante": ("RADIANTE", "verde"), "feliz": ("FELIZ", "verde"), "ok": ("DE BOA", "queijo"),
    "chateado": ("CHATEADO", "queijo2"), "péssimo": ("PÉSSIMO", "vida"), "fraco": ("FRACO", "vida"), "morto": ("MORTO", "apagado"),
}
LARGURA_ROTULO = px.largura_pixel("FELICIDADE", 2)


# ---- pedacinhos de layout ----


def _texto(texto: str, tamanho: int = 12, tinta: str = "texto", negrito: bool = False, quebra: bool = True) -> QLabel:
    rotulo = QLabel(texto, wordWrap=quebra)
    rotulo.setFont(px.fonte_texto(tamanho, negrito))
    rotulo.setStyleSheet(f"color: {px.COR.get(tinta, tinta)};")
    return rotulo


def _linha(titulo: str, dica: str, controle: QWidget) -> QWidget:
    caixa = QWidget()
    h = QHBoxLayout(caixa)
    h.setContentsMargins(0, 2, 0, 2)
    h.setSpacing(16)
    textos = QVBoxLayout()
    textos.setSpacing(2)
    textos.addWidget(_texto(titulo, 13, "texto", True))
    if dica:
        textos.addWidget(_texto(dica, 11, "suave"))
    h.addLayout(textos, 1)
    h.addWidget(controle, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    return caixa


def _cartao(titulo: str = "", icone: str = "", estilo: str = "painel") -> tuple[px.Moldura, QVBoxLayout]:
    cartao = px.Moldura(estilo)
    corpo = QVBoxLayout(cartao)
    corpo.setContentsMargins(18, 14, 18, 16)
    corpo.setSpacing(10)
    if titulo:
        cabeca = QHBoxLayout()
        cabeca.setSpacing(8)
        if icone:
            ic = QLabel()
            ic.setPixmap(px.pixmap_icone(icone, 2))
            cabeca.addWidget(ic)
        cabeca.addWidget(px.RotuloPixel(titulo, 2, "queijo"))
        cabeca.addStretch(1)
        corpo.addLayout(cabeca)
    return cartao, corpo


def _pagina(*partes) -> QScrollArea:
    miolo = QWidget()
    corpo = QVBoxLayout(miolo)
    corpo.setContentsMargins(4, 4, 12, 12)
    corpo.setSpacing(14)
    for parte in partes:
        if isinstance(parte, QWidget):
            corpo.addWidget(parte)
        else:
            corpo.addLayout(parte)
    corpo.addStretch(1)
    rolagem = QScrollArea()
    rolagem.setWidgetResizable(True)
    rolagem.setFrameShape(QScrollArea.Shape.NoFrame)
    rolagem.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    rolagem.setWidget(miolo)
    return rolagem


def _grade_amostras(colunas: int = 8) -> QGridLayout:
    g = QGridLayout()
    g.setSpacing(6)
    g.setAlignment(Qt.AlignmentFlag.AlignLeft)
    return g


def nome_da_acao(ident: str) -> str:
    """Nome legível de uma chave de aprendizado, para a aba Aprendizado."""
    if ident.startswith("ensinada:"):
        return f"Frase sua: “{ident.split(':', 1)[1][:40]}”"
    interacao = rep.por_id().get(ident)
    if interacao is None:
        return ident
    if interacao.tipo == rep.TRAVESSURA:
        return f"Travessura: {rep.PERMISSOES.get(interacao.permissao, (ident,))[0].lower()} ({ident})"
    if interacao.tipo == rep.INFO:
        return f"Informação: {rep.CATEGORIAS[interacao.categoria].lower()} ({interacao.fonte.replace('_', ' ')})"
    if interacao.tipo == rep.BRINCADEIRA:
        return f"Brincadeira: {ident.replace('-', ' ')}"
    texto = interacao.textos[0] if interacao.textos else ident
    return f"{rep.CATEGORIAS.get(interacao.categoria, 'Fala')}: “{texto[:42]}{'…' if len(texto) > 42 else ''}”"


def _amostra_estampa(estampa: str, cor_roupa: str) -> QPixmap:
    """Um quadradinho com a estampa da roupa, para escolher."""
    img = QImage(12, 12, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    for y in range(12):
        for x in range(12):
            tom = 2 if y < 4 else 1 if y < 9 else 0
            img.setPixelColor(x, y, QColor(*aparencia.cor_da_roupa(estampa or "lisa", cor_roupa, x, y, tom)))
    return QPixmap.fromImage(img.scaled(30, 30))


# ---- o painel ----


class Painel(QWidget):
    def __init__(self, pet=None) -> None:
        super().__init__()
        self._pet = pet
        self._atual = config.Config()
        self._lembretes: list[lembretes.Lembrete] = []
        self._editando: lembretes.Lembrete | None = None
        self._visual = self._aparencia()
        self._visual_salvo = self._visual
        self._quadro = 0
        self._pose = 0
        self._previa: dict[str, sprites.Animacao] = {}
        self._retratos: dict[str, sprites.Animacao] = {}
        self.setWindowTitle("Rato-Alarme — painel do rato")
        self.setStyleSheet(px.ESTILO)
        self.setMinimumSize(980, 700)

        corpo = QVBoxLayout(self)
        corpo.setContentsMargins(14, 14, 14, 12)
        corpo.setSpacing(12)
        corpo.addWidget(self._montar_hud())

        meio = QHBoxLayout()
        meio.setSpacing(12)
        meio.addWidget(self._montar_menu())
        self._paginas = QStackedWidget()
        for construir in (
            self._pagina_inicio, self._pagina_visual, self._pagina_comportamento, self._pagina_permissoes,
            self._pagina_falas, self._pagina_lembretes, self._pagina_aprendizado, self._pagina_alarme,
        ):
            self._paginas.addWidget(construir())
        meio.addWidget(self._paginas, 1)
        corpo.addLayout(meio, 1)

        rodape = QHBoxLayout()
        rodape.addWidget(_texto(f"Rato-Alarme {VERSAO}", 11, "apagado", quebra=False))
        self._aviso = _texto("", 12, "queijo", True)
        rodape.addWidget(self._aviso, 1, Qt.AlignmentFlag.AlignRight)
        salvar = px.BotaoPixel("Salvar", "estrela", "verde")
        salvar.setDefault(True)
        salvar.clicked.connect(self.salvar)
        rodape.addWidget(salvar)
        corpo.addLayout(rodape)
        self.resize(1080, 760)

        self._relogio = QTimer(self, interval=1_000)
        self._relogio.timeout.connect(self._atualizar_estado)
        self._animacao = QTimer(self, interval=110)
        self._animacao.timeout.connect(self._animar)
        if pet is not None:
            pet.mudou.connect(self._atualizar_estado)

    def paintEvent(self, _evento) -> None:
        p = QPainter(self)
        p.fillRect(self.rect(), px.cor("fundo"))
        # um xadrezinho bem discreto no fundo, de chão de toca
        c = QColor(px.COR["fundo2"])
        passo = 24
        for y in range(0, self.height(), passo):
            for x in range((y // passo % 2) * passo, self.width(), passo * 2):
                p.fillRect(QRect(x, y, passo, passo), c)
        p.end()

    # ---- HUD ----

    def _montar_hud(self) -> QWidget:
        hud = px.Moldura("madeira")
        h = QHBoxLayout(hud)
        h.setContentsMargins(16, 14, 16, 14)
        h.setSpacing(18)

        moldura_retrato = px.Moldura("fundo")
        moldura_retrato.setFixedSize(150, 150)
        mr = QVBoxLayout(moldura_retrato)
        mr.setContentsMargins(6, 6, 6, 6)
        self._retrato = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        mr.addWidget(self._retrato)
        h.addWidget(moldura_retrato)

        identidade = QVBoxLayout()
        identidade.setSpacing(6)
        self._nome_hud = px.RotuloPixel("", 4, "texto", "madeira3")
        identidade.addWidget(self._nome_hud)
        self._sobre_hud = _texto("", 12, "madeira3", True)
        identidade.addWidget(self._sobre_hud)
        self._humor_hud = px.RotuloPixel("", 2, "verde", "madeira3")
        identidade.addWidget(self._humor_hud)
        self._estado = _texto("", 12, "texto", True)
        identidade.addWidget(self._estado)
        self._nivel = px.Barra("xp", "NÍVEL", largura_rotulo=px.largura_pixel("NÍVEL", 2))
        identidade.addWidget(self._nivel)
        identidade.addStretch(1)
        editar = px.BotaoPixel("Editar rato", "lapis")
        editar.clicked.connect(lambda: self._ir_para(1))
        identidade.addWidget(editar, 0, Qt.AlignmentFlag.AlignLeft)
        h.addLayout(identidade, 3)

        status_caixa, status = _cartao(estilo="fundo")
        self._barras = {}
        for tipo, rotulo in (("vida", "VIDA"), ("barriga", "BARRIGA"), ("diversao", "DIVERSÃO"), ("felicidade", "FELICIDADE")):
            barra = px.Barra(tipo, rotulo, largura_rotulo=LARGURA_ROTULO)
            self._barras[tipo] = barra
            status.addWidget(barra)
        h.addWidget(status_caixa, 4)

        atributos_caixa, atributos = _cartao(estilo="fundo")
        self._atributos = {}
        for chave, rotulo, tinta in (
            ("inteligencia", "INTELIGÊNCIA", "azul"), ("afeto", "AFETO", "rosa"), ("travessura", "TRAVESSURA", "queijo"),
            ("gula", "GULA", "queijo2"), ("energia", "ENERGIA", "verde"),
        ):
            pontos = px.Pontos(rotulo, tinta)
            self._atributos[chave] = pontos
            atributos.addWidget(pontos)
        h.addWidget(atributos_caixa, 4)
        return hud

    # ---- menu de páginas ----

    def _montar_menu(self) -> QWidget:
        menu = px.Moldura("painel")
        menu.setFixedWidth(210)
        v = QVBoxLayout(menu)
        v.setContentsMargins(12, 14, 12, 14)
        v.setSpacing(8)
        self._grupo_menu = QButtonGroup(self)
        self._grupo_menu.setExclusive(True)
        for i, (texto, icone) in enumerate((
            ("Início", "casa"), ("Personalizar", "chapeu"), ("Comportamento", "engrenagem"), ("Permissões", "cadeado"),
            ("Falas", "balao"), ("Lembretes", "relogio"), ("Aprendizado", "cerebro"), ("Ponto", "sino"),
        )):
            botao = px.BotaoPixel(texto, icone)
            botao.setCheckable(True)
            botao.setChecked(i == 0)
            self._grupo_menu.addButton(botao, i)
            v.addWidget(botao)
        self._grupo_menu.idClicked.connect(self._ir_para)
        v.addStretch(1)
        dica = _texto("Clique no rato: tapa.\nArraste: colo.\nMouse em cima: carinho.\nBotão direito: menu.", 10, "suave")
        v.addWidget(dica)
        return menu

    def _ir_para(self, indice: int) -> None:
        self._paginas.setCurrentIndex(indice)
        botao = self._grupo_menu.button(indice)
        if botao is not None:
            botao.setChecked(True)
        if indice == 1:
            self._montar_previa()

    # ---- páginas ----

    def _pagina_inicio(self) -> QWidget:
        self._memorial, memorial = _cartao("Descanse em paz", "caveira", "fundo")
        linha = QHBoxLayout()
        lapide = QLabel()
        lapide.setPixmap(px.pixmap_item("lapide", 96))
        linha.addWidget(lapide)
        self._texto_memorial = _texto("", 13, "texto", True)
        linha.addWidget(self._texto_memorial, 1)
        memorial.addLayout(linha)
        adotar = px.BotaoPixel("Adotar novo rato", "coracao", "verde")
        adotar.clicked.connect(self._adotar)
        memorial.addWidget(adotar, 0, Qt.AlignmentFlag.AlignLeft)

        acoes_caixa, acoes_corpo = _cartao("Cuidar do rato", "coracao")
        grade = QGridLayout()
        grade.setSpacing(8)
        self._botoes_pet = []
        for i, (texto, icone, metodo) in enumerate((
            ("Queijo", "queijo", self._dar_queijo), ("Biscoito", "comida", self._dar_biscoito), ("Maçã", "comida", self._dar_maca),
            ("Bolinha", "bola", self._brincar), ("Carinho", "coracao", self._carinho), ("Chamar", "rato", self._chamar),
            ("Mandar embora", "tchau", self._mandar_embora), ("Limpar tela", "vassoura", self._limpar_objetos),
        )):
            botao = px.BotaoPixel(texto, icone)
            botao.clicked.connect(metodo)
            grade.addWidget(botao, i // 4, i % 4)
            self._botoes_pet.append(botao)
        acoes_corpo.addLayout(grade)

        sono, sono_corpo = _cartao("Dormir", "lua")
        sono_corpo.addWidget(_texto("Se ele estiver incomodando, ponha para dormir. Dormindo, ele não apronta nada (mas os lembretes ainda tocam).", 11, "suave"))
        linha = QHBoxLayout()
        self._duracao = QComboBox()
        for texto, _ in SONOS:
            self._duracao.addItem(texto)
        self._duracao.setCurrentIndex(1)
        self._dormir = px.BotaoPixel("Pôr para dormir", "lua")
        self._dormir.clicked.connect(self._por_para_dormir)
        self._acordar = px.BotaoPixel("Acordar", "sol")
        self._acordar.clicked.connect(self._acordar_rato)
        linha.addWidget(self._duracao, 1)
        linha.addWidget(self._dormir)
        linha.addWidget(self._acordar)
        sono_corpo.addLayout(linha)
        self._dormir_visivel = px.Interruptor("Mostrar ele dormindo no canto da tela")
        sono_corpo.addWidget(self._dormir_visivel)

        geral, geral_corpo = _cartao("Geral", "engrenagem")
        self._pet_ligado = px.Interruptor()
        self._saudacao = px.Interruptor()
        self._pode_morrer = px.Interruptor()
        geral_corpo.addWidget(_linha("Pet ligado", "Desligado, só o alarme do ponto continua.", self._pet_ligado))
        geral_corpo.addWidget(_linha("Dar oi quando o computador ligar", "Ele aparece, cumprimenta e traz alguma coisa.", self._saudacao))
        geral_corpo.addWidget(_linha("Ele pode morrer", "Sem comida, diversão e carinho por muito tempo, a vida dele acaba. Desligado, ele só fica fraquinho.", self._pode_morrer))

        historia, historia_corpo = _cartao("Nossa história", "livro")
        self._historia = _texto("", 12, "texto")
        historia_corpo.addWidget(self._historia)
        return _pagina(self._memorial, acoes_caixa, sono, geral, historia)

    def _pagina_visual(self) -> QWidget:
        lado = QHBoxLayout()
        lado.setSpacing(14)

        previa_caixa, previa = _cartao("Prévia", "rato", "fundo")
        previa_caixa.setFixedWidth(300)
        self._previa_rotulo = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self._previa_rotulo.setMinimumSize(240, 240)
        previa.addWidget(self._previa_rotulo)
        poses = QHBoxLayout()
        antes = px.BotaoPixel("<")
        antes.clicked.connect(lambda: self._trocar_pose(-1))
        depois = px.BotaoPixel(">")
        depois.clicked.connect(lambda: self._trocar_pose(1))
        self._nome_pose = px.RotuloPixel("SENTADO", 2, "suave")
        poses.addWidget(antes)
        poses.addWidget(self._nome_pose, 1, Qt.AlignmentFlag.AlignCenter)
        poses.addWidget(depois)
        previa.addLayout(poses)
        botoes = QGridLayout()
        sorteio = px.BotaoPixel("Sortear", "dado")
        sorteio.clicked.connect(self._sortear_visual)
        desfazer = px.BotaoPixel("Desfazer", "volta")
        desfazer.clicked.connect(self._desfazer_visual)
        vestir = px.BotaoPixel("Vestir!", "estrela", "verde")
        vestir.clicked.connect(self._salvar_visual)
        botoes.addWidget(sorteio, 0, 0)
        botoes.addWidget(desfazer, 0, 1)
        botoes.addWidget(vestir, 1, 0, 1, 2)
        previa.addLayout(botoes)
        previa.addStretch(1)
        lado.addWidget(previa_caixa, 0, Qt.AlignmentFlag.AlignTop)

        escolhas = QVBoxLayout()
        escolhas.setSpacing(14)
        nome_caixa, nome = _cartao("Nome e jeito", "rato")
        linha_nome = QHBoxLayout()
        self._campo_nome = QLineEdit()
        self._campo_nome.setMaxLength(24)
        self._campo_nome.textEdited.connect(lambda t: self._mudar_visual(nome=t.strip() or "Rato"))
        sugerir = px.BotaoPixel("", "dado")
        sugerir.setToolTip("Sugerir um nome")
        sugerir.clicked.connect(self._sugerir_nome)
        linha_nome.addWidget(self._campo_nome, 1)
        linha_nome.addWidget(sugerir)
        nome.addLayout(linha_nome)
        self._grupo_personalidade = QButtonGroup(self)
        jeitos = QGridLayout()
        jeitos.setSpacing(6)
        self._botoes_personalidade = {}
        for i, (chave, (titulo, dica)) in enumerate(aparencia.PERSONALIDADES.items()):
            b = px.BotaoPixel(titulo)
            b.setCheckable(True)
            b.setToolTip(dica)
            b.clicked.connect(lambda _=False, c=chave: self._mudar_visual(personalidade=c))
            self._grupo_personalidade.addButton(b)
            self._botoes_personalidade[chave] = b
            jeitos.addWidget(b, i // 3, i % 3)
        nome.addLayout(jeitos)
        self._dica_personalidade = _texto("", 11, "suave")
        nome.addWidget(self._dica_personalidade)
        escolhas.addWidget(nome_caixa)

        self._amostras: dict[str, dict[str, px.Amostra]] = {}

        def secao(titulo: str, icone: str, campo: str, itens: list[tuple[str, str, QPixmap | None, str]]) -> px.Moldura:
            caixa, corpo_secao = _cartao(titulo, icone)
            grade = _grade_amostras()
            self._amostras[campo] = {}
            for i, (chave, cor_hex, imagem, dica) in enumerate(itens):
                a = px.Amostra(chave, cor_hex, imagem, dica)
                a.escolhida.connect(lambda c, f=campo: self._mudar_visual(**{f: c}))
                self._amostras[campo][chave] = a
                grade.addWidget(a, i // 9, i % 9)
            corpo_secao.addLayout(grade)
            return caixa

        escolhas.addWidget(secao("Pelo", "rato", "pelo", [(k, v[1][2], None, v[0]) for k, v in aparencia.PELOS.items()]))
        cat = aparencia.catalogo()
        self._secao_roupa = secao("Roupa", "chapeu", "roupa", [(k, "", None if not k else _amostra_estampa(k, "vermelho"), v) for k, v in aparencia.ESTAMPAS.items()])
        escolhas.addWidget(self._secao_roupa)
        escolhas.addWidget(secao("Cor da roupa", "estrela", "cor_roupa", [(k, v[1], None, v[0]) for k, v in aparencia.CORES.items()]))
        for slot, titulo, icone in (("chapeu", "Chapéu", "chapeu"), ("cabelo", "Cabelo", "lapis"), ("rosto", "Rosto", "estrela"), ("pescoco", "Pescoço", "coracao")):
            itens = [("", "", None, "Nada")] + [(k, "", px.pixmap_acessorio(k), n) for k, n in cat[slot].items()]
            escolhas.addWidget(secao(titulo, icone, slot, itens))
        escolhas.addWidget(secao("Cor do cabelo", "lapis", "cor_cabelo", [(k, v[1], None, v[0]) for k, v in aparencia.CORES.items()]))
        escolhas.addStretch(1)
        lado.addLayout(escolhas, 1)

        miolo = QWidget()
        miolo.setLayout(lado)
        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QScrollArea.Shape.NoFrame)
        rolagem.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        rolagem.setWidget(miolo)
        return rolagem

    def _pagina_comportamento(self) -> QWidget:
        self._intensidade = px.Deslizante()
        self._travessura = px.Deslizante()
        self._liberdade = px.Deslizante()
        self._dica_intensidade = _texto("", 11, "suave")
        self._dica_travessura = _texto("", 11, "suave")
        self._dica_liberdade = _texto("", 11, "suave")
        for s in (self._intensidade, self._travessura, self._liberdade):
            s.valueChanged.connect(self._explicar)

        def bloco(titulo: str, icone: str, s, dica: QLabel, esquerda: str, direita: str) -> px.Moldura:
            caixa, corpo = _cartao(titulo, icone)
            linha = QHBoxLayout()
            linha.addWidget(px.RotuloPixel(esquerda, 2, "suave"))
            linha.addWidget(s, 1)
            linha.addWidget(px.RotuloPixel(direita, 2, "suave"))
            corpo.addLayout(linha)
            corpo.addWidget(dica)
            return caixa

        return _pagina(
            bloco("Intensidade", "raio", self._intensidade, self._dica_intensidade, "CALMO", "GRUDENTO"),
            bloco("Travessura", "estrela", self._travessura, self._dica_travessura, "BONZINHO", "PESTINHA"),
            bloco("Liberdade de escolha", "cerebro", self._liberdade, self._dica_liberdade, "OBEDIENTE", "LIVRE"),
        )

    def _pagina_permissoes(self) -> QWidget:
        self._internet = px.Interruptor()
        self._falar_alto = px.Interruptor()
        geral, geral_corpo = _cartao("Rato conectado", "balao")
        geral_corpo.addWidget(_linha("Pode usar a internet", "Para notícias, clima, cotações e curiosidades. Nenhum dado seu é enviado.", self._internet))
        geral_corpo.addWidget(_linha("Pode falar em voz alta", "Lê as falas com a voz do sistema.", self._falar_alto))

        trav, trav_corpo = _cartao("Travessuras liberadas", "cadeado")
        self._permissoes: dict = {}
        possivel = {
            rep.P_FECHAR_ABA: acoes.pode_fechar_aba(),
            rep.P_MINIMIZAR: acoes.pode_minimizar(),
            rep.P_CURSOR: acoes.pode_mover_cursor(),
            rep.P_JANELAS: sistema.mexe_em_outras_janelas(),
            rep.P_EMPURRAR: acoes.pode_empurrar(),
            rep.P_VOLUME: acoes.pode_mexer_volume(),
        }
        for chave, (texto, dica) in rep.PERMISSOES.items():
            caixa = px.Interruptor()
            if not possivel.get(chave, True):
                caixa.setEnabled(False)
                dica += " (Não funciona neste sistema.)"
            self._permissoes[chave] = caixa
            trav_corpo.addWidget(_linha(texto, dica, caixa))
        aviso = _texto(
            "No Mac, na primeira travessura o sistema pede permissão de Acessibilidade e de Automação para o "
            "Rato-Alarme (Ajustes do Sistema › Privacidade e Segurança). Sem ela, ele só não consegue aprontar.",
            11, "suave",
        )
        trav_corpo.addWidget(aviso)
        return _pagina(geral, trav)

    def _pagina_falas(self) -> QWidget:
        categorias, cat_corpo = _cartao("O que ele pode dizer", "balao")
        g = QGridLayout()
        g.setSpacing(8)
        self._falas: dict = {}
        for i, (chave, texto) in enumerate(rep.CATEGORIAS.items()):
            caixa = px.Interruptor(texto)
            self._falas[chave] = caixa
            g.addWidget(caixa, i // 2, i % 2)
        cat_corpo.addLayout(g)

        clima, clima_corpo = _cartao("Clima", "sol")
        self._cidade = QLineEdit()
        self._cidade.setPlaceholderText("Em branco: descobre sozinho")
        self._cidade.setFixedWidth(240)
        clima_corpo.addWidget(_linha("Cidade da previsão", "Para o clima e os lembretes de previsão.", self._cidade))

        ensinar, ens = _cartao("Ensinar uma frase", "lapis")
        ens.addWidget(_texto("Ele repete o que você ensinar. Dê ♥ quando ele falar, para ele repetir mais.", 11, "suave"))
        linha = QHBoxLayout()
        self._frase = QLineEdit()
        self._frase.setPlaceholderText("Ex.: Bora que hoje vai dar certo!")
        self._frase.returnPressed.connect(self._ensinar)
        botao = px.BotaoPixel("Ensinar", "mais")
        botao.clicked.connect(self._ensinar)
        linha.addWidget(self._frase, 1)
        linha.addWidget(botao)
        ens.addLayout(linha)
        self._frases = QListWidget()
        self._frases.setMaximumHeight(140)
        ens.addWidget(self._frases)
        esquecer = px.BotaoPixel("Esquecer a marcada", "lixo")
        esquecer.clicked.connect(self._esquecer_frase)
        ens.addWidget(esquecer, 0, Qt.AlignmentFlag.AlignRight)

        sabe, sabe_corpo = _cartao("O que ele sabe de você", "cerebro")
        sabe_corpo.addWidget(_texto("Ele pergunta de vez em quando e usa as respostas nas falas.", 11, "suave"))
        self._fatos = QListWidget()
        self._fatos.setMaximumHeight(140)
        sabe_corpo.addWidget(self._fatos)
        apagar = px.BotaoPixel("Apagar o marcado", "lixo")
        apagar.clicked.connect(self._esquecer_fato)
        sabe_corpo.addWidget(apagar, 0, Qt.AlignmentFlag.AlignRight)
        return _pagina(categorias, clima, ensinar, sabe)

    def _pagina_lembretes(self) -> QWidget:
        lista_caixa, lista = _cartao("Lembretes", "relogio")
        lista.addWidget(_texto("No horário, o rato aparece com uma placa (mesmo dormindo, se você quiser) e o computador mostra uma notificação.", 11, "suave"))
        self._lista_lembretes = QVBoxLayout()
        self._lista_lembretes.setSpacing(8)
        lista.addLayout(self._lista_lembretes)
        novo = px.BotaoPixel("Novo lembrete", "mais", "verde")
        novo.clicked.connect(self._novo_lembrete)
        lista.addWidget(novo, 0, Qt.AlignmentFlag.AlignLeft)

        self._editor, ed = _cartao("Editar lembrete", "lapis", "fundo")
        self._hora_lembrete = QTimeEdit()
        self._hora_lembrete.setDisplayFormat("HH:mm")
        self._hora_lembrete.setWrapping(True)
        ed.addWidget(_linha("Hora", "", self._hora_lembrete))
        dias = QHBoxLayout()
        dias.setSpacing(6)
        self._dias_lembrete = []
        for i, nome in enumerate(lembretes.DIAS):
            b = px.BotaoPixel(nome)
            b.setCheckable(True)
            self._dias_lembrete.append(b)
            dias.addWidget(b)
        ed.addWidget(_texto("Dias", 13, "texto", True))
        ed.addLayout(dias)
        atalhos = QHBoxLayout()
        for texto, escolha in (("Todo dia", lembretes.TODOS_OS_DIAS), ("Dias úteis", lembretes.DIAS_UTEIS), ("Fim de semana", (5, 6))):
            b = px.BotaoPixel(texto)
            b.clicked.connect(lambda _=False, e=escolha: [d.setChecked(i in e) for i, d in enumerate(self._dias_lembrete)])
            atalhos.addWidget(b)
        atalhos.addStretch(1)
        ed.addLayout(atalhos)
        self._tipo_lembrete = QComboBox()
        for chave, (nome, _, _) in lembretes.TIPOS.items():
            self._tipo_lembrete.addItem(nome, chave)
        ed.addWidget(_linha("Aviso", "O que o rato vai dizer na placa.", self._tipo_lembrete))
        self._texto_lembrete = QLineEdit()
        self._texto_lembrete.setPlaceholderText("Texto do aviso (para 'Mensagem minha') ou um complemento")
        ed.addWidget(self._texto_lembrete)
        self._som_lembrete = px.Interruptor("Tocar um bipe")
        self._acordar_lembrete = px.Interruptor("Acordar o rato se ele estiver dormindo")
        ed.addWidget(self._som_lembrete)
        ed.addWidget(self._acordar_lembrete)
        botoes = QHBoxLayout()
        salvar = px.BotaoPixel("Guardar", "estrela", "verde")
        salvar.clicked.connect(self._guardar_lembrete)
        testar = px.BotaoPixel("Testar agora", "sino")
        testar.clicked.connect(self._testar_lembrete)
        cancelar = px.BotaoPixel("Cancelar", "nao")
        cancelar.clicked.connect(self._cancelar_lembrete)
        botoes.addWidget(salvar)
        botoes.addWidget(testar)
        botoes.addWidget(cancelar)
        botoes.addStretch(1)
        ed.addLayout(botoes)
        self._editor.hide()
        return _pagina(lista_caixa, self._editor)

    def _pagina_aprendizado(self) -> QWidget:
        caixa, corpo = _cartao("O que ele aprendeu", "cerebro")
        self._resumo_aprendizado = _texto("", 12, "texto")
        corpo.addWidget(self._resumo_aprendizado)
        corpo.addWidget(_texto(
            "Carinho, queijo e ♥ fazem ele repetir o que fez há pouco. Tapa e ✕ fazem ele evitar. "
            "Depois de muitos tapas na mesma travessura, ele para de fazer, a não ser que tenha liberdade para teimar.",
            11, "suave",
        ))
        self._aprendido = QTreeWidget()
        self._aprendido.setHeaderLabels(["Valor", "Opinião", "O quê"])
        self._aprendido.setRootIsDecorated(False)
        self._aprendido.setColumnWidth(0, 90)
        self._aprendido.setColumnWidth(1, 150)
        self._aprendido.setMinimumHeight(300)
        corpo.addWidget(self._aprendido)
        esquecer = px.BotaoPixel("Esquecer tudo", "lixo", "vermelho")
        esquecer.clicked.connect(self._esquecer_tudo)
        corpo.addWidget(esquecer, 0, Qt.AlignmentFlag.AlignLeft)
        return _pagina(caixa)

    def _pagina_alarme(self) -> QWidget:
        caixa, corpo = _cartao("Alarme do ponto", "sino")
        corpo.addWidget(_texto("Nos horários de entrada e saída, o rato do alarme aparece, toca e foge até ser pego com 3 cliques.", 11, "suave"))
        self._entrada = QTimeEdit()
        self._saida = QTimeEdit()
        for campo in (self._entrada, self._saida):
            campo.setDisplayFormat("HH:mm")
            campo.setWrapping(True)
        self._alarme = px.Interruptor()
        self._fechar = px.Interruptor()
        self._inicio = px.Interruptor()
        corpo.addWidget(_linha("Horário de entrada", "Nessa hora o rato do alarme aparece e toca.", self._entrada))
        corpo.addWidget(_linha("Horário de saída", "Nessa hora ele aparece de novo.", self._saida))
        corpo.addWidget(_linha("Alarme ligado", "Desligado, o rato do alarme não aparece. O pet continua.", self._alarme))
        if sistema.mexe_em_outras_janelas():
            corpo.addWidget(_linha("Rato pode fechar janelas", "Desligado, ele continua com as outras travessuras.", self._fechar))
        if inicio.gerenciado():
            corpo.addWidget(_linha("Iniciar com o computador", "Desligado, o rato só roda quando você abrir o programa.", self._inicio))
        return _pagina(caixa)

    # ---- abrir, preencher, atualizar ----

    def abrir(self) -> None:
        self._preencher(config.carregar(config.caminho_padrao()))
        self._visual = self._visual_salvo = self._aparencia()
        self._preencher_visual()
        self._atualizar_estado()
        self._relogio.start()
        self._animacao.start()
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, evento) -> None:
        self._relogio.stop()
        self._animacao.stop()
        super().closeEvent(evento)

    def liberar(self) -> None:
        """Solta as imagens do rato (chamado na saída do app)."""
        self._relogio.stop()
        self._animacao.stop()
        self._previa, self._retratos = {}, {}
        self._retrato.clear()
        self._previa_rotulo.clear()

    def _preencher(self, atual: config.Config) -> None:
        self._atual = atual
        self._entrada.setTime(QTime(atual.entrada.hour, atual.entrada.minute))
        self._saida.setTime(QTime(atual.saida.hour, atual.saida.minute))
        self._alarme.setChecked(atual.alarme_ligado)
        self._fechar.setChecked(atual.fechar_janela)
        self._inicio.setChecked(atual.iniciar_com_sistema)
        self._pet_ligado.setChecked(atual.pet_ligado)
        self._saudacao.setChecked(atual.saudacao_boot)
        self._pode_morrer.setChecked(atual.pode_morrer)
        self._dormir_visivel.setChecked(atual.dormir_visivel)
        self._intensidade.setValue(atual.intensidade)
        self._travessura.setValue(atual.travessura)
        self._liberdade.setValue(atual.liberdade)
        self._internet.setChecked(atual.internet)
        self._falar_alto.setChecked(atual.falar_alto)
        for chave, caixa in self._permissoes.items():
            caixa.setChecked(chave in atual.permissoes)
        for chave, caixa in self._falas.items():
            caixa.setChecked(chave in atual.falas)
        self._cidade.setText(atual.cidade)
        self._lembretes = list(atual.lembretes)
        self._listar_lembretes()
        self._explicar()
        self._aviso.clear()

    def _cerebro(self) -> Cerebro:
        return self._pet.cerebro if self._pet is not None else Cerebro(caminho_cerebro())

    def _nec(self) -> necessidades.Necessidades:
        return self._pet.nec if self._pet is not None else necessidades.carregar()

    def _aparencia(self) -> aparencia.Aparencia:
        return self._pet.aparencia if self._pet is not None else aparencia.carregar()

    def _atualizar_estado(self) -> None:
        pet = self._pet
        for botao in self._botoes_pet + [self._dormir, self._acordar]:
            botao.setEnabled(pet is not None)
        cerebro, nec, a = self._cerebro(), self._nec(), self._aparencia()
        self.setWindowTitle(f"{a.nome} — painel do rato")
        self._nome_hud.definir(a.nome.upper())
        idade = a.dias()
        jeito = aparencia.PERSONALIDADES.get(a.personalidade, ("", ""))[0]
        self._sobre_hud.setText(f"{jeito} · {idade} dia{'s' if idade != 1 else ''} com você · {nec.vidas}º rato")
        humor, tinta = HUMOR.get(nec.humor(), ("", "texto"))
        self._humor_hud.definir(f"HUMOR: {humor}", tinta)
        self._estado.setText(pet.resumo() if pet is not None else "O pet não está rodando.")
        self._nivel.definir(cerebro.progresso() * 100, f"{cerebro.nivel}")
        for campo, barra in self._barras.items():
            barra.definir(getattr(nec, campo))
        sabe = len(cerebro.fatos) + len(cerebro.frases) + len(cerebro.pesos) // 10
        valores = {
            "inteligencia": (min(5, (cerebro.nivel - 1) // 2 + sabe // 3), f"Nível {cerebro.nivel}, sabe {len(cerebro.fatos)} coisas sobre você e {len(cerebro.frases)} frases"),
            "afeto": (min(5, nec.carinhos // 8), f"{nec.carinhos} carinhos"),
            "travessura": (round(self._travessura.value() / 20), f"Travessura {self._travessura.value()}%"),
            "gula": (min(5, nec.refeicoes // 6), f"{nec.refeicoes} refeições"),
            "energia": (min(5, round((nec.barriga + nec.diversao) / 40)), "Barriga cheia e diversão em dia"),
        }
        for chave, (valor, dica) in valores.items():
            self._atributos[chave].definir(valor, dica)
        self._memorial.setVisible(nec.morto)
        if nec.morto:
            quando = nec.morreu_em.replace("T", " às ") if nec.morreu_em else ""
            self._texto_memorial.setText(f"{a.nome} morreu de {nec.causa} {quando}.\nViveu {idade} dias, comeu {nec.refeicoes} vezes e ganhou {nec.carinhos} carinhos.")
        self._historia.setText(
            f"Juntos há {idade} dias · nível {cerebro.nivel} ({cerebro.xp} xp)\n"
            f"{nec.refeicoes} refeições · {nec.brincadeiras} brincadeiras · {nec.carinhos} carinhos · {nec.tapas} tapas\n"
            f"Sabe {len(cerebro.fatos)} coisas sobre você e {len(cerebro.frases)} frases suas."
        )
        self._listar_frases(cerebro)
        self._listar_fatos(cerebro)
        self._listar_aprendido(cerebro)

    def _animar(self) -> None:
        """Retrato do HUD e prévia da personalização, quadro a quadro."""
        self._quadro += 1
        morto = self._nec().morto
        anim = "morto" if morto else ("triste" if self._nec().fraco else "sentado")
        retrato = self._quadro_de(self._retratos_atual(), anim)
        if retrato is not None:
            self._retrato.setPixmap(retrato.scaled(132, 132, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))
        if self._paginas.currentIndex() == 1:
            previa = self._quadro_de(self._previa, POSES[self._pose])
            if previa is not None:
                self._previa_rotulo.setPixmap(previa.scaled(240, 240, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation))

    def _retratos_atual(self) -> dict:
        if self._pet is not None and self._pet._anims:
            return self._pet._anims
        if not self._retratos:
            self._retratos = sprites.carregar(144, ("sentado", "triste", "morto"), montador=aparencia.Montador(self._aparencia()))
        return self._retratos

    def _quadro_de(self, anims: dict, nome: str) -> QPixmap | None:
        animacao = anims.get(nome) or anims.get("sentado")
        if animacao is None:
            return None
        passo = max(1, round(animacao.clipe.fps * 0.11))
        return animacao.direita[(self._quadro * passo) % len(animacao.direita)]

    # ---- listas ----

    def _listar_frases(self, cerebro: Cerebro) -> None:
        if [self._frases.item(i).text() for i in range(self._frases.count())] == cerebro.frases:
            return
        self._frases.clear()
        self._frases.addItems(cerebro.frases)

    def _listar_fatos(self, cerebro: Cerebro) -> None:
        linhas = [f"{FATOS.get(k, k)}: {v}" for k, v in cerebro.fatos.items()]
        if [self._fatos.item(i).text() for i in range(self._fatos.count())] == linhas:
            return
        self._fatos.clear()
        for (chave, _), linha in zip(cerebro.fatos.items(), linhas):
            item = QListWidgetItem(linha)
            item.setData(Qt.ItemDataRole.UserRole, chave)
            self._fatos.addItem(item)

    def _listar_aprendido(self, cerebro: Cerebro) -> None:
        pesos = sorted(cerebro.pesos.items(), key=lambda kv: -abs(kv[1]))
        gosta = sum(1 for k, _ in pesos if cerebro.opiniao(k) == GOSTA)
        evita = sum(1 for k, _ in pesos if cerebro.opiniao(k) in (EVITA_TXT, DESISTIU_TXT))
        self._resumo_aprendizado.setText(
            f"Ele já aprendeu sobre {len(pesos)} coisas: gosta de {gosta} e evita {evita}. "
            f"Você ensinou {len(cerebro.frases)} frases e ele sabe {len(cerebro.fatos)} coisas sobre você."
            if pesos else "Ele ainda não aprendeu nada. Dê carinho, queijo ou tapas e veja aqui o que muda."
        )
        linhas = []
        for ident, valor in pesos[:80]:
            barra = ("+" if valor > 0 else "−") + ("▮" * min(8, round(abs(valor) * 2)) or "·")
            linhas.append((barra, OPINIAO[cerebro.opiniao(ident)], nome_da_acao(ident)))
        atuais = [tuple(self._aprendido.topLevelItem(i).text(c) for c in range(3)) for i in range(self._aprendido.topLevelItemCount())]
        if atuais != linhas:
            self._aprendido.clear()
            self._aprendido.addTopLevelItems([QTreeWidgetItem(list(linha)) for linha in linhas])

    def _explicar(self) -> None:
        i = self._intensidade.value()
        minutos = round((60 + 3900 * (1 - i / 100) ** 2) / 60)
        self._dica_intensidade.setText(
            f"Aparece mais ou menos a cada {minutos} minuto{'s' if minutos != 1 else ''} e fica um pouco"
            f"{' mais' if i > 60 else ''} na tela. Quanto mais alto, mais vezes ele vem e mais coisas faz em cada visita."
        )
        t = self._travessura.value()
        chance = round((0.04 + 0.56 * t / 100) * 100)
        self._dica_travessura.setText(
            f"Cerca de {chance}% do que ele faz são travessuras: fechar abas, mexer no cursor, empurrar janelas, largar coisas na tela... "
            "Só as liberadas em Permissões."
        )
        lib = self._liberdade.value()
        self._dica_liberdade.setText(
            "Segue à risca o que aprendeu com carinho e tapas." if lib < 25 else
            "Segue o que aprendeu, mas às vezes muda de ideia." if lib < 65 else
            "Faz o que quer. Às vezes repete até o que você já ensinou que não gosta."
        )

    # ---- ações do rato ----

    def _no_pet(self, metodo: str, *args) -> None:
        if self._pet is not None:
            getattr(self._pet, metodo)(*args)
            self._atualizar_estado()

    def _chamar(self) -> None:
        self._no_pet("chamar")

    def _dar_queijo(self) -> None:
        self._no_pet("dar_comida", "queijo")

    def _dar_biscoito(self) -> None:
        self._no_pet("dar_comida", "biscoito")

    def _dar_maca(self) -> None:
        self._no_pet("dar_comida", "maca")

    def _brincar(self) -> None:
        self._no_pet("brincar_bolinha")

    def _carinho(self) -> None:
        if self._pet is not None and self._pet.estado != self._pet.ATIVO:
            self._pet.chamar()
        self._no_pet("fazer_carinho")

    def _mandar_embora(self) -> None:
        self._no_pet("mandar_embora")

    def _limpar_objetos(self) -> None:
        self._no_pet("limpar_objetos")

    def _por_para_dormir(self) -> None:
        if self._pet is None:
            return
        _, duracao = SONOS[self._duracao.currentIndex()]
        agora = datetime.now()
        if duracao == config.SEMPRE:
            ate = config.SEMPRE
        elif duracao is None:
            ate = (agora + timedelta(days=1)).replace(hour=7, minute=0, second=0).isoformat(timespec="minutes")
        else:
            ate = (agora + duracao).isoformat(timespec="minutes")
        self._pet.cfg = self._pet.cfg.com(dormir_visivel=self._dormir_visivel.isChecked())
        self._pet.dormir(ate)
        self._atual = self._atual.com(dormir_ate=ate, dormir_visivel=self._dormir_visivel.isChecked())
        self._aviso.setText("Boa noite, rato.")
        self._atualizar_estado()

    def _acordar_rato(self) -> None:
        if self._pet is not None:
            self._pet.acordar()
            self._atual = self._atual.com(dormir_ate="")
            self._aviso.setText("Ele acordou.")
            self._atualizar_estado()

    def _adotar(self) -> None:
        if self._pet is not None:
            self._pet.adotar()
        else:
            nec = necessidades.carregar()
            nec.adotar(relogio.time())
            necessidades.salvar(nec)
            Cerebro(caminho_cerebro()).esquecer_tudo()
            aparencia.salvar(self._aparencia().com(adotado_em=date.today().isoformat()))
        self._aviso.setText("Bem-vindo, rato novo!")
        self._atualizar_estado()

    # ---- personalização ----

    def _preencher_visual(self) -> None:
        a = self._visual
        if self._campo_nome.text() != a.nome:
            self._campo_nome.setText(a.nome)
        for chave, botao in self._botoes_personalidade.items():
            botao.setChecked(chave == a.personalidade)
        self._dica_personalidade.setText(aparencia.PERSONALIDADES.get(a.personalidade, ("", ""))[1])
        for campo, amostras in self._amostras.items():
            valor = getattr(a, campo)
            for chave, amostra in amostras.items():
                amostra.setChecked(chave == valor)
        for chave, amostra in self._amostras.get("roupa", {}).items():
            if chave:
                amostra._imagem = _amostra_estampa(chave, a.cor_roupa)
                amostra.update()

    def _mudar_visual(self, **mudancas) -> None:
        visual_antes = self._visual.chave()
        self._visual = aparencia.validar(self._visual.com(**mudancas))
        self._preencher_visual()
        if self._visual.chave() != visual_antes:
            self._montar_previa()
        self._aviso.setText("Clique em Vestir! para o rato usar isso.")

    def _montar_previa(self) -> None:
        nomes = tuple(dict.fromkeys([POSES[self._pose], "sentado"]))
        self._previa = sprites.carregar(144, nomes, montador=aparencia.Montador(self._visual))

    def _trocar_pose(self, passo: int) -> None:
        self._pose = (self._pose + passo) % len(POSES)
        self._nome_pose.definir(POSES[self._pose].upper())
        self._montar_previa()

    def _sortear_visual(self) -> None:
        acaso = random.Random()
        cat = aparencia.catalogo()
        escolha = lambda opcoes, nada=0.35: "" if acaso.random() < nada else acaso.choice(list(opcoes))  # noqa: E731
        self._mudar_visual(
            pelo=acaso.choice(list(aparencia.PELOS)),
            cabelo=escolha(cat["cabelo"], 0.5),
            cor_cabelo=acaso.choice(list(aparencia.CORES)),
            chapeu=escolha(cat["chapeu"], 0.4),
            rosto=escolha(cat["rosto"], 0.6),
            pescoco=escolha(cat["pescoco"], 0.5),
            roupa=escolha([k for k in aparencia.ESTAMPAS if k], 0.3),
            cor_roupa=acaso.choice(list(aparencia.CORES)),
        )

    def _sugerir_nome(self) -> None:
        nome = random.choice([n for n in aparencia.NOMES_SUGERIDOS if n != self._visual.nome])
        self._campo_nome.setText(nome)
        self._mudar_visual(nome=nome)

    def _desfazer_visual(self) -> None:
        self._visual = self._visual_salvo
        self._preencher_visual()
        self._montar_previa()

    def _salvar_visual(self) -> None:
        if self._pet is not None:
            self._pet.vestir(self._visual)
        else:
            aparencia.salvar(self._visual)
            self._retratos = {}
        self._visual_salvo = self._visual
        self._aviso.setText(f"{self._visual.nome} está de visual novo!")
        self._atualizar_estado()

    # ---- lembretes ----

    def _listar_lembretes(self) -> None:
        while self._lista_lembretes.count():
            item = self._lista_lembretes.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        if not self._lembretes:
            self._lista_lembretes.addWidget(_texto("Nenhum lembrete ainda. Que tal um para beber água?", 12, "suave"))
            return
        for l in sorted(self._lembretes, key=lambda x: x.hora):
            cartao = px.Moldura("botao" if l.ativo else "fundo")
            h = QHBoxLayout(cartao)
            h.setContentsMargins(14, 10, 14, 10)
            h.setSpacing(12)
            h.addWidget(px.RotuloPixel(l.hora.strftime("%H:%M"), 3, "queijo" if l.ativo else "apagado"))
            textos = QVBoxLayout()
            textos.setSpacing(2)
            textos.addWidget(_texto(l.texto if l.tipo == "mensagem" and l.texto else l.nome_tipo, 13, "texto", True))
            textos.addWidget(_texto(l.resumo().split(" · ", 2)[1], 11, "suave"))
            h.addLayout(textos, 1)
            ativo = px.Interruptor()
            ativo.setChecked(l.ativo)
            ativo.setToolTip("Ligado ou desligado")
            ativo.toggled.connect(lambda ligado, ident=l.id: self._ligar_lembrete(ident, ligado))
            h.addWidget(ativo)
            editar = px.BotaoPixel("", "lapis")
            editar.setToolTip("Editar")
            editar.clicked.connect(lambda _=False, ident=l.id: self._editar_lembrete(ident))
            apagar = px.BotaoPixel("", "lixo")
            apagar.setToolTip("Apagar")
            apagar.clicked.connect(lambda _=False, ident=l.id: self._apagar_lembrete(ident))
            h.addWidget(editar)
            h.addWidget(apagar)
            self._lista_lembretes.addWidget(cartao)

    def _novo_lembrete(self) -> None:
        agora = datetime.now() + timedelta(minutes=5)
        self._abrir_editor(lembretes.Lembrete(lembretes.novo_id(), time(agora.hour, agora.minute), "agua"))

    def _editar_lembrete(self, ident: str) -> None:
        l = next((x for x in self._lembretes if x.id == ident), None)
        if l is not None:
            self._abrir_editor(l)

    def _abrir_editor(self, l: lembretes.Lembrete) -> None:
        self._editando = l
        self._hora_lembrete.setTime(QTime(l.hora.hour, l.hora.minute))
        for i, b in enumerate(self._dias_lembrete):
            b.setChecked(i in l.dias)
        self._tipo_lembrete.setCurrentIndex(max(0, self._tipo_lembrete.findData(l.tipo)))
        self._texto_lembrete.setText(l.texto)
        self._som_lembrete.setChecked(l.som)
        self._acordar_lembrete.setChecked(l.acordar)
        self._editor.show()

    def _lembrete_do_editor(self) -> lembretes.Lembrete | None:
        if self._editando is None:
            return None
        hora = self._hora_lembrete.time()
        return self._editando.com(
            hora=time(hora.hour(), hora.minute()),
            dias=tuple(i for i, b in enumerate(self._dias_lembrete) if b.isChecked()),
            tipo=self._tipo_lembrete.currentData(),
            texto=self._texto_lembrete.text().strip()[:200],
            som=self._som_lembrete.isChecked(),
            acordar=self._acordar_lembrete.isChecked(),
        )

    def _guardar_lembrete(self) -> None:
        novo = self._lembrete_do_editor()
        if novo is None:
            return
        if not novo.dias:
            self._aviso.setText("Escolha pelo menos um dia.")
            return
        if novo.tipo == "mensagem" and not novo.texto:
            self._aviso.setText("Escreva o texto do aviso.")
            return
        self._lembretes = [l for l in self._lembretes if l.id != novo.id] + [novo]
        self._gravar_lembretes()
        self._cancelar_lembrete()
        self._aviso.setText(f"Lembrete das {novo.hora:%H:%M} guardado.")

    def _testar_lembrete(self) -> None:
        l = self._lembrete_do_editor()
        if l is not None and self._pet is not None:
            self._pet.tocar_lembrete(l)

    def _cancelar_lembrete(self) -> None:
        self._editando = None
        self._editor.hide()

    def _ligar_lembrete(self, ident: str, ligado: bool) -> None:
        self._lembretes = [l.com(ativo=ligado) if l.id == ident else l for l in self._lembretes]
        self._gravar_lembretes()

    def _apagar_lembrete(self, ident: str) -> None:
        self._lembretes = [l for l in self._lembretes if l.id != ident]
        self._gravar_lembretes()

    def _gravar_lembretes(self) -> None:
        """Lembretes valem na hora, sem precisar do Salvar: o resto do config fica como está no disco."""
        atual = config.carregar(config.caminho_padrao()).com(lembretes=tuple(self._lembretes))
        try:
            config.salvar(config.caminho_padrao(), atual)
        except (OSError, ValueError):
            self._aviso.setText("Não consegui salvar o lembrete.")
            return
        self._atual = self._atual.com(lembretes=tuple(self._lembretes))
        if self._pet is not None:
            self._pet.cfg = self._pet.cfg.com(lembretes=tuple(self._lembretes))
        QTimer.singleShot(0, self._listar_lembretes)

    # ---- frases, fatos e esquecimento ----

    def _ensinar(self) -> None:
        cerebro = self._cerebro()
        if cerebro.ensinar(self._frase.text()):
            cerebro.salvar()
            self._frase.clear()
            self._aviso.setText("Ele aprendeu a frase.")
        self._atualizar_estado()

    def _esquecer_frase(self) -> None:
        item = self._frases.currentItem()
        if item is None:
            return
        cerebro = self._cerebro()
        cerebro.esquecer_frase(item.text())
        cerebro.salvar()
        self._atualizar_estado()

    def _esquecer_fato(self) -> None:
        item = self._fatos.currentItem()
        if item is None:
            return
        cerebro = self._cerebro()
        cerebro.fatos.pop(item.data(Qt.ItemDataRole.UserRole), None)
        cerebro.salvar()
        self._atualizar_estado()

    def _esquecer_tudo(self) -> None:
        resposta = QMessageBox.question(
            self,
            "Esquecer tudo?",
            "O rato esquece o que aprendeu, as frases que você ensinou e o que sabe de você. Não dá para desfazer.",
        )
        if resposta != QMessageBox.StandardButton.Yes:
            return
        if self._pet is not None:
            self._pet.esquecer()
        else:
            self._cerebro().esquecer_tudo()
        self._aviso.setText("Ele esqueceu tudo.")
        self._atualizar_estado()

    # ---- salvar ----

    def salvar(self) -> None:
        entrada, saida = self._entrada.time(), self._saida.time()
        # o sono pode ter mudado pelo menu do rato enquanto o painel estava aberto
        disco = config.carregar(config.caminho_padrao())
        novo = config.Config(
            time(entrada.hour(), entrada.minute()),
            time(saida.hour(), saida.minute()),
            self._alarme.isChecked(),
            self._fechar.isChecked(),
            self._inicio.isChecked(),
            pet_ligado=self._pet_ligado.isChecked(),
            intensidade=self._intensidade.value(),
            travessura=self._travessura.value(),
            liberdade=self._liberdade.value(),
            saudacao_boot=self._saudacao.isChecked(),
            internet=self._internet.isChecked(),
            falar_alto=self._falar_alto.isChecked(),
            cidade=self._cidade.text().strip(),
            dormir_ate=self._pet.cfg.dormir_ate if self._pet is not None else disco.dormir_ate,
            dormir_visivel=self._dormir_visivel.isChecked(),
            permissoes=tuple(k for k, c in self._permissoes.items() if c.isChecked()),
            falas=tuple(k for k, c in self._falas.items() if c.isChecked()),
            pode_morrer=self._pode_morrer.isChecked(),
            lembretes=tuple(self._lembretes),
        )
        try:
            config.salvar(config.caminho_padrao(), novo)
        except ValueError:
            self._aviso.setText("A entrada precisa ser antes da saída.")
        except OSError:
            self._aviso.setText("Não consegui salvar a configuração.")
        else:
            inicio.aplicar(novo.iniciar_com_sistema)
            self._atual = novo
            if self._pet is not None:
                self._pet.cfg = novo
            self._aviso.setText("Salvo.")
