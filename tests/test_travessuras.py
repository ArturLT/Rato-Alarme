import random
import unittest
from urllib.parse import parse_qs, urlparse

from alarma.travessuras import MAX_JANELAS, comandos_janelas, url_youtube


def cliente(endereco: str, pid: int = 1, ws: int = 1, **extra: object) -> dict:
    return {"address": endereco, "pid": pid, "workspace": {"id": ws}, **extra}


class TestTravessuras(unittest.TestCase):
    def test_busca_de_queijo(self) -> None:
        url = urlparse(url_youtube())
        self.assertEqual(url.hostname, "www.youtube.com")
        self.assertEqual(parse_qs(url.query)["search_query"], ["vídeos de queijo"])

    def test_nunca_fecha_janela(self) -> None:
        clientes = [cliente(f"0x{i}", floating=i % 2 == 0) for i in range(6)]
        comandos = comandos_janelas(clientes, 1, 99, random.Random(1))
        self.assertEqual(len(comandos), MAX_JANELAS)
        for comando in comandos:
            self.assertIn("hl.dsp.window.move(", comando)
            self.assertNotIn("close", comando)

    def test_ignora_propria_outro_workspace_e_tela_cheia(self) -> None:
        clientes = [
            cliente("0xa", pid=99),
            cliente("0xb", ws=2),
            cliente("0xc", fullscreen=1),
        ]
        self.assertEqual(comandos_janelas(clientes, 1, 99, random.Random(1)), [])


if __name__ == "__main__":
    unittest.main()
