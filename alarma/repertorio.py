"""Tudo o que o rato sabe fazer e dizer. Cada interação tem uma chave própria, para
ele aprender uma por uma do que a pessoa gosta.

Textos podem usar {nome}, {comida}, {cor}, {animal}, {musica}, {time}, {bebida},
{lugar}, {filme}, {hobby}: o que o rato aprendeu nas perguntas. Uma fala que usa
um fato que ele ainda não sabe fica de fora do sorteio.
"""

import string
from dataclasses import dataclass
from functools import lru_cache

# tipos
FALA = "fala"
INFO = "info"
TRAVESSURA = "travessura"
BRINCADEIRA = "brincadeira"
PERGUNTA = "pergunta"

# categorias de fala que o painel liga e desliga
PIADAS = "piadas"
CURIOSIDADES = "curiosidades"
PROVOCACOES = "provocacoes"
CARINHO = "carinho"
LEMBRANCAS = "lembrancas"
NOTICIAS = "noticias"
CLIMA = "clima"
MUNDO = "mundo"
COMPUTADOR = "computador"
PERGUNTAS = "perguntas"
ENSINADAS = "ensinadas"
CATEGORIAS = {
    PIADAS: "Piadas de rato",
    CURIOSIDADES: "Curiosidades",
    PROVOCACOES: "Provocações",
    CARINHO: "Falas carinhosas",
    LEMBRANCAS: "Coisas que ele aprendeu sobre você",
    NOTICIAS: "Notícias",
    CLIMA: "Clima e previsão",
    MUNDO: "Cotações, história e feriados",
    COMPUTADOR: "Informações do computador",
    PERGUNTAS: "Perguntas para te conhecer",
    ENSINADAS: "Frases que você ensinou",
}
DA_INTERNET = (NOTICIAS, CLIMA, MUNDO)

# permissões que o painel liga e desliga
P_FECHAR_ABA = "fechar_abas"
P_MINIMIZAR = "minimizar"
P_CURSOR = "mover_cursor"
P_OBJETOS = "objetos"
P_MUDO = "mutar"
P_SITES = "abrir_sites"
P_NOTAS = "bloco_notas"
P_JANELAS = "mexer_janelas"
P_EMPURRAR = "empurrar_janelas"
P_APPS = "abrir_apps"
P_VOLUME = "mexer_volume"
P_NOTIFICAR = "notificacoes"
PERMISSOES = {
    P_FECHAR_ABA: ("Fechar abas do navegador", "Só fecha quando o navegador está na frente."),
    P_MINIMIZAR: ("Minimizar janelas", "Esconde a janela da frente. Ela volta pelo Dock ou pela barra de tarefas."),
    P_CURSOR: ("Mexer no cursor", "Ele morde o cursor e arrasta por alguns segundos."),
    P_OBJETOS: ("Deixar coisas na tela", "Queijo, meia, bilhetes... Clique neles para sumirem."),
    P_MUDO: ("Deixar o computador sem som", "O som volta quando você bate nele ou quando ele vai embora."),
    P_SITES: ("Abrir sites", "Vídeo de queijo e outras bobagens, no máximo uma vez por hora."),
    P_NOTAS: ("Escrever no bloco de notas", "Abre um bloco do próprio rato, não mexe nos seus arquivos."),
    P_EMPURRAR: ("Empurrar janelas", "Esbarra na janela da frente e ela anda um pouquinho."),
    P_APPS: ("Abrir programas bobos", "Calculadora e bloquinho de notas do sistema, para fazer graça."),
    P_VOLUME: ("Mexer no volume", "Abaixa o volume por um tempinho e depois devolve como estava."),
    P_NOTIFICAR: ("Mandar notificações", "Recadinhos do rato nas notificações do sistema."),
    P_JANELAS: ("Mexer e fechar janelas", "Só no Linux com Hyprland."),
}
PADRAO_DESLIGADAS = (P_MUDO, P_VOLUME)


