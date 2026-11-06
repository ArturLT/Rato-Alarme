import json
import unittest
from pathlib import Path

from alarma.animacao import (
    ACERTO,
    CANSADO,
    CORRENDO,
    CORRIDA,
    DORMINDO,
    DUR_PEGO,
    FUGA,
    NOMES,
    PEGO,
    Clipe,
    clipe_da_folha,
    escolher,
)
from alarma.caca import DIRECOES, DUR_GAIOLA, Fase

FOLHAS = Path(__file__).parent.parent / "alarma" / "folhas"


def folha(nome: str) -> dict:
    return json.loads((FOLHAS / f"rato-{nome}.json").read_text(encoding="utf-8"))


class TestAnimacao(unittest.TestCase):
    def test_escolha_por_estado(self) -> None:
        self.assertEqual(escolher(None, False, False, False), DORMINDO)
        self.assertEqual(escolher(None, False, False, True), PEGO)
        self.assertEqual(escolher(Fase.GAIOLA, False, False, False), FUGA)
        self.assertEqual(escolher(Fase.SOLTO, False, False, False), CORRENDO)
        self.assertEqual(escolher(Fase.SOLTO, True, False, False), CANSADO)
        self.assertEqual(escolher(Fase.SOLTO, True, True, False), ACERTO)

    def test_toda_direcao_tem_animacao(self) -> None:
        self.assertEqual(set(CORRIDA), set(DIRECOES))
        for nome, espelhada in CORRIDA.values():
            self.assertIn(nome, NOMES)
        self.assertTrue(CORRIDA["esquerda"][1])
        self.assertFalse(CORRIDA["cima"][1])

    def test_loop_repete_e_unica_para_no_fim(self) -> None:
        self.assertEqual(Clipe(4, 10, True).indice(0.5), 1)
        self.assertEqual(Clipe(4, 10, False).indice(9.0), 3)

    def test_folhas_existem_com_quadros(self) -> None:
        for nome in NOMES:
            dados = folha(nome)
            clipe = clipe_da_folha(dados["meta"])
            self.assertTrue((FOLHAS / f"rato-{nome}.png").exists())
            self.assertLessEqual(clipe.quadros, len(dados["frames"]))

    def test_tempos_batem_com_as_folhas(self) -> None:
        fuga = clipe_da_folha(folha(FUGA)["meta"])
        pego = clipe_da_folha(folha(PEGO)["meta"])
        self.assertAlmostEqual(fuga.quadros / fuga.fps, DUR_GAIOLA, delta=0.1)
        self.assertAlmostEqual(pego.quadros / pego.fps, DUR_PEGO + 0.1, delta=0.1)


if __name__ == "__main__":
    unittest.main()
