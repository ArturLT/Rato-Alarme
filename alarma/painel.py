"""Painel de controle. Grava o arquivo de configuração (o rato e a bandeja releem) e
conversa direto com o pet para dormir, chamar, dar queijo e ensinar frases."""

import time as relogio
from datetime import datetime, time, timedelta

from PySide6.QtCore import Qt, QTime, QTimer
from PySide6.QtGui import QPalette
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSlider,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from alarma import acoes, config, inicio, sistema
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


def _campo_hora() -> QTimeEdit:
    campo = QTimeEdit()
    campo.setDisplayFormat("HH:mm")
    campo.setWrapping(True)
    return campo


def _discreto(rotulo: QLabel) -> QLabel:
    rotulo.setForegroundRole(QPalette.ColorRole.PlaceholderText)
    return rotulo


def _rotulo(texto: str, dica: str) -> QWidget:
    caixa = QWidget()
    colunas = QVBoxLayout(caixa)
    colunas.setContentsMargins(0, 0, 0, 0)
    colunas.setSpacing(2)
    colunas.addWidget(QLabel(texto))
    colunas.addWidget(_discreto(QLabel(dica, wordWrap=True)))
    return caixa


def _grade(linhas: list[tuple[str, str, QWidget]]) -> QGridLayout:
    grade = QGridLayout()
    grade.setVerticalSpacing(14)
    grade.setHorizontalSpacing(20)
    grade.setColumnStretch(0, 1)
    for linha, (texto, dica, controle) in enumerate(linhas):
        grade.addWidget(_rotulo(texto, dica), linha, 0)
        grade.addWidget(controle, linha, 1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    return grade


def _pagina(*partes) -> QWidget:
    """Uma aba com rolagem, para caber em telas pequenas."""
    miolo = QWidget()
    corpo = QVBoxLayout(miolo)
    corpo.setContentsMargins(16, 16, 16, 16)
    corpo.setSpacing(16)
    for parte in partes:
        if isinstance(parte, QWidget):
            corpo.addWidget(parte)
        else:
            corpo.addLayout(parte)
    corpo.addStretch(1)
    rolagem = QScrollArea()
    rolagem.setWidgetResizable(True)
    rolagem.setFrameShape(QScrollArea.Shape.NoFrame)
    rolagem.setWidget(miolo)
    return rolagem


def _barra(maximo: int = 100) -> QProgressBar:
    barra = QProgressBar()
    barra.setRange(0, maximo)
    barra.setTextVisible(True)
    barra.setFixedWidth(190)
    return barra


def _deslizante() -> QSlider:
    s = QSlider(Qt.Orientation.Horizontal)
    s.setRange(0, 100)
    s.setSingleStep(5)
    s.setPageStep(10)
    s.setFixedWidth(190)
    return s


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


class Painel(QWidget):
    def __init__(self, pet=None) -> None:
        super().__init__()
        self._pet = pet
        self.setWindowTitle("Rato-Alarme — painel do rato")
        self._atual = config.Config()

        abas = QTabWidget()
        abas.setDocumentMode(True)
        abas.addTab(self._aba_rato(), "🐭 Rato")
        abas.addTab(self._aba_comportamento(), "🎚 Comportamento")
        abas.addTab(self._aba_permissoes(), "🔓 Permissões")
        abas.addTab(self._aba_falas(), "💬 Falas")
        abas.addTab(self._aba_aprendizado(), "🧠 Aprendizado")
        abas.addTab(self._aba_alarme(), "⏰ Alarme")
        self._abas = abas

        self._aviso = QLabel(wordWrap=True)
        salvar = QPushButton("Salvar")
        salvar.setDefault(True)
        salvar.clicked.connect(self.salvar)
        rodape = QHBoxLayout()
        rodape.setContentsMargins(16, 0, 16, 0)
        rodape.addWidget(_discreto(QLabel(f"Versão {VERSAO}")))
        rodape.addWidget(self._aviso, 1)
        rodape.addWidget(salvar)

        corpo = QVBoxLayout(self)
        corpo.setContentsMargins(0, 8, 0, 16)
        corpo.setSpacing(12)
        corpo.addWidget(abas, 1)
        corpo.addLayout(rodape)
        self.resize(600, 640)

        self._relogio = QTimer(self, interval=2_000)
        self._relogio.timeout.connect(self._atualizar_estado)
        if pet is not None:
            pet.mudou.connect(self._atualizar_estado)

    # ---- abas ----

    def _aba_rato(self) -> QWidget:
        self._estado = QLabel(wordWrap=True)
        fonte = self._estado.font()
        fonte.setPointSize(fonte.pointSize() + 3)
        fonte.setBold(True)
        self._estado.setFont(fonte)
        self._nivel = _barra()
        self._humor = _barra()

        acoes_rato = QGridLayout()
        acoes_rato.setSpacing(8)
        self._botoes_pet = []
        # métodos de verdade, sem lambda: lambda que guarda o painel impede o Qt de destruí-lo na hora certa
        for i, (texto, metodo) in enumerate((
            ("Chamar o rato agora", self._chamar),
            ("🧀 Dar queijo", self._dar_queijo),
            ("Mandar embora por agora", self._mandar_embora),
            ("Tirar as coisas da tela", self._limpar_objetos),
        )):
            botao = QPushButton(texto)
            botao.clicked.connect(metodo)
            acoes_rato.addWidget(botao, i // 2, i % 2)
            self._botoes_pet.append(botao)

        sono = QGroupBox("Dormir")
        self._duracao = QComboBox()
        for texto, _ in SONOS:
            self._duracao.addItem(texto)
        self._duracao.setCurrentIndex(1)
        self._dormir = QPushButton("💤 Pôr para dormir")
        self._dormir.clicked.connect(self._por_para_dormir)
        self._acordar = QPushButton("Acordar")
        self._acordar.clicked.connect(self._acordar_rato)
        self._dormir_visivel = QCheckBox("Mostrar ele dormindo no canto da tela")
        linha = QHBoxLayout()
        linha.addWidget(self._duracao, 1)
        linha.addWidget(self._dormir)
        linha.addWidget(self._acordar)
        dentro = QVBoxLayout(sono)
        dentro.addWidget(_discreto(QLabel("Se ele estiver incomodando, ponha para dormir. Dormindo, ele não apronta nada.", wordWrap=True)))
        dentro.addLayout(linha)
        dentro.addWidget(self._dormir_visivel)

        self._pet_ligado = QCheckBox()
        self._saudacao = QCheckBox()
        geral = _grade([
            ("Pet ligado", "Desligado, só o alarme do ponto continua.", self._pet_ligado),
            ("Dar oi quando o computador ligar", "Ele aparece, cumprimenta e traz alguma coisa.", self._saudacao),
            ("Nível", "Sobe com carinho e queijo. A cada nível ele aprende uma fala nova.", self._nivel),
            ("Humor", "Carinho e queijo alegram, tapa entristece.", self._humor),
        ])
        dica = _discreto(QLabel(
            "Clique no rato para dar um tapa: três tapas seguidos expulsam ele. "
            "Passe o mouse em cima dele, indo e voltando, para fazer carinho. "
            "Botão direito nele abre mais opções.",
            wordWrap=True,
        ))
        return _pagina(self._estado, acoes_rato, sono, geral, dica)

    def _aba_comportamento(self) -> QWidget:
        self._intensidade = _deslizante()
        self._travessura = _deslizante()
        self._liberdade = _deslizante()
        self._dica_intensidade = _discreto(QLabel(wordWrap=True))
        self._dica_travessura = _discreto(QLabel(wordWrap=True))
        self._dica_liberdade = _discreto(QLabel(wordWrap=True))
        for s in (self._intensidade, self._travessura, self._liberdade):
            s.valueChanged.connect(self._explicar)

        def bloco(titulo: str, s: QSlider, dica: QLabel, esquerda: str, direita: str) -> QGroupBox:
            caixa = QGroupBox(titulo)
            g = QGridLayout(caixa)
            g.addWidget(_discreto(QLabel(esquerda)), 0, 0)
            g.addWidget(s, 0, 1)
            g.addWidget(_discreto(QLabel(direita)), 0, 2)
            g.addWidget(dica, 1, 0, 1, 3)
            return caixa

        return _pagina(
            bloco("Intensidade das interações", self._intensidade, self._dica_intensidade, "Calmo", "Grudento"),
            bloco("Travessura", self._travessura, self._dica_travessura, "Bonzinho", "Pestinha"),
            bloco("Liberdade de escolha", self._liberdade, self._dica_liberdade, "Obediente", "Livre"),
        )

    def _aba_permissoes(self) -> QWidget:
        self._internet = QCheckBox()
        self._falar_alto = QCheckBox()
        self._permissoes: dict[str, QCheckBox] = {}
        linhas = [
            ("Pode usar a internet", "Para notícias, clima, cotações e curiosidades. Nenhum dado seu é enviado.", self._internet),
            ("Pode falar em voz alta", "Lê as falas com a voz do sistema.", self._falar_alto),
        ]
        possivel = {
            rep.P_FECHAR_ABA: acoes.pode_fechar_aba(),
            rep.P_MINIMIZAR: acoes.pode_minimizar(),
            rep.P_CURSOR: acoes.pode_mover_cursor(),
            rep.P_JANELAS: sistema.mexe_em_outras_janelas(),
        }
        for chave, (texto, dica) in rep.PERMISSOES.items():
            caixa = QCheckBox()
            if not possivel.get(chave, True):
                caixa.setEnabled(False)
                dica += " (Não funciona neste sistema.)"
            self._permissoes[chave] = caixa
            linhas.append((texto, dica, caixa))
        aviso = _discreto(QLabel(
            "No Mac, na primeira travessura o sistema pede permissão de Acessibilidade e de Automação "
            "para o Rato-Alarme. Sem ela, ele só não consegue aprontar.",
            wordWrap=True,
        ))
        return _pagina(_grade(linhas), aviso)

    def _aba_falas(self) -> QWidget:
        categorias = QGroupBox("O que ele pode dizer")
        g = QGridLayout(categorias)
        self._falas: dict[str, QCheckBox] = {}
        for i, (chave, texto) in enumerate(rep.CATEGORIAS.items()):
            caixa = QCheckBox(texto)
            self._falas[chave] = caixa
            g.addWidget(caixa, i // 2, i % 2)

        self._cidade = QLineEdit()
        self._cidade.setPlaceholderText("Em branco: descobre sozinho")
        self._cidade.setFixedWidth(200)
        cidade = _grade([("Cidade do clima", "Para a previsão do tempo.", self._cidade)])

        ensinar = QGroupBox("Ensinar uma frase")
        self._frase = QLineEdit()
        self._frase.setPlaceholderText("Ex.: Bora que hoje vai dar certo!")
        self._frase.returnPressed.connect(self._ensinar)
        botao = QPushButton("Ensinar")
        botao.clicked.connect(self._ensinar)
        self._frases = QListWidget()
        self._frases.setMaximumHeight(130)
        esquecer = QPushButton("Esquecer a frase marcada")
        esquecer.clicked.connect(self._esquecer_frase)
        linha = QHBoxLayout()
        linha.addWidget(self._frase, 1)
        linha.addWidget(botao)
        e = QVBoxLayout(ensinar)
        e.addWidget(_discreto(QLabel("Ele repete o que você ensinar. Dê ♥ quando ele falar para ele repetir mais.", wordWrap=True)))
        e.addLayout(linha)
        e.addWidget(self._frases)
        e.addWidget(esquecer, 0, Qt.AlignmentFlag.AlignRight)

        sabe = QGroupBox("O que ele sabe de você")
        self._fatos = QListWidget()
        self._fatos.setMaximumHeight(130)
        apagar = QPushButton("Apagar o marcado")
        apagar.clicked.connect(self._esquecer_fato)
        s = QVBoxLayout(sabe)
        s.addWidget(_discreto(QLabel("Ele pergunta de vez em quando e usa as respostas nas falas.", wordWrap=True)))
        s.addWidget(self._fatos)
        s.addWidget(apagar, 0, Qt.AlignmentFlag.AlignRight)
        return _pagina(categorias, cidade, ensinar, sabe)

    def _aba_aprendizado(self) -> QWidget:
        self._resumo_aprendizado = QLabel(wordWrap=True)
        self._aprendido = QTreeWidget()
        self._aprendido.setHeaderLabels(["Valor", "Opinião", "O quê"])
        self._aprendido.setRootIsDecorated(False)
        self._aprendido.setColumnWidth(0, 90)
        self._aprendido.setColumnWidth(1, 130)
        self._aprendido.setMinimumHeight(260)
        esquecer = QPushButton("Esquecer tudo o que ele aprendeu")
        esquecer.clicked.connect(self._esquecer_tudo)
        explica = _discreto(QLabel(
            "Carinho, queijo e ♥ fazem ele repetir o que fez há pouco. Tapa e ✕ fazem ele evitar. "
            "Depois de muitos tapas na mesma travessura, ele para de fazer, a não ser que tenha liberdade para teimar.",
            wordWrap=True,
        ))
        return _pagina(self._resumo_aprendizado, explica, self._aprendido, esquecer)

    def _aba_alarme(self) -> QWidget:
        self._entrada = _campo_hora()
        self._saida = _campo_hora()
        self._alarme = QCheckBox()
        self._fechar = QCheckBox()
        self._inicio = QCheckBox()
        linhas = [
            ("Horário de entrada", "Nessa hora o rato do alarme aparece e toca.", self._entrada),
            ("Horário de saída", "Nessa hora ele aparece de novo.", self._saida),
            ("Alarme ligado", "Desligado, o rato do alarme não aparece. O pet continua.", self._alarme),
        ]
        if sistema.mexe_em_outras_janelas():
            linhas.append(("Rato pode fechar janelas", "Desligado, ele continua com as outras travessuras.", self._fechar))
        if inicio.gerenciado():
            linhas.append(("Iniciar com o computador", "Desligado, o rato só roda quando você abrir o programa.", self._inicio))
        return _pagina(_grade(linhas))

    # ---- abrir e preencher ----

    def abrir(self) -> None:
        self._preencher(config.carregar(config.caminho_padrao()))
        self._atualizar_estado()
        self._relogio.start()
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, evento) -> None:
        self._relogio.stop()
        super().closeEvent(evento)

    def _preencher(self, atual: config.Config) -> None:
        self._atual = atual
        self._entrada.setTime(QTime(atual.entrada.hour, atual.entrada.minute))
        self._saida.setTime(QTime(atual.saida.hour, atual.saida.minute))
        self._alarme.setChecked(atual.alarme_ligado)
        self._fechar.setChecked(atual.fechar_janela)
        self._inicio.setChecked(atual.iniciar_com_sistema)
        self._pet_ligado.setChecked(atual.pet_ligado)
        self._saudacao.setChecked(atual.saudacao_boot)
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
        self._explicar()
        self._aviso.clear()

    def _cerebro(self) -> Cerebro:
        return self._pet.cerebro if self._pet is not None else Cerebro(caminho_cerebro())

    def _atualizar_estado(self) -> None:
        pet = self._pet
        for botao in self._botoes_pet + [self._dormir, self._acordar]:
            botao.setEnabled(pet is not None)
        self._estado.setText(pet.resumo() if pet is not None else "O pet não está rodando.")
        cerebro = self._cerebro()
        self._nivel.setValue(round(cerebro.progresso() * 100))
        self._nivel.setFormat(f"nível {cerebro.nivel}  ·  {cerebro.xp} xp")
        humor = round(cerebro.humor(relogio.time()))
        self._humor.setValue(humor)
        self._humor.setFormat("radiante" if humor >= 80 else "feliz" if humor >= 60 else "chateado" if humor >= 35 else "triste")
        self._listar_frases(cerebro)
        self._listar_fatos(cerebro)
        self._listar_aprendido(cerebro)

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
            f"Ensinou {len(cerebro.frases)} frases e sabe {len(cerebro.fatos)} coisas sobre você."
            if pesos else "Ele ainda não aprendeu nada. Dê carinho, queijo ou tapas e veja aqui o que muda."
        )
        linhas = []
        for ident, valor in pesos[:80]:
            barra = ("+" if valor > 0 else "−") + ("▮" * min(8, round(abs(valor) * 2)) or "·")
            linhas.append((barra, OPINIAO[cerebro.opiniao(ident)], nome_da_acao(ident)))
        atuais = [
            tuple(self._aprendido.topLevelItem(i).text(c) for c in range(3))
            for i in range(self._aprendido.topLevelItemCount())
        ]
        if atuais != linhas:
            self._aprendido.clear()
            self._aprendido.addTopLevelItems([QTreeWidgetItem(list(linha)) for linha in linhas])

    def _explicar(self) -> None:
        i = self._intensidade.value()
        espera = 60 + 3900 * (1 - i / 100) ** 2
        minutos = round(espera / 60)
        self._dica_intensidade.setText(
            f"Aparece mais ou menos a cada {minutos} minuto{'s' if minutos != 1 else ''} e fica um pouco"
            f"{' mais' if i > 60 else ''} na tela. Quanto mais alto, mais vezes ele vem e mais coisas faz em cada visita."
        )
        t = self._travessura.value()
        chance = round((0.04 + 0.56 * t / 100) * 100)
        self._dica_travessura.setText(
            f"Cerca de {chance}% do que ele faz são travessuras: fechar abas, mexer no cursor, largar coisas na tela... "
            "Só as liberadas na aba Permissões."
        )
        lib = self._liberdade.value()
        self._dica_liberdade.setText(
            "Segue à risca o que aprendeu com carinho e tapas." if lib < 25 else
            "Segue o que aprendeu, mas às vezes muda de ideia." if lib < 65 else
            "Faz o que quer. Às vezes repete até o que você já ensinou que não gosta."
        )

    # ---- ações ----

    def _no_pet(self, metodo: str) -> None:
        if self._pet is not None:
            getattr(self._pet, metodo)()
            self._atualizar_estado()

    def _chamar(self) -> None:
        self._no_pet("chamar")

    def _dar_queijo(self) -> None:
        self._no_pet("dar_queijo")

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
            "O rato volta a ser filhote: esquece o que aprendeu, as frases que você ensinou e o que sabe de você. Não dá para desfazer.",
        )
        if resposta != QMessageBox.StandardButton.Yes:
            return
        if self._pet is not None:
            self._pet.esquecer()
        else:
            self._cerebro().esquecer_tudo()
        self._aviso.setText("Ele esqueceu tudo.")
        self._atualizar_estado()

    def salvar(self) -> None:
        entrada, saida = self._entrada.time(), self._saida.time()
        # o sono pode ter mudado pelo menu do rato enquanto o painel estava aberto
        sono = config.carregar(config.caminho_padrao())
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
            dormir_ate=self._pet.cfg.dormir_ate if self._pet is not None else sono.dormir_ate,
            dormir_visivel=self._dormir_visivel.isChecked(),
            permissoes=tuple(k for k, c in self._permissoes.items() if c.isChecked()),
            falas=tuple(k for k, c in self._falas.items() if c.isChecked()),
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
