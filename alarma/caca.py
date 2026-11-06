"""Regras da caçada ao rato. Sem GTK: o tempo e o acaso vêm de fora."""

import math
import random

DUR_GAIOLA = 3.0
CLIQUES = 3
FUGA_S = 3.0
CANSADO_S = 1.5
RAIO_MEDO = 260.0
VEL_FUGA = 450.0
VEL_PASSEIO = 125.0
INTERVALO_TRAVESSURA = 20.0
LADO_RATO = 96
MIN_TRECHO = 220.0
MAX_TRECHO = 700.0
COMPROMISSO_S = 0.6

NOTAS = "notas"
YOUTUBE = "youtube"
JANELAS = "janelas"

DIREITA = "direita"
ESQUERDA = "esquerda"
CIMA = "cima"
BAIXO = "baixo"
CIMA_DIREITA = "cima-direita"
CIMA_ESQUERDA = "cima-esquerda"
BAIXO_DIREITA = "baixo-direita"
BAIXO_ESQUERDA = "baixo-esquerda"
_D = math.sqrt(0.5)
DIRECOES = {
    DIREITA: (1.0, 0.0),
    ESQUERDA: (-1.0, 0.0),
    CIMA: (0.0, -1.0),
    BAIXO: (0.0, 1.0),
    CIMA_DIREITA: (_D, -_D),
    CIMA_ESQUERDA: (-_D, -_D),
    BAIXO_DIREITA: (_D, _D),
    BAIXO_ESQUERDA: (-_D, _D),
}


class Fase:
    GAIOLA = "gaiola"
    SOLTO = "solto"
    PEGO = "pego"


class Caca:
    def __init__(
        self,
        acaso: random.Random,
        inicio: float,
        youtube_feito: bool = False,
    ) -> None:
        self._acaso = acaso
        self._inicio = inicio
        self._ciclo = inicio + DUR_GAIOLA
        self._proxima = inicio + DUR_GAIOLA + INTERVALO_TRAVESSURA
        self._fila = [NOTAS, JANELAS] if youtube_feito else [NOTAS, YOUTUBE, JANELAS]
        self._restante = 0.0
        self._velocidade = VEL_PASSEIO
        self._desde = inicio
        self._ultimo = inicio
        self.fase = Fase.GAIOLA
        self.cliques = 0
        self.x: float | None = None
        self.esquerda = False
        self.direcao = DIREITA
        self.y = 0.0

    @property
    def restantes(self) -> int:
        return CLIQUES - self.cliques

    def cansado(self, agora: float) -> bool:
        if self.fase != Fase.SOLTO:
            return False
        return (agora - self._ciclo) % (FUGA_S + CANSADO_S) >= FUGA_S

    def clique(self, agora: float) -> bool:
        """Conta um acerto. Retorna True quando o rato foi pego."""
        if self.fase != Fase.SOLTO:
            return False
        self.cliques += 1
        self._ciclo = agora
        self._restante = 0.0
        if self.cliques >= CLIQUES:
            self.fase = Fase.PEGO
            return True
        return False

    def _folga(self, vetor: tuple[float, float], limites: tuple[int, int, int, int]) -> float:
        """Quanto dá para andar nessa direção antes de bater na parede."""
        x0, y0, x1, y1 = limites
        folgas = []
        if vetor[0]:
            folgas.append(((x1 if vetor[0] > 0 else x0) - self.x) / vetor[0])
        if vetor[1]:
            folgas.append(((y1 if vetor[1] > 0 else y0) - self.y) / vetor[1])
        return min(folgas)

    def _planejar(
        self,
        agora: float,
        medo: tuple[float, float] | None,
        limites: tuple[int, int, int, int],
    ) -> None:
        """Escolhe o próximo trecho. medo é o vetor que aponta para longe do cursor."""
        atual = DIRECOES[self.direcao]
        contrario = (-atual[0], -atual[1])
        folgas = {nome: self._folga(v, limites) for nome, v in DIRECOES.items()}
        opcoes = [n for n, f in folgas.items() if f >= MIN_TRECHO]
        if not opcoes:
            opcoes = [max(folgas, key=folgas.__getitem__)]

        if medo is not None:
            nome = max(
                opcoes,
                key=lambda n: DIRECOES[n][0] * medo[0]
                + DIRECOES[n][1] * medo[1]
                + self._acaso.uniform(0, 0.3),
            )
        else:
            sem_volta = [n for n in opcoes if DIRECOES[n] != contrario] or opcoes
            nome = self._acaso.choice(sem_volta)

        self.direcao = nome
        vetor = DIRECOES[nome]
        if vetor[0]:
            self.esquerda = vetor[0] < 0
        self._restante = min(folgas[nome], self._acaso.uniform(MIN_TRECHO, MAX_TRECHO))
        self._velocidade = VEL_PASSEIO if medo is None else VEL_FUGA
        self._desde = agora

    def passo(
        self,
        agora: float,
        cursor: tuple[int, int] | None,
        area: tuple[int, int, int, int],
    ) -> tuple[int, int] | None:
        """Avança o rato e retorna a nova posição, ou None se ele não andou."""
        x0, y0, x1, y1 = area
        limites = (x0, y0, x1 - LADO_RATO, y1 - LADO_RATO)
        dt = agora - self._ultimo
        self._ultimo = agora

        if self.x is None:
            self.x, self.y = (limites[0] + limites[2]) / 2, (limites[1] + limites[3]) / 2
            return round(self.x), round(self.y)
        if self.fase == Fase.GAIOLA:
            if agora - self._inicio < DUR_GAIOLA:
                return None
            self.fase = Fase.SOLTO
        if self.fase != Fase.SOLTO or self.cansado(agora):
            return None

        self.x = min(max(self.x, limites[0]), limites[2])
        self.y = min(max(self.y, limites[1]), limites[3])

        medo = None
        if cursor is not None:
            dx = self.x + LADO_RATO / 2 - cursor[0]
            dy = self.y + LADO_RATO / 2 - cursor[1]
            distancia = math.hypot(dx, dy)
            if distancia < RAIO_MEDO:
                medo = (dx / distancia, dy / distancia) if distancia else (1.0, 0.0)

        vetor = DIRECOES[self.direcao]
        if self._restante <= 0:
            self._planejar(agora, medo, limites)
        elif medo is not None:
            self._velocidade = VEL_FUGA
            indo_para_o_cursor = vetor[0] * medo[0] + vetor[1] * medo[1] < 0
            if indo_para_o_cursor and agora - self._desde >= COMPROMISSO_S:
                self._planejar(agora, medo, limites)

        vetor = DIRECOES[self.direcao]
        anda = min(self._restante, self._velocidade * dt, self._folga(vetor, limites))
        self.x += vetor[0] * anda
        self.y += vetor[1] * anda
        self._restante -= anda
        if self._folga(vetor, limites) < 1:
            self._restante = 0.0
        return round(self.x), round(self.y)

    def travessura(self, agora: float) -> str | None:
        """Retorna a travessura da vez, ou None se ainda não chegou a hora."""
        if self.fase != Fase.SOLTO or agora < self._proxima:
            return None
        self._proxima = agora + INTERVALO_TRAVESSURA
        escolhida = self._fila.pop(0)
        if escolhida != YOUTUBE:
            self._fila.append(escolhida)
        return escolhida
