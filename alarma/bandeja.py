"""Ícone na bandeja: mostra o estado do alarme, abre o painel e encerra tudo.

Processo separado do rato porque o AppIndicator usa GTK3 e o rato usa GTK4,
e os dois não carregam juntos. Lê o estado dos arquivos, sem falar com o rato.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("AyatanaAppIndicator3", "0.1")
from gi.repository import AyatanaAppIndicator3 as AppIndicator
from gi.repository import GLib, Gtk

from alarma import config, travessuras
from alarma.logica import decidir, pendente, resumir
from alarma.registro import DISPARADO, PEGO, Registro, caminho_mudo, caminho_padrao

RAIZ = Path(__file__).parent.parent
ICONES = Path(__file__).parent / "icones"
ICONE_CALMO = "rato-alarme"
ICONE_SOLTO = "rato-alarme-solto"
SERVICO_RATO = "alarma-meme.service"
ATUALIZAR_S = 5


class Bandeja:
    def __init__(self) -> None:
        self._indicador = AppIndicator.Indicator.new(
            "alarma-meme", ICONE_CALMO, AppIndicator.IndicatorCategory.APPLICATION_STATUS
        )
        self._indicador.set_icon_theme_path(str(ICONES))
        self._indicador.set_title("Rato-Alarme")

        menu = Gtk.Menu()
        self._estado = Gtk.MenuItem()
        self._estado.set_sensitive(False)
        painel = Gtk.MenuItem(label="Painel de controle")
        painel.connect("activate", self._abrir_painel)
        sair = Gtk.MenuItem(label="Sair")
        sair.connect("activate", self._sair)
        for item in (self._estado, Gtk.SeparatorMenuItem(), painel, sair):
            menu.append(item)
        menu.show_all()
        self._indicador.set_menu(menu)
        self._indicador.set_status(AppIndicator.IndicatorStatus.ACTIVE)

        self._atualizar()
        GLib.timeout_add_seconds(ATUALIZAR_S, self._atualizar)

    def _atualizar(self) -> bool:
        preferencias = config.carregar(config.caminho_padrao())
        decisao = decidir(
            datetime.now().astimezone(), preferencias.entrada, preferencias.saida
        )
        dia = decisao.agora.date().isoformat()
        registro = Registro(caminho_padrao())
        pego = registro.tem(dia, decisao.alarme, PEGO)
        disparado = registro.tem(dia, decisao.alarme, DISPARADO)
        solto = pendente(decisao, preferencias.alarme_ligado, pego, disparado)
        texto = resumir(decisao, preferencias.alarme_ligado, pego, solto)
        self._estado.set_label(texto)
        self._indicador.set_icon_full(ICONE_SOLTO if solto else ICONE_CALMO, texto)
        return True

    def _abrir_painel(self, *_args: object) -> None:
        subprocess.Popen([sys.executable, "-m", "alarma.painel"], cwd=RAIZ)

    def _sair(self, *_args: object) -> None:
        """Encerra até o próximo boot. O início automático continua habilitado."""
        try:
            subprocess.run(["systemctl", "--user", "stop", SERVICO_RATO], timeout=15)
        except (OSError, subprocess.TimeoutExpired):
            pass
        travessuras.restaurar_som(caminho_mudo())
        Gtk.main_quit()


def main() -> int:
    Bandeja()
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
