"""O mapa dos monitores, para o rato andar por todos eles sem sair para o vazio. Sem Qt.

Posições são do canto de cima à esquerda da janela do rato (lado L). Um ponto é
válido se a janela inteira cabe num monitor. Para ir de um monitor a outro, o rato
passa pela borda que eles dividem, num trecho onde os dois existem: assim ele
nunca fica num lugar sem tela, nem quando os monitores têm tamanhos diferentes
ou estão desalinhados.
"""

import random
from collections import deque

Ret = tuple[int, int, int, int]  # x0, y0, x1, y1
FOLGA = 3


class Mapa:
    def __init__(self, telas: list[Ret], lado: int) -> None:
        self.telas = [t for t in telas if t[2] - t[0] >= lado and t[3] - t[1] >= lado] or [(0, 0, 1920, 1080)]
        self.lado = lado

    # ---- onde está ----

    def indice(self, ponto: tuple[float, float]) -> int:
        """O monitor onde está o meio do rato; fora de todos, o mais perto."""
        cx, cy = ponto[0] + self.lado / 2, ponto[1] + self.lado / 2
        for i, (x0, y0, x1, y1) in enumerate(self.telas):
            if x0 <= cx < x1 and y0 <= cy < y1:
                return i
        return min(range(len(self.telas)), key=lambda i: self._distancia(i, cx, cy))

    def _distancia(self, i: int, cx: float, cy: float) -> float:
        x0, y0, x1, y1 = self.telas[i]
        dx = max(x0 - cx, 0, cx - x1)
        dy = max(y0 - cy, 0, cy - y1)
        return dx * dx + dy * dy

    def tela(self, ponto: tuple[float, float]) -> Ret:
        return self.telas[self.indice(ponto)]

    def dentro(self, ponto: tuple[float, float], indice: int | None = None) -> tuple[float, float]:
        """O ponto mais perto em que a janela inteira cabe no monitor (o dele, ou o indicado)."""
        x0, y0, x1, y1 = self.telas[self.indice(ponto) if indice is None else indice]
        return min(max(ponto[0], x0), x1 - self.lado), min(max(ponto[1], y0), y1 - self.lado)

    def valido(self, ponto: tuple[float, float]) -> bool:
        """Nenhum pedaço da janela fora de todas as telas (no meio da travessia, ela fica em duas)."""
        x, y, L = ponto[0], ponto[1], self.lado
        amostras = [(x + a * L, y + b * L) for a in (0, 0.25, 0.5, 0.75, 1) for b in (0, 0.25, 0.5, 0.75, 1)]
        return all(
            any(x0 - FOLGA <= px <= x1 + FOLGA and y0 - FOLGA <= py <= y1 + FOLGA for x0, y0, x1, y1 in self.telas)
            for px, py in amostras
        )

    # ---- para onde ir ----

    def aleatorio(self, acaso: random.Random, preferida: int | None = None, chao: float = 0.6) -> tuple[float, float]:
        """Um lugar qualquer; no monitor preferido na maioria das vezes, e quase sempre perto do chão."""
        if preferida is not None and 0 <= preferida < len(self.telas) and (len(self.telas) == 1 or acaso.random() < 0.7):
            i = preferida
        else:
            pesos = [(t[2] - t[0]) * (t[3] - t[1]) for t in self.telas]
            i = acaso.choices(range(len(self.telas)), weights=pesos)[0]
        x0, y0, x1, y1 = self.telas[i]
        x = acaso.uniform(x0 + 20, max(x0 + 21, x1 - self.lado - 20))
        if acaso.random() < chao:
            y = y1 - self.lado - acaso.uniform(0, 30)
        else:
            y = acaso.uniform(y0 + min(160, (y1 - y0) / 4), max(y0 + 161, y1 - self.lado))
        return self.dentro((x, y), i)

    def _vizinhos(self, i: int) -> list[tuple[int, list[tuple[float, float]]]]:
        """Monitores encostados no i e os dois pontos da travessia: inteiro de um lado, inteiro do outro,
        na mesma altura (ou coluna), num trecho onde os dois monitores existem."""
        a, L, saida = self.telas[i], self.lado, []
        for j, b in enumerate(self.telas):
            if j == i:
                continue
            # lado a lado
            for borda, sinal in ((a[2], 1), (a[0], -1)):
                outra = b[0] if sinal > 0 else b[2]
                if abs(borda - outra) <= FOLGA:
                    lo, hi = max(a[1], b[1]), min(a[3], b[3]) - L
                    if hi >= lo:
                        y = (lo + hi) / 2
                        saida.append((j, [(borda - L if sinal > 0 else borda, y), (borda if sinal > 0 else borda - L, y)]))
            # um em cima do outro
            for borda, sinal in ((a[3], 1), (a[1], -1)):
                outra = b[1] if sinal > 0 else b[3]
                if abs(borda - outra) <= FOLGA:
                    lo, hi = max(a[0], b[0]), min(a[2], b[2]) - L
                    if hi >= lo:
                        x = (lo + hi) / 2
                        saida.append((j, [(x, borda - L if sinal > 0 else borda), (x, borda if sinal > 0 else borda - L)]))
        return saida

    def caminho(self, origem: tuple[float, float], destino: tuple[float, float]) -> list[tuple[float, float]]:
        """Pontos por onde passar, terminando no destino (ajustado para caber num monitor)."""
        i, j = self.indice(origem), self.indice(destino)
        destino = self.dentro(destino, j)
        if i == j:
            return [destino]
        anterior: dict[int, tuple[int, list[tuple[float, float]]] | None] = {i: None}
        fila = deque([i])
        while fila:
            k = fila.popleft()
            if k == j:
                break
            for vizinho, passagem in self._vizinhos(k):
                if vizinho not in anterior:
                    anterior[vizinho] = (k, passagem)
                    fila.append(vizinho)
        if j not in anterior:
            # monitores sem borda em comum: fica no próprio monitor
            return [self.dentro(destino, i)]
        travessias, k = [], j
        while anterior[k] is not None:
            k_ant, passagem = anterior[k]
            travessias.append(passagem)
            k = k_ant
        travessias.reverse()
        return [p for t in travessias for p in t] + [destino]

    def saida(self, ponto: tuple[float, float]) -> tuple[float, float]:
        """Para onde correr para sair de cena: a borda lateral mais perto que não dá para outro monitor."""
        i = self.indice(ponto)
        x0, y0, x1, y1 = self.telas[i]
        bordas = []
        livre_esq = not any(abs(t[2] - x0) <= FOLGA and t[1] < y1 and t[3] > y0 for k, t in enumerate(self.telas) if k != i)
        livre_dir = not any(abs(t[0] - x1) <= FOLGA and t[1] < y1 and t[3] > y0 for k, t in enumerate(self.telas) if k != i)
        if livre_esq:
            bordas.append((ponto[0] - x0, (x0 - self.lado * 0.8, ponto[1])))
        if livre_dir:
            bordas.append((x1 - ponto[0], (x1 - self.lado * 0.2, ponto[1])))
        if not bordas:
            return (x1 - self.lado * 0.2, ponto[1])
        return min(bordas)[1]