@dataclass(frozen=True)
class Interacao:
    id: str
    tipo: str
    categoria: str
    textos: tuple[str, ...] = ()
    permissao: str | None = None
    peso: float = 1.0
    animacao: str = "falando"
    travessa: bool = False
    fonte: str = ""
    fato: str = ""

    @property
    def internet(self) -> bool:
        return self.categoria in DA_INTERNET


def campos(texto: str) -> set[str]:
    return {nome for _, nome, _, _ in string.Formatter().parse(texto) if nome}


def preencher(texto: str, fatos: dict[str, str]) -> str | None:
    """Troca {nome} e companhia pelo que ele sabe. None se faltar algum fato."""
    valores = dict(fatos)
    valores.setdefault("nome", "humano")
    if not campos(texto) <= set(valores):
        return None
    try:
        return texto.format(**valores)
    except (KeyError, IndexError, ValueError):
        return None


def _falas(categoria: str, prefixo: str, textos: list[str], **extra) -> list[Interacao]:
    return [Interacao(f"{prefixo}-{i + 1:02d}", FALA, categoria, (t,), **extra) for i, t in enumerate(textos)]


_PIADAS = [
    "Por que o rato não usa computador? Porque já é o mouse.",
    "Qual o queijo mais triste? O queijo prato... ele sempre fica por baixo.",
    "O que o rato disse pro gato? Nada. Eu não sou doido.",
    "Sabe o que é um rato num micro-ondas? Um rato aquecido. Não faça isso.",
    "Qual o contrário de volátil? Vem cá, sobrinho. Hehe.",
    "Por que o queijo não joga cartas? Porque tem medo do rato blefar.",
    "Fui no médico e ele disse que eu tenho queijo demais no sangue. Fiquei com cara de requeijão.",
    "Toc toc. Quem é? É o rato. Que rato? O rato que roeu sua paciência.",
    "Meu wi-fi caiu. Juro que não fui eu que roí o cabo. Dessa vez.",
    "O que o queijo falou quando olhou no espelho? Haloumi!",
    "Qual o rato mais rápido do mundo? O que viu o gato primeiro.",
    "Por que o rato atravessou o teclado? Pra chegar no Ctrl+Queijo.",
    "Eu ia contar uma piada sobre queijo, mas ela é muito parmesã... digo, pesada.",
    "Sou tão pequeno que meu backup cabe num pen drive de 1 mega.",
    "Qual a música favorita do rato? Queijo-me, queijo-me muito.",
    "Por que o rato é bom em matemática? Porque roi os números.",
    "O que é um rato com uma espada? Um ratoso cavaleiro.",
    "Tentei fazer dieta. Durou do café da manhã até o primeiro cheiro de queijo.",
    "Minha senha é 'queijo123'. Não conta pra ninguém.",
    "Sabe por que eu nunca perco no esconde-esconde? Eu moro atrás do seu monitor.",
    "Eu não sou bagunceiro. Sou um designer de caos.",
    "Fui demitido da fábrica de queijo. Diziam que eu fazia muitos furos no trabalho.",
    "O que o rato falou quando viu o morcego? Olha, um primo que fez faculdade de aviação!",
    "Rato que dorme, o gato pega. Por isso eu durmo no seu teclado.",
    "Me chama de ratinho do RH: recursos humanos, queijos não.",
]

