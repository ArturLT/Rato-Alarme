import unittest
from datetime import datetime, time, timedelta, timezone

from alarma.logica import LIMIAR_MANHA, LIMIAR_TARDE, Alarme, decidir

TZ = timezone(timedelta(hours=-3))


def instante(dia: int, hora: int, minuto: int, segundo: int = 0) -> datetime:
    return datetime(2026, 11, dia, hora, minuto, segundo, tzinfo=TZ)


class TestDecidir(unittest.TestCase):
    def test_computador_desligado_nao_alarme(self) -> None:
        decisao = decidir(False, instante(6, 7, 10), instante(6, 7, 10), fuso=TZ)
        self.assertEqual(decisao.alarme, Alarme.NENHUM)
        self.assertFalse(decisao.ativo)

    def test_ligou_antes_das_0650(self) -> None:
        decisao = decidir(True, instante(6, 6, 49, 59), instante(6, 8, 0), fuso=TZ)
        self.assertEqual(decisao.alarme, Alarme.NENHUM)

    def test_ligou_exatamente_0650(self) -> None:
        decisao = decidir(True, instante(6, 6, 50), instante(6, 6, 50), fuso=TZ)
        self.assertEqual(decisao.alarme, Alarme.MANHA)
        self.assertTrue(decisao.ativo)

    def test_ligou_entre_os_limiares(self) -> None:
        decisao = decidir(True, instante(6, 12, 48, 59), instante(6, 12, 48, 59), fuso=TZ)
        self.assertEqual(decisao.alarme, Alarme.MANHA)

    def test_ligou_exatamente_1249(self) -> None:
        decisao = decidir(True, instante(6, 12, 49), instante(6, 12, 49), fuso=TZ)
        self.assertEqual(decisao.alarme, Alarme.TARDE)

    def test_ligou_depois_das_1249_fica_so_na_tarde(self) -> None:
        decisao = decidir(True, instante(6, 18, 5), instante(6, 18, 5), fuso=TZ)
        self.assertEqual(decisao.alarme, Alarme.TARDE)

    def test_boot_de_outro_dia_nao_conta(self) -> None:
        decisao = decidir(True, instante(5, 22, 0), instante(6, 9, 0), fuso=TZ)
        self.assertEqual(decisao.alarme, Alarme.NENHUM)

    def test_limiares(self) -> None:
        self.assertEqual(LIMIAR_MANHA, time(6, 50))
        self.assertEqual(LIMIAR_TARDE, time(12, 49))


if __name__ == "__main__":
    unittest.main()
