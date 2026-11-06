"""Como o rato é: nome, pelo, cabelo, roupa e acessórios. E a montagem dos sprites com tudo isso.

As folhas do PixelFX saem com o rato cinza e pelado. Aqui, quadro a quadro:
1. as cores do pelo são trocadas pela paleta escolhida;
2. onde a máscara (rato-X.mascara.png) é magenta, entra a roupa, com a mesma luz e sombra do pelo;
3. chapéu, cabelo, coisas do rosto e do pescoço são colados nos pontos de encaixe que a folha traz.
"""

import json
from dataclasses import asdict, dataclass, fields, replace
from datetime import date
from pathlib import Path

from alarma.caminhos import pasta_config

PASTA_ACESSORIOS = Path(__file__).parent / "folhas" / "acessorios"

# A paleta original do pelo (_rato.js): contorno, 5 tons e o brilho do olho.
PELO_BASE = ["#17121c", "#352c3a", "#574b58", "#7f7278", "#a99c9c", "#d6cabf", "#fff4e6"]
PELOS = {
    "cinza": ("Cinza", PELO_BASE[1:6]),
    "marrom": ("Marrom", ["#3a2418", "#5e3a24", "#8a5a36", "#b88456", "#e2c29a"]),
    "caramelo": ("Caramelo", ["#5a3410", "#8c5420", "#c8843a", "#e8b064", "#fbe2b0"]),
    "branco": ("Branco", ["#5c5866", "#8a8696", "#c4c0cc", "#e6e2ec", "#fbf8ff"]),
    "preto": ("Preto", ["#1e1a26", "#2c2638", "#3e384c", "#58526a", "#a8a0b8"]),
    "chocolate": ("Chocolate", ["#2a160e", "#42241a", "#5e3626", "#7c4c36", "#c09a80"]),
    "dourado": ("Dourado", ["#5a3a08", "#8a6010", "#c8981c", "#f0c844", "#fff0a8"]),
    "azul": ("Azul fantasia", ["#1c2448", "#2c3a70", "#4a62a8", "#7a96d8", "#c8d8ff"]),
    "rosa": ("Rosa fantasia", ["#5a2440", "#8a3a66", "#c06a98", "#e8a0c4", "#ffe0f0"]),
    "verde": ("Verde zumbi", ["#1c3a20", "#2c5a30", "#4a8a48", "#7ab868", "#cfeec0"]),
    "lilas": ("Lilás", ["#3a2a5a", "#56408a", "#7a62b8", "#a690dc", "#e2d8ff"]),
}
CORES = {
    "vermelho": ("Vermelho", "#d03838"),
    "laranja": ("Laranja", "#e87830"),
    "amarelo": ("Amarelo", "#f0c030"),
    "verde": ("Verde", "#3aa060"),
    "azul": ("Azul", "#3a7cd8"),
    "roxo": ("Roxo", "#7a4ac8"),
    "rosa": ("Rosa", "#e85a9a"),
    "preto": ("Preto", "#2a2632"),
    "branco": ("Branco", "#ece8f0"),
    "marrom": ("Marrom", "#7a4a2a"),
    "loiro": ("Loiro", "#f0d070"),
    "ruivo": ("Ruivo", "#d0602a"),
}
ESTAMPAS = {
    "": "Sem roupa",
    "lisa": "Camiseta lisa",
    "listras": "Listrada",
    "xadrez": "Xadrez",
    "bolinhas": "Bolinhas",
    "moletom": "Moletom com bolso",
}
PERSONALIDADES = {
    "brincalhao": ("Brincalhão", "Inventa mais brincadeiras."),
    "curioso": ("Curioso", "Traz mais notícias e curiosidades."),
    "carinhoso": ("Carinhoso", "Fala mais coisas fofas."),
    "travesso": ("Travesso", "Apronta um pouco mais."),
    "preguicoso": ("Preguiçoso", "Cochila mais e anda devagar."),
}
SLOTS = ("cabelo", "pescoco", "rosto", "chapeu")  # ordem de desenho: o chapéu fica por cima do cabelo
CABELO_BASE = ["#ff0010", "#ff0020", "#ff0030", "#ff0040"]
MAGENTA = (255, 0, 255)
SEM_ACESSORIO = ("morto", "pendurado")
NOMES_SUGERIDOS = ["Queijinho", "Ratatouille", "Bigode", "Pipoca", "Tico", "Farofa", "Requeijão", "Biscoito", "Pingo", "Gouda"]


def caminho_padrao() -> Path:
    return pasta_config() / "rato.json"