_CURIOSIDADES = [
    "Sabia que ratos dão risadinhas quando a gente faz cócegas? É sério, só que num som agudo demais pra você ouvir.",
    "Ratos conseguem passar por buracos do tamanho de uma moeda. Por isso nenhuma gaveta me segura.",
    "Os dentes da frente de um rato nunca param de crescer. Por isso eu roo tudo. Inclusive sua paciência.",
    "Ratos sonham! Eles repassam caminhos do labirinto enquanto dormem.",
    "Na verdade, ratos preferem doce a queijo. Mas não conta pra ninguém que eu disse isso.",
    "O primeiro mouse de computador era de madeira, feito em 1964. Meu tataravô.",
    "Um polvo tem três corações. Eu só tenho um, e ele é seu.",
    "O mel não estraga. Acharam mel de 3 mil anos nas pirâmides, ainda bom de comer.",
    "Bananas são levemente radioativas. Nada que faça mal, relaxa.",
    "Os flamingos são rosa por causa do que comem. Se eu comesse só queijo, ficaria amarelo?",
    "A Torre Eiffel cresce uns 15 centímetros no verão, por causa do calor.",
    "Os humanos piscam umas 15 vezes por minuto. Você piscou agora, eu vi.",
    "Lontras dormem de mãos dadas pra não se afastarem na água.",
    "O coração de uma baleia-azul é do tamanho de um carro pequeno.",
    "Existem mais estrelas no universo do que grãos de areia em todas as praias da Terra.",
    "O cérebro humano gasta uns 20% da energia do corpo. Pensa menos e come mais queijo.",
    "As vacas têm melhores amigas e ficam estressadas quando são separadas.",
    "O raio é cinco vezes mais quente que a superfície do Sol.",
    "O Brasil tem a maior biodiversidade do planeta: uma em cada dez espécies vive aqui.",
    "A primeira mensagem enviada pela internet, em 1969, foi 'LO'. Era pra ser 'LOGIN', mas o sistema travou.",
    "Ratos conseguem nadar por até três dias. Eu prefiro não testar.",
    "As abelhas reconhecem rostos humanos. Igual eu reconheço o seu.",
    "Um dia em Vênus dura mais que um ano em Vênus.",
    "O caracol pode dormir por até três anos. Meta de vida.",
    "O 'Ctrl+Z' foi inventado no Xerox PARC nos anos 70. Desde então, a humanidade erra sem medo.",
]

_PROVOCACOES = [
    "Você tá trabalhando ou só fingindo? Eu tô de olho.",
    "Quantas abas abertas, hein... posso fechar umas?",
    "Que tal uma pausa? Eu fico aqui vigiando o teclado.",
    "Aposto que você não consegue me pegar.",
    "Esse cursor aí parece gostoso. Posso morder?",
    "Ei! Ei! Ei! Nada não. Só queria atenção.",
    "Você tá muito sério. Sorri um pouquinho.",
    "Se você me der queijo, eu prometo me comportar. Talvez.",
    "Eu vi o que você digitou. Brincadeira. Ou não.",
    "Sabia que eu moro no seu computador e não pago aluguel?",
    "Hoje eu tô com vontade de aprontar...",
    "Você bebeu água hoje? Bebe água. Eu espero.",
    "Postura! Coluna reta! O rato tá mandando.",
    "Faz quanto tempo que você não levanta dessa cadeira?",
    "Se eu sumir, procura atrás das janelas. Eu adoro me esconder lá.",
]

_CARINHO = [
    "Gosto de passar o dia com você, {nome}.",
    "Você tá indo bem. Sério.",
    "Se precisar de mim, é só me chamar pelo ícone lá em cima.",
    "Tô orgulhoso de você, sabia?",
    "Um dia de cada vez. E um queijo de cada vez.",
    "Você é o melhor humano que eu já conheci. E olha que eu conheço uns três.",
    "Obrigado por não me expulsar hoje.",
    "Respira fundo. Prontinho. Melhor?",
    "Eu acho que hoje vai ser um bom dia.",
    "Não esquece de comer alguma coisa, tá?",
    "Se ficar cansado, descansa. O computador espera.",
    "Você me ensinou tanta coisa, {nome}.",
    "Cheguei só pra dizer oi. Oi!",
    "Já disse que você digita bonito?",
    "Fica tranquilo, eu tô aqui.",
]

_LEMBRANCAS = [
    ("nome", "{nome}! Eu lembrei do seu nome. Viu como eu aprendo?"),
    ("comida", "{nome}, tô com fome. Bem que podia ter {comida} aqui."),
    ("comida", "Sonhei com {comida}. Será que é bom com queijo?"),
    ("cor", "Pintei meu bigode de {cor} pra combinar com você. Mentira, não tenho tinta."),
    ("animal", "Hoje eu vi um {animal} na internet e lembrei de você."),
    ("musica", "Tô cantarolando {musica} desde cedo. A culpa é sua."),
    ("time", "Como anda o {time}? Torço junto, mesmo sem entender nada de bola."),
    ("bebida", "Que tal uma pausa pra um {bebida}?"),
    ("lugar", "Um dia eu quero conhecer {lugar}. Me leva na mochila?"),
    ("filme", "Assisti {filme} escondido no seu computador. Brincadeira... ou não."),
    ("hobby", "Quando você vai me ensinar a {hobby}?"),
]

