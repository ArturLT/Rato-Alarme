import unittest
from unittest import mock

from alarma import acoes


class TestAcoes(unittest.TestCase):
    def test_reconhece_navegadores(self) -> None:
        self.assertTrue(acoes.eh_navegador("Notícias - Google Chrome"))
        self.assertTrue(acoes.eh_navegador("firefox"))
        self.assertFalse(acoes.eh_navegador("Visual Studio Code"))

    def test_script_do_chrome_nao_fecha_a_ultima_aba(self) -> None:
        script = acoes.script_fechar_aba_mac("Google Chrome")
        self.assertIn("count of tabs of front window) > 1", script)
        self.assertIn("close active tab", script)
        self.assertIn("close current tab", acoes.script_fechar_aba_mac("Safari"))
        self.assertIn('keystroke "w"', acoes.script_fechar_aba_mac("Firefox"))
        self.assertIsNone(acoes.script_fechar_aba_mac("Pages"))

    def test_nao_fecha_nada_fora_do_navegador_no_mac(self) -> None:
        with mock.patch("sys.platform", "darwin"), mock.patch.object(acoes, "_osascript", side_effect=["Pages"]) as osa:
            self.assertFalse(acoes.fechar_aba())
        self.assertEqual(osa.call_count, 1)

    def test_nao_minimiza_o_proprio_rato(self) -> None:
        with mock.patch("sys.platform", "darwin"), mock.patch.object(acoes, "_osascript", side_effect=["Python"]) as osa:
            self.assertFalse(acoes.minimizar())
        self.assertEqual(osa.call_count, 1)

    def test_minimiza_a_janela_da_frente_no_mac(self) -> None:
        with mock.patch("sys.platform", "darwin"), mock.patch.object(acoes, "_osascript", side_effect=["Notes", ""]) as osa:
            self.assertTrue(acoes.minimizar())
        self.assertIn("AXMinimized", osa.call_args_list[1].args[0])

    def test_voz(self) -> None:
        self.assertEqual(acoes.comando_voz("oi  tudo bem", "darwin"), ["say", "-v", "Luciana", "oi tudo bem"])
        self.assertIn("Speak('d''água')", acoes.comando_voz("d'água", "win32")[-1])

    def test_erro_nunca_derruba(self) -> None:
        with mock.patch("sys.platform", "darwin"), mock.patch.object(acoes, "_osascript", side_effect=RuntimeError):
            self.assertFalse(acoes.fechar_aba())
            self.assertFalse(acoes.minimizar())