@dataclass(frozen=True)
class Aparencia:
    nome: str = "Queijinho"
    pelo: str = "cinza"
    cabelo: str = ""
    cor_cabelo: str = "marrom"
    chapeu: str = ""
    rosto: str = ""
    pescoco: str = ""
    roupa: str = ""
    cor_roupa: str = "vermelho"
    personalidade: str = "brincalhao"
    adotado_em: str = ""

    def com(self, **mudancas) -> "Aparencia":
        return replace(self, **mudancas)

    def chave(self) -> tuple:
        """O que muda os sprites (o nome e a personalidade não mudam)."""
        return (self.pelo, self.cabelo, self.cor_cabelo, self.chapeu, self.rosto, self.pescoco, self.roupa, self.cor_roupa)

    def dias(self, hoje: date | None = None) -> int:
        try:
            inicio = date.fromisoformat(self.adotado_em)
        except ValueError:
            return 0
        return max(0, ((hoje or date.today()) - inicio).days)


def catalogo() -> dict:
    """Peças que existem, por slot: {slot: {id: nome}}."""
    try:
        dados = json.loads((PASTA_ACESSORIOS / "catalogo.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {s: {} for s in SLOTS}
    saida = {s: {} for s in SLOTS}
    for ident, pc in dados.get("pecas", {}).items():
        if pc.get("slot") in saida:
            saida[pc["slot"]][ident] = pc.get("nome", ident)
    return saida


def validar(a: Aparencia) -> Aparencia:
    """Troca o que não existir pelo padrão, para um arquivo velho ou estragado nunca quebrar o rato."""
    cat = catalogo()
    padrao = Aparencia()
    mudancas = {}
    if a.pelo not in PELOS:
        mudancas["pelo"] = padrao.pelo
    for campo in ("cor_cabelo", "cor_roupa"):
        if getattr(a, campo) not in CORES:
            mudancas[campo] = getattr(padrao, campo)
    for slot in SLOTS:
        if getattr(a, slot) and getattr(a, slot) not in cat[slot]:
            mudancas[slot] = ""
    if a.roupa not in ESTAMPAS:
        mudancas["roupa"] = ""
    if a.personalidade not in PERSONALIDADES:
        mudancas["personalidade"] = padrao.personalidade
    nome = " ".join(a.nome.split())[:24]
    if nome != a.nome:
        mudancas["nome"] = nome or padrao.nome
    return a.com(**mudancas) if mudancas else a


def carregar(caminho: Path | None = None) -> Aparencia:
    caminho = caminho or caminho_padrao()
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return validar(Aparencia(adotado_em=date.today().isoformat()))
    if not isinstance(dados, dict):
        return Aparencia(adotado_em=date.today().isoformat())
    nomes = {f.name for f in fields(Aparencia)}
    valores = {k: v for k, v in dados.items() if k in nomes and isinstance(v, str)}
    a = Aparencia(**valores)
    if not a.adotado_em:
        a = a.com(adotado_em=date.today().isoformat())
    return validar(a)


def salvar(a: Aparencia, caminho: Path | None = None) -> None:
    caminho = caminho or caminho_padrao()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(".tmp")
    temporario.write_text(json.dumps(asdict(validar(a)), indent=2, ensure_ascii=False), encoding="utf-8")
    temporario.replace(caminho)


# ---- cores ----


def _rgb(texto: str) -> tuple[int, int, int]:
    texto = texto.lstrip("#")
    return int(texto[0:2], 16), int(texto[2:4], 16), int(texto[4:6], 16)


def _misturar(a: tuple, b: tuple, t: float) -> tuple[int, int, int]:
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def rampa(base: str, n: int) -> list[tuple[int, int, int]]:
    """n tons do escuro ao claro em volta da cor base, com sombra puxada para o roxo (fica mais pixel art)."""
    cor = _rgb(base)
    sombra, luz = (30, 20, 50), (255, 250, 235)
    tons = []
    for i in range(n):
        t = i / max(1, n - 1)
        tons.append(_misturar(cor, sombra, 0.55 * (1 - t) ** 1.4) if t < 0.5 else _misturar(cor, luz, 0.45 * (t - 0.5) * 2))
    return tons


def trocas_de_pelo(pelo: str) -> dict[tuple, tuple]:
    novos = PELOS.get(pelo, PELOS["cinza"])[1]
    return {_rgb(velho): _rgb(novo) for velho, novo in zip(PELO_BASE[1:6], novos)}


def _tom_do_pelo(rgb: tuple) -> int:
    """0 escuro, 1 médio, 2 claro: qual tom do pelo original estava ali."""
    try:
        i = [_rgb(c) for c in PELO_BASE].index(rgb)
    except ValueError:
        return 1
    return 0 if i <= 2 else 1 if i == 3 else 2


def cor_da_roupa(estampa: str, cor: str, x: int, y: int, tom: int) -> tuple[int, int, int]:
    """A cor da roupa num pixel do quadro, com a luz do pelo que estava embaixo."""
    tons = rampa(CORES.get(cor, CORES["vermelho"])[1], 3)
    branco = rampa("#ece8f0", 3)
    if cor == "branco":
        branco = rampa("#3a7cd8", 3)
    if estampa == "listras" and (y // 2) % 2:
        return branco[tom]
    if estampa == "xadrez" and ((x // 2) + (y // 2)) % 2:
        return _misturar(tons[tom], (20, 15, 30), 0.35)
    if estampa == "bolinhas" and (x % 4 == 1 and y % 4 == 1):
        return branco[min(2, tom + 1)]
    if estampa == "moletom" and y % 6 == 0:
        return tons[max(0, tom - 1)]
    return tons[tom]


# ---- montagem dos quadros (precisa do Qt) ----


def _acessorio(ident: str, vista: str, cabelo: str):
    """A imagem do acessório (QImage 32x32 com encaixe no meio), com o cabelo já na cor escolhida."""
    from PySide6.QtGui import QImage

    caminho = PASTA_ACESSORIOS / f"{ident}-{vista}.png"
    if not caminho.exists() and vista == "costas":
        return None
    if not caminho.exists():
        caminho = PASTA_ACESSORIOS / f"{ident}-lado.png"
    imagem = QImage(str(caminho))
    if imagem.isNull():
        return None
    imagem = imagem.convertToFormat(QImage.Format.Format_RGBA8888)
    tons = rampa(CORES.get(cabelo, CORES["marrom"])[1], 4)
    trocas = {_rgb(v): n for v, n in zip(CABELO_BASE, tons)}
    _trocar(imagem, lambda rgb, _x, _y: trocas.get(rgb))
    return imagem


def _trocar(imagem, funcao) -> None:
    """Passa por cada pixel visível; funcao(rgb, x, y) devolve a cor nova ou None."""
    largura, altura = imagem.width(), imagem.height()
    linha = imagem.bytesPerLine()
    dados = imagem.bits()
    for y in range(altura):
        base = y * linha
        for x in range(largura):
            i = base + x * 4
            if dados[i + 3] == 0:
                continue
            nova = funcao((dados[i], dados[i + 1], dados[i + 2]), x, y)
            if nova is not None:
                dados[i], dados[i + 1], dados[i + 2] = nova


class Montador:
    """Veste os quadros de uma folha. Guarda os acessórios já carregados."""

    def __init__(self, aparencia: Aparencia) -> None:
        self.aparencia = aparencia
        self._pelo = trocas_de_pelo(aparencia.pelo)
        self._pecas: dict[tuple[str, str], object] = {}
        self._vestido = aparencia.pelo != "cinza" or bool(aparencia.roupa) or any(getattr(aparencia, s) for s in SLOTS)

    @property
    def mexe(self) -> bool:
        return self._vestido

    def _peca(self, ident: str, vista: str):
        chave = (ident, vista)
        if chave not in self._pecas:
            self._pecas[chave] = _acessorio(ident, vista, self.aparencia.cor_cabelo)
        return self._pecas[chave]

    def vestir(self, quadro, mascara, ancora: dict | None, animacao: str):
        """quadro e mascara: QImage do mesmo tamanho (rato olhando para a direita). Devolve um QImage novo."""
        from PySide6.QtCore import QPoint
        from PySide6.QtGui import QImage, QPainter

        imagem = quadro.convertToFormat(QImage.Format.Format_RGBA8888)
        if not self._vestido:
            return imagem
        a = self.aparencia
        pelo = self._pelo
        roupa = a.roupa
        tronco = None
        if roupa and mascara is not None:
            m = mascara.convertToFormat(QImage.Format.Format_RGBA8888)
            md, ml = m.constBits(), m.bytesPerLine()
            tronco = {
                (x, y)
                for y in range(m.height())
                for x in range(m.width())
                if md[y * ml + x * 4 + 3] and (md[y * ml + x * 4], md[y * ml + x * 4 + 1], md[y * ml + x * 4 + 2]) == MAGENTA
            }

        def pintar(rgb, x, y):
            if tronco and (x, y) in tronco:
                return cor_da_roupa(roupa, a.cor_roupa, x, y, _tom_do_pelo(rgb))
            return pelo.get(rgb)

        _trocar(imagem, pintar)
        if ancora and animacao not in SEM_ACESSORIO:
            pintor = QPainter(imagem)
            pintor.setOpacity(float(ancora.get("fade", 1) or 0))
            vista = ancora.get("vista", "lado")
            for slot in SLOTS:
                ident = getattr(a, slot)
                ponto = ancora.get("olho" if slot == "rosto" else "pescoco" if slot == "pescoco" else "topo")
                if not ident or not ponto:
                    continue
                if slot == "rosto" and vista == "costas":
                    continue
                img = self._peca(ident, vista)
                if img is not None:
                    pintor.drawImage(QPoint(ponto[0] - img.width() // 2, ponto[1] - img.height() // 2), img)
            pintor.end()
        return imagem