_PERGUNTAS = [
    ("nome", "Como você se chama?"),
    ("comida", "Qual é a sua comida favorita?"),
    ("cor", "Qual é a sua cor favorita?"),
    ("animal", "Qual é o seu animal favorito? (Fala rato, fala rato...)"),
    ("musica", "Que música você anda ouvindo?"),
    ("time", "Você torce pra algum time?"),
    ("bebida", "Café, chá, suco ou refri? O que você mais bebe?"),
    ("lugar", "Que lugar do mundo você quer conhecer?"),
    ("filme", "Qual é o seu filme favorito?"),
    ("hobby", "O que você gosta de fazer quando não está no computador?"),
]

# Falas que ele só aprende subindo de nível, com carinho e queijo.
SEGREDOS = [
    "Aprendi uma palavra nova: 'cafuné'. Quer testar?",
    "Agora eu sei contar até dez: um, dois, queijo, quatro... ah, deixa.",
    "Descobri que se eu ficar quietinho, você me dá mais carinho.",
    "Eu tô ficando esperto, hein? Já sei a diferença entre aba e janela.",
    "Sabia que eu sei assobiar? fiu fiu. Não saiu. Mas eu sei.",
    "Meu novo truque: fingir de morto. ... ... Viu? Não vi você rindo.",
    "Aprendi a palavra 'obrigado'. Obrigado, {nome}.",
    "Já estou no nível de rato de laboratório. Pós-graduado.",
    "Hoje eu ensaiei um poema: queijo, queijinho, você é meu vizinho.",
    "Quando eu crescer quero ser um rato de biblioteca.",
]


def _infos() -> list[Interacao]:
    lista = [
        ("clima-agora", CLIMA, "clima_agora", "placa"),
        ("clima-hoje", CLIMA, "clima_hoje", "placa"),
        ("clima-amanha", CLIMA, "clima_amanha", "placa"),
        ("clima-chuva", CLIMA, "clima_chuva", "falando"),
        ("noticia-brasil", NOTICIAS, "noticia_brasil", "placa"),
        ("noticia-mundo", NOTICIAS, "noticia_mundo", "placa"),
        ("noticia-tecnologia", NOTICIAS, "noticia_tecnologia", "placa"),
        ("noticia-ciencia", NOTICIAS, "noticia_ciencia", "placa"),
        ("noticia-esportes", NOTICIAS, "noticia_esportes", "placa"),
        ("noticia-economia", NOTICIAS, "noticia_economia", "placa"),
        ("noticia-saude", NOTICIAS, "noticia_saude", "placa"),
        ("cotacao-dolar", MUNDO, "cotacao_dolar", "placa"),
        ("cotacao-euro", MUNDO, "cotacao_euro", "placa"),
        ("cotacao-bitcoin", MUNDO, "cotacao_bitcoin", "placa"),
        ("hoje-na-historia", MUNDO, "hoje_na_historia", "placa"),
        ("feriado", MUNDO, "proximo_feriado", "placa"),
        ("wikipedia", MUNDO, "wikipedia", "falando"),
        ("pc-bateria", COMPUTADOR, "bateria", "placa"),
        ("pc-cpu", COMPUTADOR, "cpu", "placa"),
        ("pc-memoria", COMPUTADOR, "memoria", "placa"),
        ("pc-disco", COMPUTADOR, "disco", "placa"),
        ("pc-ligado", COMPUTADOR, "tempo_ligado", "falando"),
        ("pc-hora", COMPUTADOR, "hora", "placa"),
        ("pc-sistema", COMPUTADOR, "sistema", "falando"),
        ("pc-programa", COMPUTADOR, "maior_programa", "falando"),
        ("pc-downloads", COMPUTADOR, "downloads", "falando"),
        ("pc-processos", COMPUTADOR, "processos", "falando"),
    ]
    return [Interacao(f"info-{i}", INFO, cat, fonte=fonte, animacao=anim, peso=1.4) for i, cat, fonte, anim in lista]


