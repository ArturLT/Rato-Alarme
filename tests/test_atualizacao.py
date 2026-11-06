import io
import json
import unittest
from unittest import mock

from alarma import atualizacao
from alarma.atualizacao import interpretar, mais_nova, nome_do_instalador

PAGINA = "https://github.com/ArturLT/Rato-Alarme/releases/tag/v1.2.0"


def _release(tag: str = "v1.2.0", **extra: object) -> dict:
    nomes = (
        "Rato-Alarme-Windows.exe",
        "Rato-Alarme-macOS-AppleSilicon.dmg",
        "Rato-Alarme-macOS-Intel.dmg",
    )
    return {
        "tag_name": tag,
        "html_url": PAGINA,
        "assets": [{"name": n, "browser_download_url": f"https://d/{n}"} for n in nomes],
        **extra,
    }


class TestVersoes(unittest.TestCase):
    def test_compara_numeros_e_nao_texto(self) -> None:
        self.assertTrue(mais_nova("v1.10.0", "1.9.0"))
        self.assertFalse(mais_nova("v1.9.0", "1.10.0"))

    def test_mesma_versao_nao_e_nova(self) -> None:
        self.assertFalse(mais_nova("v1.0.0", "1.0.0"))

    def test_tag_estranha_e_ignorada(self) -> None:
        for tag in ("nightly", "v1.0-beta", "", None, 3):
            self.assertFalse(mais_nova(tag, "1.0.0"), tag)


class TestInterpretar(unittest.TestCase):
    def test_escolhe_o_instalador_de_cada_sistema(self) -> None:
        casos = (
            ("win32", "AMD64", "Rato-Alarme-Windows.exe"),
            ("darwin", "arm64", "Rato-Alarme-macOS-AppleSilicon.dmg"),
            ("darwin", "x86_64", "Rato-Alarme-macOS-Intel.dmg"),
        )
        for sistema, maquina, nome in casos:
            achado = interpretar(_release(), "1.0.0", sistema, maquina)
            self.assertEqual(achado.download, f"https://d/{nome}")
            self.assertEqual(achado.versao, "1.2.0")

    def test_linux_nao_tem_instalador(self) -> None:
        self.assertIsNone(nome_do_instalador("linux", "x86_64"))
        achado = interpretar(_release(), "1.0.0", "linux", "x86_64")
        self.assertIsNone(achado.download)
        self.assertEqual(achado.pagina, PAGINA)

    def test_sem_o_instalador_ainda_avisa_com_a_pagina(self) -> None:
        achado = interpretar(_release(assets=[]), "1.0.0", "win32", "AMD64")
        self.assertIsNone(achado.download)

    def test_ignora_o_que_nao_e_novo_ou_esta_em_teste(self) -> None:
        self.assertIsNone(interpretar(_release("v1.0.0"), "1.0.0", "win32", "AMD64"))
        self.assertIsNone(interpretar(_release(prerelease=True), "1.0.0", "win32", "AMD64"))
        self.assertIsNone(interpretar(_release(draft=True), "1.0.0", "win32", "AMD64"))

    def test_resposta_estragada_nao_quebra(self) -> None:
        for dados in (None, [], {"tag_name": "v9.0.0"}, {"message": "rate limit"}):
            self.assertIsNone(interpretar(dados, "1.0.0", "win32", "AMD64"))


class TestBuscar(unittest.TestCase):
    def test_sem_internet_fica_tudo_como_esta(self) -> None:
        with mock.patch("urllib.request.urlopen", side_effect=OSError):
            self.assertIsNone(atualizacao.buscar("win32", "AMD64"))

    def test_json_invalido_fica_tudo_como_esta(self) -> None:
        with mock.patch("urllib.request.urlopen", return_value=io.BytesIO(b"<html>")):
            self.assertIsNone(atualizacao.buscar("win32", "AMD64"))

    def test_acha_a_versao_e_se_identifica_sem_dados_pessoais(self) -> None:
        corpo = io.BytesIO(json.dumps(_release("v99.0.0")).encode())
        with mock.patch("urllib.request.urlopen", return_value=corpo) as abrir:
            achado = atualizacao.buscar("win32", "AMD64")
        self.assertEqual(achado.versao, "99.0.0")
        pedido = abrir.call_args.args[0]
        self.assertTrue(pedido.get_header("User-agent").startswith("Rato-Alarme/"))
