"""Barriga, diversão, felicidade e vida do rato. Sem Qt: o tempo vem de fora.

Tudo vai de 0 a 100. Com o tempo, barriga, diversão e felicidade caem. Se alguma
chegar a zero, a vida começa a cair; com tudo bem cuidado, a vida volta a subir.
Vida zero: o rato morre (de fome, de tédio ou de tristeza) e fica uma lápide,
até a pessoa adotar outro. Isso pode ser desligado no painel.

O tempo só conta com o programa aberto: com o computador desligado, o rato dorme.
Um intervalo maior que PAUSA_MAX_S entre duas contas vale só PAUSA_MAX_S.
"""

import json
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from pathlib import Path

from alarma.caminhos import pasta_estado

POR_HORA = {"barriga": 6.0, "diversao": 8.0, "felicidade": 4.0}
VIDA_PERDE_POR_HORA = 7.0
VIDA_GANHA_POR_HORA = 4.0
BEM_CUIDADO = 40.0
PAUSA_MAX_S = 10 * 60
FRACO = 30.0
AVISO = 25.0
CAUSAS = {"barriga": "fome", "diversao": "tédio", "felicidade": "tristeza"}


def caminho_padrao() -> Path:
    return pasta_estado() / "necessidades.json"


def _limitar(valor: float) -> float:
    return max(0.0, min(100.0, valor))


@dataclass
class Necessidades:
    barriga: float = 80.0
    diversao: float = 80.0
    felicidade: float = 75.0
    vida: float = 100.0
    morto: bool = False
    causa: str = ""
    morreu_em: str = ""
    atualizado: float = 0.0
    refeicoes: int = 0
    brincadeiras: int = 0
    carinhos: int = 0
    tapas: int = 0
    vidas: int = 1

    # ---- tempo ----

    def atualizar(self, agora: float, dormindo: bool = False, pode_morrer: bool = True) -> list[str]:
        """Faz o tempo passar. Retorna avisos novos: "fome", "tedio", "triste", "fraco", "morreu"."""
        if self.morto:
            self.atualizado = agora
            return []
        if self.atualizado <= 0:
            self.atualizado = agora
            return []
        passou = min(max(0.0, agora - self.atualizado), PAUSA_MAX_S)
        self.atualizado = agora
        if passou <= 0:
            return []
        horas = passou / 3600 * (0.5 if dormindo else 1.0)
        antes = {campo: getattr(self, campo) for campo in (*POR_HORA, "vida")}
        for campo, taxa in POR_HORA.items():
            setattr(self, campo, _limitar(getattr(self, campo) - taxa * horas))
        zerados = [c for c in POR_HORA if getattr(self, c) <= 0]
        if zerados:
            self.vida = _limitar(self.vida - VIDA_PERDE_POR_HORA * len(zerados) * horas)
        elif all(getattr(self, c) >= BEM_CUIDADO for c in POR_HORA):
            self.vida = _limitar(self.vida + VIDA_GANHA_POR_HORA * horas)
        if not pode_morrer:
            self.vida = max(self.vida, 1.0)

        avisos = []
        for campo, aviso in (("barriga", "fome"), ("diversao", "tedio"), ("felicidade", "triste")):
            if antes[campo] > AVISO >= getattr(self, campo):
                avisos.append(aviso)
        if antes["vida"] > FRACO >= self.vida:
            avisos.append("fraco")
        if self.vida <= 0:
            self._morrer(min(POR_HORA, key=lambda c: getattr(self, c)))
            avisos.append("morreu")
        return avisos

    def _morrer(self, campo: str) -> None:
        self.morto = True
        self.vida = 0.0
        self.causa = CAUSAS.get(campo, "tristeza")
        self.morreu_em = datetime.now().isoformat(timespec="minutes")

    # ---- cuidados ----

    def alimentar(self, quanto: float = 30.0) -> None:
        if self.morto:
            return
        self.barriga = _limitar(self.barriga + quanto)
        self.felicidade = _limitar(self.felicidade + quanto * 0.2)
        self.refeicoes += 1

    def brincar(self, quanto: float = 25.0) -> None:
        if self.morto:
            return
        self.diversao = _limitar(self.diversao + quanto)
        self.felicidade = _limitar(self.felicidade + quanto * 0.3)
        self.barriga = _limitar(self.barriga - quanto * 0.1)
        self.brincadeiras += 1

    def carinho(self, quanto: float = 10.0) -> None:
        if self.morto:
            return
        self.felicidade = _limitar(self.felicidade + quanto)
        self.diversao = _limitar(self.diversao + quanto * 0.3)
        self.carinhos += 1

    def tapa(self, quanto: float = 12.0) -> None:
        if self.morto:
            return
        self.felicidade = _limitar(self.felicidade - quanto)
        self.tapas += 1

    def divertir(self, quanto: float = 4.0) -> None:
        """Pequena alegria: ele fez algo que gosta, alguém clicou no que ele largou."""
        if not self.morto:
            self.diversao = _limitar(self.diversao + quanto)

    def adotar(self, agora: float) -> None:
        """Um rato novo no lugar do que morreu (ou por escolha)."""
        vidas = self.vidas + 1
        self.__init__()
        self.vidas = vidas
        self.atualizado = agora

    # ---- leitura ----

    @property
    def fraco(self) -> bool:
        return not self.morto and self.vida <= FRACO

    def pior(self) -> str | None:
        """A necessidade mais urgente, se alguma estiver baixa."""
        campo = min(POR_HORA, key=lambda c: getattr(self, c))
        return campo if getattr(self, campo) <= AVISO else None

    def humor(self) -> str:
        if self.morto:
            return "morto"
        media = (self.barriga + self.diversao + self.felicidade) / 3
        if self.fraco:
            return "fraco"
        if media >= 80:
            return "radiante"
        if media >= 60:
            return "feliz"
        if media >= 40:
            return "ok"
        if media >= 20:
            return "chateado"
        return "péssimo"


def carregar(caminho: Path | None = None) -> Necessidades:
    caminho = caminho or caminho_padrao()
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return Necessidades()
    if not isinstance(dados, dict):
        return Necessidades()
    n = Necessidades()
    for f in fields(Necessidades):
        valor = dados.get(f.name)
        padrao = getattr(n, f.name)
        if isinstance(padrao, bool):
            if isinstance(valor, bool):
                setattr(n, f.name, valor)
        elif isinstance(padrao, (int, float)) and isinstance(valor, (int, float)) and not isinstance(valor, bool):
            setattr(n, f.name, type(padrao)(valor) if not isinstance(padrao, float) else float(valor))
        elif isinstance(padrao, str) and isinstance(valor, str):
            setattr(n, f.name, valor)
    for campo in (*POR_HORA, "vida"):
        setattr(n, campo, _limitar(getattr(n, campo)))
    return n


def salvar(n: Necessidades, caminho: Path | None = None) -> None:
    caminho = caminho or caminho_padrao()
    try:
        caminho.parent.mkdir(parents=True, exist_ok=True)
        temporario = caminho.with_suffix(".tmp")
        temporario.write_text(json.dumps(asdict(n), indent=1), encoding="utf-8")
        temporario.replace(caminho)
    except OSError:
        pass