def _travessuras() -> list[Interacao]:
    t = TRAVESSURA
    itens = [
        Interacao("fechar-aba", t, t, ("Ops, fechei uma aba. Ela tava pedindo.",), P_FECHAR_ABA, 1.0, "acerto", True),
        Interacao("minimizar", t, t, ("Escondi sua janela. Acha ela!",), P_MINIMIZAR, 1.0, "acerto", True),
        Interacao("arrastar-cursor", t, t, ("Peguei seu cursor! É meu agora!",), P_CURSOR, 1.0, "puxando", True),
        Interacao("tremer-cursor", t, t, ("Tô fazendo cosquinha no seu cursor.",), P_CURSOR, 0.6, "feliz", True),
        Interacao("mutar", t, t, ("Shhh... silêncio. O rato tá pensando.",), P_MUDO, 0.4, "falando", True),
        Interacao("video-queijo", t, t, ("Olha que vídeo lindo eu achei!",), P_SITES, 0.3, "feliz", True),
        Interacao("notas", t, t, ("Vou escrever no meu diário.",), P_NOTAS, 0.7, "falando", True),
        Interacao("mexer-janelas", t, t, ("Arrumei suas janelas. Do meu jeito.",), P_JANELAS, 0.8, "acerto", True),
        Interacao("fechar-janela", t, t, ("Essa janela tava feia.",), P_JANELAS, 0.4, "acerto", True),
    ]
    itens += [
        Interacao("empurrar-janela", t, t, ("Ops, esbarrei na sua janela.",), P_EMPURRAR, 0.8, "feliz", True),
        Interacao("abrir-calculadora", t, t, ("Abri a calculadora pra contar meus queijos.",), P_APPS, 0.4, "feliz", True),
        Interacao("abrir-recado", t, t, ("Deixei um recado num bloquinho pra você.",), P_APPS, 0.3, "falando", True),
        Interacao("baixar-volume", t, t, ("Shhh... abaixei o volume um pouquinho. Já devolvo.",), P_VOLUME, 0.4, "falando", True),
        Interacao("notificacao", t, t, ("Te mandei uma notificação! Olha lá.",), P_NOTIFICAR, 0.7, "acenando", True),
    ]
    for item, fala in (
        ("queijo", "Deixei um queijinho pra você."),
        ("meia", "Achei sua meia. Não pergunta onde."),
        ("bilhete", "Escrevi um bilhete pra você."),
        ("moeda", "Achei uma moeda! Tá aí, de presente."),
        ("flor", "Trouxe uma flor. Não arranquei do vizinho, juro."),
        ("presente", "Trouxe um presente! Clica nele pra abrir."),
        ("bolinha", "Achei uma bolinha! Joga pra mim? Clica nela!"),
        ("biscoito", "Guardei um biscoito pra você. Só mordi um pouquinho."),
        ("maca", "Uma maçã pro professor... digo, pra você."),
        ("clipe", "Achei um clipe perdido. Vai que você precisa."),
        ("lapis", "Seu lápis tava no chão. De nada."),
        ("pena", "Uma pena! Não pergunta de que passarinho."),
        ("folha", "Trouxe uma folhinha lá de fora."),
        ("estrela", "Peguei uma estrela! Clica nela pra ter sorte."),
        ("cogumelo", "Achei um cogumelo. Não come, hein!"),
        ("botao", "Um botão! Acho que caiu da sua camisa."),
        ("papel", "Escrevi uma coisa num papel. Clica pra ler."),
    ):
        itens.append(Interacao(f"trazer-{item}", t, t, (fala,), P_OBJETOS, 0.9, f"andando-{item}", True))
    itens.append(Interacao("migalhas", t, t, ("Ops, deixei cair umas migalhas.",), P_OBJETOS, 0.6, "comendo", True))
    itens.append(Interacao("pegadas", t, t, ("Pisei no seu monitor com a pata suja.",), P_OBJETOS, 0.5, "andando", True))
    return itens


