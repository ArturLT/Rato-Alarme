import random
import unittest
from datetime import datetime, time

from alarma import falas
from alarma.logica import Alarme


class TestAtraso(unittest.TestCase):
    def test_conta_os_minutos_depois_do_horario(self) -> None:
        agora = datetime(2026, 11, 6, 8, 5)
        self.assertEqual(falas.minutos_de_atraso(agora, time(6, 50)), 75)

    def test_antes_do_horario_nao_ha_atraso(self) -> None:
        agora = datetime(2026, 11, 6, 6, 0)
        self.assertEqual(falas.minutos_de_atraso(agora, time(6, 50)), 0)

    def test_por_extenso(self) -> None:
        for minutos, texto in (
            (1, "1 minuto"),
            (25, "25 minutos"),
            (60, "1 hora"),
            (61, "1 hora e 1 minuto"),
            (125, "2 horas e 5 minutos"),
        ):
            self.assertEqual(falas.por_extenso(minutos), texto)


class TestSorteio(unittest.TestCase):
    def test_sem_atraso_nao_cita_minutos(self) -> None:
        for alarme in (Alarme.MANHA, Alarme.TARDE):
            for frase in falas.pontualidade(alarme, 0):
                self.assertNotIn("minuto", frase)
                self.assertNotIn("{", frase)

    def test_com_atraso_cita_o_tempo_real(self) -> None:
        frases = falas.pontualidade(Alarme.MANHA, 12)
        self.assertTrue(any("12 minutos" in f for f in frases))
        self.assertFalse(any("{" in f for f in frases))

    def test_cada_alarme_fala_do_seu_ponto(self) -> None:
        self.assertNotEqual(falas.pontualidade(Alarme.MANHA, 5), falas.pontualidade(Alarme.TARDE, 5))

    def test_nunca_repete_a_ultima_e_usa_os_dois_temas(self) -> None:
        acaso = random.Random(1)
        ultima, vistas = "", []
        for _ in range(300):
            frase = falas.sortear(acaso, Alarme.MANHA, 10, ultima)
            self.assertNotEqual(frase, ultima)
            ultima = frase
            vistas.append(frase)
        self.assertTrue(set(vistas) & set(falas.COMPUTADOR))
        self.assertTrue(set(vistas) & set(falas.pontualidade(Alarme.MANHA, 10)))
