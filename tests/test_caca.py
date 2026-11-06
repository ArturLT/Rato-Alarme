import math
import random
import unittest

from alarma.caca import (
    CLIQUES,
    DIRECOES,
    DUR_GAIOLA,
    FUGA_S,
    INTERVALO_TRAVESSURA,
    JANELAS,
    LADO_RATO,
    NOTAS,
    VEL_FUGA,
    YOUTUBE,
    Caca,
    Fase,
)

AREA = (0, 0, 1920, 1080)


def solto() -> Caca:
    caca = Caca(random.Random(1), 0.0)
    caca.passo(0.0, None, AREA)
    caca.passo(DUR_GAIOLA, None, AREA)
    return caca


class TestCaca(unittest.TestCase):
    def test_comeca_na_gaiola_sem_aceitar_clique(self) -> None:
        caca = Caca(random.Random(1), 0.0)
        self.assertEqual(caca.fase, Fase.GAIOLA)
        self.assertFalse(caca.clique(1.0))
        self.assertEqual(caca.cliques, 0)

    def test_sai_da_gaiola_no_tempo(self) -> None:
        caca = Caca(random.Random(1), 0.0)
        caca.passo(0.0, None, AREA)
        caca.passo(DUR_GAIOLA - 0.1, None, AREA)
        self.assertEqual(caca.fase, Fase.GAIOLA)
        caca.passo(DUR_GAIOLA, None, AREA)
        self.assertEqual(caca.fase, Fase.SOLTO)

    def test_pego_so_no_ultimo_clique(self) -> None:
        caca = solto()
        for i in range(CLIQUES - 1):
            self.assertFalse(caca.clique(4.0 + i))
        self.assertTrue(caca.clique(9.0))
        self.assertEqual(caca.fase, Fase.PEGO)

    def test_foge_do_cursor(self) -> None:
        caca = solto()
        cursor = (round(caca.x) + 60, round(caca.y) + 48)
        antes = math.dist((caca.x, caca.y), cursor)
        agora = DUR_GAIOLA
        for _ in range(8):
            agora += 0.1
            caca.passo(agora, cursor, AREA)
        self.assertGreater(math.dist((caca.x, caca.y), cursor), antes + 200)

    def test_para_quando_cansa(self) -> None:
        caca = solto()
        agora = DUR_GAIOLA + FUGA_S + 0.2
        self.assertTrue(caca.cansado(agora))
        self.assertIsNone(caca.passo(agora, (0, 0), AREA))

    def test_nunca_sai_da_area(self) -> None:
        caca = solto()
        agora = DUR_GAIOLA
        for _ in range(2000):
            agora += 0.1
            caca.passo(agora, (round(caca.x) + 5, round(caca.y) + 5), AREA)
            self.assertTrue(0 <= caca.x <= 1920 - LADO_RATO)
            self.assertTrue(0 <= caca.y <= 1080 - LADO_RATO)

    def test_velocidade_maxima_sem_saltos(self) -> None:
        caca = solto()
        agora = DUR_GAIOLA
        for _ in range(300):
            antes = (caca.x, caca.y)
            agora += 0.1
            caca.passo(agora, (round(caca.x) + 5, round(caca.y) + 5), AREA)
            self.assertLessEqual(math.dist(antes, (caca.x, caca.y)), VEL_FUGA * 0.1 + 0.01)

    def _trechos(self, cursor_de, semente: int) -> list[float]:
        """Roda a caçada e mede quanto o rato anda antes de cada mudança de direção."""
        caca = Caca(random.Random(semente), 0.0)
        caca.passo(0.0, None, AREA)
        agora = DUR_GAIOLA
        caca.passo(agora, None, AREA)
        trechos, andado, direcao = [], 0.0, caca.direcao
        for _ in range(6000):
            agora += 0.1
            antes = (caca.x, caca.y)
            caca.passo(agora, cursor_de(caca, agora), AREA)
            if caca.direcao != direcao:
                trechos.append(andado)
                andado, direcao = 0.0, caca.direcao
            andado += math.dist(antes, (caca.x, caca.y))
        return trechos

    def test_sem_vai_e_volta_com_cursor_parado_no_limite_do_medo(self) -> None:
        def parado(_caca: Caca, _agora: float) -> tuple[int, int]:
            return (960, 540)

        for semente in range(5):
            trechos = self._trechos(parado, semente)
            self.assertGreater(len(trechos), 10)
            curtos = [t for t in trechos if t < 100]
            self.assertLess(len(curtos) / len(trechos), 0.1, trechos[:30])

    def test_sem_vai_e_volta_perseguido_ate_a_parede(self) -> None:
        def perseguidor(caca: Caca, agora: float) -> tuple[int, int]:
            angulo = agora * 1.3
            return (
                round(caca.x + 48 + math.cos(angulo) * 120),
                round(caca.y + 48 + math.sin(angulo) * 120),
            )

        for semente in range(5):
            trechos = self._trechos(perseguidor, semente)
            curtos = [t for t in trechos if t < 100]
            self.assertLess(len(curtos) / len(trechos), 0.1, trechos[:30])

    def test_anda_exatamente_na_direcao_do_sprite(self) -> None:
        caca = solto()
        agora = DUR_GAIOLA
        for _ in range(400):
            agora += 0.1
            antes = (caca.x, caca.y)
            direcao_antes = caca.direcao
            caca.passo(agora, None, AREA)
            if caca.direcao == direcao_antes and caca.x != antes[0] or caca.y != antes[1]:
                dx, dy = caca.x - antes[0], caca.y - antes[1]
                vx, vy = DIRECOES[caca.direcao]
                self.assertAlmostEqual(dx * vy - dy * vx, 0.0, places=6)

    def test_youtube_uma_vez_so(self) -> None:
        caca = solto()
        agora = DUR_GAIOLA
        vistas = []
        for _ in range(7):
            agora += INTERVALO_TRAVESSURA
            vistas.append(caca.travessura(agora))
        self.assertEqual(vistas.count(YOUTUBE), 1)
        self.assertEqual(vistas[:3], [NOTAS, YOUTUBE, JANELAS])

    def test_youtube_ja_feito_nao_repete(self) -> None:
        caca = Caca(random.Random(1), 0.0, youtube_feito=True)
        caca.passo(0.0, None, AREA)
        caca.passo(DUR_GAIOLA, None, AREA)
        agora = DUR_GAIOLA
        for _ in range(5):
            agora += INTERVALO_TRAVESSURA
            self.assertNotEqual(caca.travessura(agora), YOUTUBE)

    def test_sem_travessura_antes_da_hora(self) -> None:
        caca = solto()
        self.assertIsNone(caca.travessura(DUR_GAIOLA + 1))


if __name__ == "__main__":
    unittest.main()
