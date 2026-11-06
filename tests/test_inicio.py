import plistlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from alarma import inicio


class TestInicio(unittest.TestCase):
    def test_codigo_fonte_nunca_se_registra(self) -> None:
        with mock.patch("sys.platform", "darwin"):
            self.assertFalse(inicio.gerenciado())

    def test_linux_fica_com_o_instalador(self) -> None:
        with mock.patch("sys.platform", "linux"), mock.patch("sys.frozen", True, create=True):
            self.assertFalse(inicio.gerenciado())

    def test_agente_do_mac_sobe_no_login_e_respeita_o_sair(self) -> None:
        agente = inicio.agente_mac("/Applications/Rato-Alarme.app/Contents/MacOS/Rato-Alarme")
        self.assertEqual(agente["ProgramArguments"][1], "--boot")
        self.assertTrue(agente["RunAtLoad"])
        self.assertEqual(agente["KeepAlive"], {"SuccessfulExit": False})

    def test_mac_liga_e_desliga(self) -> None:
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        arquivo = Path(pasta.name) / "LaunchAgents" / "meme.alarma.plist"
        with (
            mock.patch("sys.platform", "darwin"),
            mock.patch("sys.frozen", True, create=True),
            mock.patch("alarma.inicio.caminho_mac", return_value=arquivo),
        ):
            inicio.aplicar(True)
            self.assertEqual(plistlib.loads(arquivo.read_bytes())["Label"], "meme.alarma")
            inicio.aplicar(False)
            self.assertFalse(arquivo.exists())
            inicio.aplicar(False)
