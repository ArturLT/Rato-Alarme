"""Escolhe qual animação do rato mostrar e qual quadro dela. Sem GTK."""

from dataclasses import dataclass

from alarma.caca import (
    BAIXO,
    BAIXO_DIREITA,
    BAIXO_ESQUERDA,
    CIMA,
    CIMA_DIREITA,
    CIMA_ESQUERDA,
    DIREITA,
    ESQUERDA,
    Fase,
)

DORMINDO = "dormindo"
FUGA = "fuga"
CORRENDO = "correndo"
CORRENDO_CIMA = "correndo-cima"
CORRENDO_BAIXO = "correndo-baixo"
CORRENDO_CIMA_LADO = "correndo-cima-lado"
CORRENDO_BAIXO_LADO = "correndo-baixo-lado"
CANSADO = "cansado"
FALANDO = "falando"
ACERTO = "acerto"
PEGO = "pego"
SUMINDO = "sumindo"
NOMES = (
    DORMINDO,
    FUGA,
    CORRENDO,
    CORRENDO_CIMA,
    CORRENDO_BAIXO,
    CORRENDO_CIMA_LADO,
    CORRENDO_BAIXO_LADO,
    CANSADO,
    FALANDO,
    ACERTO,
    PEGO,
    SUMINDO,
)
# Direção → (animação, espelhada). O lado esquerdo é o direito espelhado.
CORRIDA = {
    DIREITA: (CORRENDO, False),
    ESQUERDA: (CORRENDO, True),
    CIMA: (CORRENDO_CIMA, False),
    BAIXO: (CORRENDO_BAIXO, False),
    CIMA_DIREITA: (CORRENDO_CIMA_LADO, False),
    CIMA_ESQUERDA: (CORRENDO_CIMA_LADO, True),
    BAIXO_DIREITA: (CORRENDO_BAIXO_LADO, False),
    BAIXO_ESQUERDA: (CORRENDO_BAIXO_LADO, True),
}
DUR_ACERTO = 0.45
DUR_PEGO = 1.9
ESPERA_SUMIR = 3.0
DUR_SUMINDO = 1.1


@dataclass(frozen=True)
class Clipe:
    quadros: int
    fps: int
    loop: bool

    def indice(self, segundos: float) -> int:
        n = int(segundos * self.fps)
        return n % self.quadros if self.loop else min(n, self.quadros - 1)


def clipe_da_folha(meta: dict) -> Clipe:
    """O último quadro de uma animação de uma vez só é vazio: fica de fora."""
    dados = meta["pixelfx"]
    quadros = dados["frames"] if dados["loop"] else dados["frames"] - 1
    return Clipe(quadros, dados["fps"], dados["loop"])


def depois_de_pego(segundos: float) -> str | None:
    """O que mostrar depois da captura. None quer dizer que o rato já sumiu."""
    if segundos < DUR_PEGO:
        return PEGO
    if segundos < DUR_PEGO + ESPERA_SUMIR:
        return DORMINDO
    if segundos < DUR_PEGO + ESPERA_SUMIR + DUR_SUMINDO:
        return SUMINDO
    return None


def escolher(
    fase: str | None,
    cansado: bool,
    em_acerto: bool,
    depois: str | None,
    falando: bool = False,
) -> str:
    if fase is None or fase == Fase.PEGO:
        return depois or DORMINDO
    if fase == Fase.GAIOLA:
        return FUGA
    if em_acerto:
        return ACERTO
    if falando:
        return FALANDO
    return CANSADO if cansado else CORRENDO