def _brincadeiras() -> list[Interacao]:
    b = BRINCADEIRA
    return [
        Interacao("passear", b, b, (), None, 1.5, "andando"),
        Interacao("cochilar", b, b, ("Vou tirar um cochilo rapidinho...",), None, 0.8, "cochilando"),
        Interacao("comer", b, b, ("Hora do lanche!",), None, 0.8, "comendo"),
        Interacao("dancar", b, b, ("Olha minha dancinha!",), None, 0.7, "feliz"),
        Interacao("acenar", b, b, ("Oi! Oi! Tô aqui!",), None, 0.8, "acenando"),
        Interacao("seguir-cursor", b, b, ("O que é isso aí? Deixa eu ver...",), None, 0.8, "andando"),
        Interacao("pedir-carinho", b, b, ("Passa o mouse em mim? Eu gosto.",), None, 0.7, "placa"),
        Interacao("sentar-olhar", b, b, (), None, 1.2, "sentado"),
        Interacao("correr", b, b, ("Corre, corre, corre!",), None, 0.6, "correndo"),
        Interacao("esconder", b, b, ("Onde será que eu tô?",), None, 0.5, "sumindo"),
        Interacao("pedir-queijo", b, b, ("Tem queijo? Clica em mim com o botão direito...",), None, 0.6, "placa"),
        Interacao("farejar", b, b, ("Sniff sniff... tô sentindo cheiro de queijo.",), None, 0.7, "andando"),
        Interacao("pular", b, b, ("Hop! Hop! Hop!",), None, 0.6, "feliz"),
        Interacao("bolinha-sozinho", b, b, ("Vou brincar de bolinha sozinho. Ou você quer jogar?",), None, 0.6, "correndo"),
        Interacao("pedir-colo", b, b, ("Me pega no colo? Clica e arrasta!",), None, 0.5, "placa"),
        Interacao("espreguicar", b, b, ("Ahhh... que preguiça.",), None, 0.6, "cochilando"),
    ]


def todas() -> list[Interacao]:
    lista: list[Interacao] = []
    lista += _falas(PIADAS, "piada", _PIADAS, peso=1.0)
    lista += _falas(CURIOSIDADES, "curiosidade", _CURIOSIDADES, peso=1.0, animacao="placa")
    lista += _falas(PROVOCACOES, "provocacao", _PROVOCACOES, peso=0.8)
    lista += _falas(CARINHO, "carinho", _CARINHO, peso=0.9)
    lista += [
        Interacao(f"lembranca-{i + 1:02d}", FALA, LEMBRANCAS, (texto,), peso=1.2, fato=fato)
        for i, (fato, texto) in enumerate(_LEMBRANCAS)
    ]
    lista += [
        Interacao(f"pergunta-{fato}", PERGUNTA, PERGUNTAS, (texto,), peso=1.0, animacao="placa", fato=fato)
        for fato, texto in _PERGUNTAS
    ]
    lista += _infos()
    lista += _travessuras()
    lista += _brincadeiras()
    return lista


@lru_cache(maxsize=1)
def _indice() -> dict[str, Interacao]:
    return {i.id: i for i in todas()}


def por_id() -> dict[str, Interacao]:
    return dict(_indice())


def segredo(indice: int) -> str:
    return SEGREDOS[indice % len(SEGREDOS)]


