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
    DUR_SUMINDO,
    ESPERA_SUMIR,
    FUGA,
    NOMES,
    PEGO,
    SUMINDO,
    Clipe,
    clipe_da_folha,
    depois_de_pego,
    FALANDO,
    escolher,
)
from alarma.caca import DIRECOES, DUR_GAIOLA, Fase

FOLHAS = Path(__file__).parent.parent / "alarma" / "folhas"


def folha(nome: str) -> dict:
    return json.loads((FOLHAS / f"rato-{nome}.json").read_text(encoding="utf-8"))


class TestAnimacao(unittest.TestCase):
    def test_escolha_por_estado(self) -> None:
        self.assertEqual(escolher(None, False, False, None), DORMINDO)
        self.assertEqual(escolher(None, False, False, PEGO), PEGO)
        self.assertEqual(escolher(None, False, False, SUMINDO), SUMINDO)
        self.assertEqual(escolher(Fase.GAIOLA, False, False, None), FUGA)
        self.assertEqual(escolher(Fase.SOLTO, False, False, None), CORRENDO)
        self.assertEqual(escolher(Fase.SOLTO, True, False, None), CANSADO)
        self.assertEqual(escolher(Fase.SOLTO, True, True, None), ACERTO)
        self.assertEqual(escolher(Fase.SOLTO, False, False, None, True), FALANDO)
        self.assertEqual(escolher(Fase.SOLTO, False, True, None, True), ACERTO)

    def test_some_um_tempo_depois_de_pego(self) -> None:
        self.assertEqual(depois_de_pego(0.5), PEGO)
        self.assertEqual(depois_de_pego(DUR_PEGO + 1), DORMINDO)
        self.assertEqual(depois_de_pego(DUR_PEGO + ESPERA_SUMIR + 0.2), SUMINDO)
        self.assertIsNone(depois_de_pego(DUR_PEGO + ESPERA_SUMIR + DUR_SUMINDO))

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
