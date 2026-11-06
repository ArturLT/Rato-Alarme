import tempfile
import unittest
from pathlib import Path

from alarma import necessidades as nec
from alarma.necessidades import PAUSA_MAX_S, Necessidades


def passar(n: Necessidades, horas: float, inicio: float = 1000.0, **kw) -> list[str]:
    """Faz o tempo passar em passos de 5 minutos, como o pet faz."""
    avisos = []
    t = n.atualizado or inicio
    n.atualizado = t
    for _ in range(int(horas * 12)):
        t += 300
        avisos += n.atualizar(t, **kw)
    return avisos


class TestNecessidades(unittest.TestCase):
    def test_tudo_cai_com_o_tempo(self) -> None:
        n = Necessidades()
        passar(n, 2)
        self.assertLess(n.barriga, 80)
        self.assertLess(n.diversao, 80)
        self.assertEqual(n.vida, 100)

    def test_computador_desligado_nao_conta(self) -> None:
        n = Necessidades(atualizado=1000.0)
        n.atualizar(1000.0 + 3 * 24 * 3600)
        self.assertAlmostEqual(n.barriga, 80 - nec.POR_HORA["barriga"] * PAUSA_MAX_S / 3600)

    def test_abandonado_morre_e_conta_de_que(self) -> None:
        n = Necessidades()
        avisos = passar(n, 60)
        self.assertTrue(n.morto)
        self.assertEqual(n.vida, 0)
        self.assertIn(n.causa, ("fome", "tédio", "tristeza"))
        self.assertIn("morreu", avisos)
        self.assertIn("fome", avisos)
        self.assertIn("fraco", avisos)

    def test_bem_cuidado_nao_morre(self) -> None:
        n = Necessidades()
        for _ in range(48):
            passar(n, 1)
            n.alimentar(10)
            n.brincar(10)
            n.carinho(5)
        self.assertFalse(n.morto)
        self.assertEqual(n.vida, 100)

    def test_sem_morte_no_painel_fica_por_um_fio(self) -> None:
        n = Necessidades()
        passar(n, 80, pode_morrer=False)
        self.assertFalse(n.morto)
        self.assertGreaterEqual(n.vida, 1)

    def test_dormindo_cai_mais_devagar(self) -> None:
        a, b = Necessidades(), Necessidades()
        passar(a, 3)
        passar(b, 3, dormindo=True)
        self.assertGreater(b.barriga, a.barriga)

    def test_morto_nao_come_e_adotar_recomeca(self) -> None:
        n = Necessidades(vida=1, barriga=0)
        passar(n, 2)
        self.assertTrue(n.morto)
        n.alimentar()
        self.assertEqual(n.barriga, 0)
        n.adotar(5000.0)
        self.assertFalse(n.morto)
        self.assertEqual(n.vidas, 2)
        self.assertEqual(n.vida, 100)

    def test_pior_e_humor(self) -> None:
        n = Necessidades(barriga=10)
        self.assertEqual(n.pior(), "barriga")
        self.assertEqual(Necessidades(barriga=95, diversao=95, felicidade=95).humor(), "radiante")

    def test_salvar_e_ler(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "n.json"
            n = Necessidades(barriga=33.5, carinhos=4)
            nec.salvar(n, caminho)
            lido = nec.carregar(caminho)
            self.assertEqual((lido.barriga, lido.carinhos), (33.5, 4))
            caminho.write_text('{"barriga": "x", "vida": 500, "morto": 1}')
            lido = nec.carregar(caminho)
            self.assertEqual((lido.barriga, lido.vida, lido.morto), (80.0, 100.0, False))