# Falas de reação, fora do sorteio: aparecem quando algo acontece.
SAUDACOES = {
    "manha": ["Bom dia, {nome}! Acordei antes de você.", "Bom dia! Já tomou café? Eu já comi queijo.", "Bom dia, flor do dia!"],
    "tarde": ["Boa tarde, {nome}! Voltei.", "Boa tarde! O dia tá rendendo?", "Oi de novo! Sentiu minha falta?"],
    "noite": ["Boa noite, {nome}! Trabalhando até agora?", "Boa noite! Não vai dormir tarde, hein.", "Ligou o computador de noite? Eu também sou notívago."],
    "madrugada": ["Madrugada, {nome}? Ninguém dorme mais nessa casa?", "Psiu... é madrugada. Mas eu tô acordado também."],
}
REACOES = {
    "tapa": ["Ai!", "Ei, isso doeu!", "Tá bom, tá bom!", "Aiii, por quê?", "Entendi, entendi..."],
    "expulso": ["Tá bom, eu vou embora...", "Fui! Mas eu volto.", "Hmpf. Vou ficar emburrado lá no canto."],
    "carinho": ["Hihihi, que bom!", "Ahhh, adoro carinho.", "Mais! Mais!", "Isso, aí atrás da orelha."],
    "queijo": ["QUEIJO! Obrigado!", "Nham nham nham.", "Você é demais! Queijo!", "Esse é do bom!"],
    "desistiu": [
        "Ia fazer uma travessura, mas lembrei que você não gosta.",
        "Hmm... melhor não. Aprendi que isso te irrita.",
        "Não vou fazer aquilo de novo. Prometo.",
    ],
    "teimoso": ["Eu sei que você não gosta, mas não resisti!", "Só dessa vez, vai!"],
    "aprendeu": ["Entendi! Você gosta disso.", "Anotado: isso te deixa feliz.", "Vou fazer mais vezes!"],
    "nao_gostou": ["Tá, não falo mais isso.", "Ok, anotado.", "Desculpa..."],
    "nivel": ["Subi de nível! Agora sou um rato nível {nivel}!", "Nível {nivel}! Tô ficando sabido."],
    "acordou": ["Ahhh... dormi bem! Voltei!", "Bom, acordei. O que eu perdi?"],
    "dormir": ["Tá bom... vou tirar uma soneca.", "Boa noite pra mim. Zzz."],
    "resposta": ["Anotado! Vou lembrar disso.", "Que legal! Agora eu sei.", "Guardei aqui no meu cérebro de rato."],
    "sem_resposta": ["Tudo bem, conta outra hora.", "Ah, segredo? Respeito."],
    "ensinada": ["Você me ensinou isso, lembra? \"{frase}\"", "Como você diz: \"{frase}\"", "\"{frase}\" — viu? Eu aprendi."],
    "voltou": ["Voltei! Sentiu minha falta?", "Cheguei!", "Surpresa!", "Tcharam!"],
    "fome": ["Tô com fome... tem queijo?", "Minha barriga tá roncando!", "Me dá comida? Botão direito em mim!", "Fome, fome, fome..."],
    "tedio": ["Tô entediado... brinca comigo?", "Que tédio. Joga uma bolinha pra mim?", "Ninguém brinca comigo..."],
    "triste": ["Tô tristinho hoje...", "Ninguém gosta de mim...", "Um carinho ia bem agora."],
    "fraco": ["Tô fraquinho... cuida de mim?", "Não tô me sentindo bem...", "Preciso de comida e carinho, rápido..."],
    "colo_bom": ["Uiii, que alto!", "Me leva pra passear!", "Colinho!", "Weeee!"],
    "colo_ruim": ["Me põe no chão!", "Ei! Me larga!", "Socorro, altura!"],
    "solto": ["Ufa, chão firme.", "De novo! De novo!", "Pousei!"],
    "bolinha": ["Bolinha! Bolinha!", "Peguei!", "Joga de novo!", "Essa foi longe!"],
    "comida": ["Nham!", "Delícia!", "Obrigado! Tava com fome.", "Isso é bom demais!"],
    "presente": ["Surpresa!", "Abriu! O que será?", "Gostou do presente?"],
    "estrela": ["Estrela da sorte! Ganhei experiência!", "Brilhou! Fiquei mais esperto."],
    "nasceu": ["Oi! Eu sou o {rato}! Prazer!", "Olá, mundo! Sou o {rato}, seu rato novo."],
}
