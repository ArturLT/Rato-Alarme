import json
import tempfile
import unittest
from datetime import time
from pathlib import Path

from alarma.config import Config, carregar, salvar


class TestConfig(unittest.TestCase):
    def setUp(self) -> None:
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.caminho = Path(pasta.name) / "sub" / "config.json"

    def escrever(self, texto: str) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self.caminho.write_text(texto, encoding="utf-8")

    def test_sem_arquivo_vale_o_padrao(self) -> None:
        self.assertEqual(carregar(self.caminho), Config())

    def test_salvar_e_carregar(self) -> None:
        config = Config(time(8, 0), time(17, 30), False, False)
        salvar(self.caminho, config)
        self.assertEqual(carregar(self.caminho), config)

    def test_salvar_recusa_entrada_depois_da_saida(self) -> None:
        with self.assertRaises(ValueError):
            salvar(self.caminho, Config(time(18, 0), time(8, 0)))
        self.assertFalse(self.caminho.exists())

    def test_arquivo_estragado_vale_o_padrao(self) -> None:
        for texto in ("{quebrado", "[1, 2]", "null"):
            self.escrever(texto)
            self.assertEqual(carregar(self.caminho), Config())

    def test_campo_invalido_nao_derruba_os_outros(self) -> None:
        self.escrever(json.dumps({"entrada": "banana", "saida": 7, "alarme_ligado": False}))
        self.assertEqual(carregar(self.caminho), Config(alarme_ligado=False))

    def test_sim_ou_nao_exige_booleano(self) -> None:
        self.escrever(json.dumps({"alarme_ligado": "false", "fechar_janela": 0}))
        self.assertEqual(carregar(self.caminho), Config())

    def test_horarios_invertidos_no_arquivo_voltam_ao_padrao(self) -> None:
        self.escrever(json.dumps({"entrada": "18:00", "saida": "08:00"}))
        self.assertEqual(carregar(self.caminho), Config())
