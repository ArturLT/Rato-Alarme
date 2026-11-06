import random
import unittest

from alarma.telas import Mapa

L = 196
# notebook à esquerda e monitor maior à direita, desalinhados
DUAS = [(0, 200, 1440, 1100), (1440, 0, 3360, 1080)]


def andar(mapa: Mapa, origem, destino, passo=5.0):
    """Anda em linha reta entre os pontos do caminho e confere cada posição."""
    x, y = origem
    for alvo in mapa.caminho(origem, destino):
        while True:
            dx, dy = alvo[0] - x, alvo[1] - y
            d = (dx * dx + dy * dy) ** 0.5
            if d <= passo:
                x, y = alvo
                break
            x, y = x + dx / d * passo, y + dy / d * passo
            yield x, y


class TestMapa(unittest.TestCase):
    def test_atravessa_monitores_desalinhados_sem_sair_da_tela(self) -> None:
        mapa = Mapa(DUAS, L)
        origem, destino = (100, 880), (3000, 50)
        posicoes = list(andar(mapa, origem, destino))
        self.assertTrue(all(mapa.valido(p) for p in posicoes))
        self.assertEqual(mapa.indice(posicoes[-1]), 1)

    def test_mesmo_monitor_vai_direto(self) -> None:
        mapa = Mapa(DUAS, L)
        self.assertEqual(mapa.caminho((100, 500), (900, 600)), [(900, 600)])

    def test_destino_fora_cabe_no_monitor(self) -> None:
        mapa = Mapa(DUAS, L)
        self.assertEqual(mapa.caminho((100, 500), (-500, 99999)), [(0, 1100 - L)])

    def test_tres_monitores_em_fila(self) -> None:
        mapa = Mapa([(0, 0, 1000, 800), (1000, 0, 2000, 800), (2000, 0, 3000, 800)], L)
        caminho = mapa.caminho((10, 10), (2800, 500))
        self.assertEqual(len(caminho), 5)
        self.assertTrue(all(mapa.valido(p) for p in andar(mapa, (10, 10), (2800, 500))))

    def test_monitor_em_cima(self) -> None:
        mapa = Mapa([(0, 0, 1920, 1080), (300, -900, 1900, 0)], L)
        self.assertTrue(all(mapa.valido(p) for p in andar(mapa, (100, 800), (1000, -800))))

    def test_monitores_soltos_nao_atravessa_o_vazio(self) -> None:
        mapa = Mapa([(0, 0, 1000, 800), (1500, 0, 2500, 800)], L)
        self.assertEqual(mapa.caminho((10, 10), (2000, 10)), [(1000 - L, 10)])

    def test_aleatorio_sempre_valido(self) -> None:
        mapa = Mapa(DUAS, L)
        acaso = random.Random(3)
        pontos = [mapa.aleatorio(acaso, 0) for _ in range(300)]
        self.assertTrue(all(mapa.valido(p) for p in pontos))
        self.assertGreater(sum(mapa.indice(p) == 0 for p in pontos), 150)

    def test_sai_pela_borda_livre(self) -> None:
        mapa = Mapa(DUAS, L)
        self.assertLess(mapa.saida((1200, 500))[0], 0)  # a direita do notebook dá no outro monitor
        self.assertGreater(mapa.saida((1500, 500))[0], 3000)
