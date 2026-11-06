import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path
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
        "assets": [
            {"name": n, "browser_download_url": f"https://d/{n}", "digest": f"sha256:{n}"}
            for n in nomes
        ],
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
            self.assertEqual(achado.resumo, f"sha256:{nome}")
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


class _Resposta(io.BytesIO):
    def __init__(self, conteudo: bytes) -> None:
        super().__init__(conteudo)
        self.headers = {"Content-Length": str(len(conteudo))}


class TestBaixar(unittest.TestCase):
    CONTEUDO = b"instalador" * 1000

    def setUp(self) -> None:
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.destino = Path(pasta.name) / "sub" / "i.exe"

    def _baixar(self, resumo: str | None, conteudo: bytes | None = None) -> list[int]:
        lancamento = atualizacao.Lancamento("1.2.0", "https://p", "https://d/i.exe", resumo)
        passos: list[int] = []
        resposta = _Resposta(self.CONTEUDO if conteudo is None else conteudo)
        with mock.patch("urllib.request.urlopen", return_value=resposta):
            atualizacao.baixar(lancamento, self.destino, passos.append)
        return passos

    def _resumo(self) -> str:
        return "sha256:" + hashlib.sha256(self.CONTEUDO).hexdigest()

    def test_arquivo_conferido_fica_no_destino(self) -> None:
        passos = self._baixar(self._resumo())
        self.assertEqual(self.destino.read_bytes(), self.CONTEUDO)
        self.assertEqual(passos[-1], 100)

    def test_arquivo_diferente_do_publicado_e_apagado(self) -> None:
        with self.assertRaises(ValueError):
            self._baixar(self._resumo(), b"adulterado")
        self.assertEqual(list(self.destino.parent.iterdir()), [])

    def test_sem_resumo_nem_tenta_baixar(self) -> None:
        with self.assertRaises(ValueError):
            self._baixar(None)
        self.assertFalse(self.destino.exists())
