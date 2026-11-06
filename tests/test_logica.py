import unittest
from datetime import datetime, time

from alarma.logica import (
    LIMIAR_MANHA,
    LIMIAR_TARDE,
    TOLERANCIA_MIN,
    Alarme,
    decidir,
    pendente,
    resumir,
)


def as_(hora: int, minuto: int, segundo: int = 0) -> datetime:
    return datetime(2026, 11, 6, hora, minuto, segundo)


class TestDecidir(unittest.TestCase):
    def test_horarios_padrao(self) -> None:
        self.assertEqual(LIMIAR_MANHA, time(6, 50))
        self.assertEqual(LIMIAR_TARDE, time(12, 49))
        self.assertEqual(TOLERANCIA_MIN, 60)

    def test_antes_da_entrada_nao_ha_alarme(self) -> None:
        decisao = decidir(as_(6, 49, 59))
        self.assertEqual(decisao.alarme, Alarme.NENHUM)
        self.assertFalse(decisao.ativo)
        self.assertFalse(decisao.no_horario)

    def test_exatamente_na_entrada(self) -> None:
        decisao = decidir(as_(6, 50))
        self.assertEqual(decisao.alarme, Alarme.MANHA)
        self.assertTrue(decisao.no_horario)

    def test_pc_ligado_logo_depois_da_entrada_ainda_vale(self) -> None:
        self.assertTrue(decidir(as_(6, 52)).no_horario)

    def test_ultimo_minuto_da_tolerancia(self) -> None:
        self.assertTrue(decidir(as_(7, 49, 59)).no_horario)

    def test_fim_da_tolerancia(self) -> None:
        decisao = decidir(as_(7, 50))
        self.assertEqual(decisao.alarme, Alarme.MANHA)
        self.assertFalse(decisao.no_horario)

    def test_ativar_as_dez_nao_esta_no_horario(self) -> None:
        self.assertFalse(decidir(as_(10, 21)).no_horario)

    def test_exatamente_na_saida(self) -> None:
        decisao = decidir(as_(12, 49))
        self.assertEqual(decisao.alarme, Alarme.TARDE)
        self.assertTrue(decisao.no_horario)

    def test_noite_nao_esta_no_horario(self) -> None:
        decisao = decidir(as_(22, 0))
        self.assertEqual(decisao.alarme, Alarme.TARDE)
        self.assertFalse(decisao.no_horario)

    def test_horarios_do_painel(self) -> None:
        def alarme(hora: int, minuto: int) -> str:
            return decidir(as_(hora, minuto), time(8, 0), time(17, 0)).alarme

        self.assertEqual(alarme(7, 59), Alarme.NENHUM)
        self.assertEqual(alarme(8, 0), Alarme.MANHA)
        self.assertEqual(alarme(16, 59), Alarme.MANHA)
        self.assertEqual(alarme(17, 0), Alarme.TARDE)


class TestEstado(unittest.TestCase):
    def setUp(self) -> None:
        self.horario = decidir(as_(7, 0))
        self.tarde_demais = decidir(as_(10, 21))
        self.nenhum = decidir(as_(6, 0))

    def test_rato_solto_no_horario(self) -> None:
        self.assertTrue(pendente(self.horario, True, False, False))

    def test_fora_do_horario_nao_solta(self) -> None:
        self.assertFalse(pendente(self.tarde_demais, True, False, False))

    def test_cacada_iniciada_continua_depois_do_horario(self) -> None:
        self.assertTrue(pendente(self.tarde_demais, True, False, True))

    def test_nada_solta_o_rato_pego_desligado_ou_sem_alarme(self) -> None:
        self.assertFalse(pendente(self.horario, True, True, True))
        self.assertFalse(pendente(self.horario, False, False, True))
        self.assertFalse(pendente(self.nenhum, True, False, True))

    def test_resumir(self) -> None:
        self.assertEqual(resumir(self.horario, False, False, False), "Alarme desligado")
        self.assertEqual(resumir(self.nenhum, True, False, False), "Rato esperando o horário")
        self.assertEqual(
            resumir(self.tarde_demais, True, False, False), "Rato esperando o horário"
        )
        self.assertEqual(
            resumir(self.horario, True, False, True), "Alarme da manhã: rato solto"
        )
        self.assertEqual(
            resumir(self.horario, True, True, False), "Alarme da manhã: rato pego"
        )
