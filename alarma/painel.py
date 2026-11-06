"""Painel de controle. Só grava o arquivo de configuração: o rato e a bandeja releem."""

from datetime import time

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

from alarma import config

APP_ID = "meme.alarma.painel"


def _campo_hora(hora: time) -> tuple[Gtk.Box, Gtk.SpinButton, Gtk.SpinButton]:
    horas = Gtk.SpinButton.new_with_range(0, 23, 1)
    minutos = Gtk.SpinButton.new_with_range(0, 59, 1)
    horas.set_value(hora.hour)
    minutos.set_value(hora.minute)
    for campo in (horas, minutos):
        campo.set_wrap(True)
        campo.set_orientation(Gtk.Orientation.VERTICAL)
        campo.connect("output", _dois_digitos)
    caixa = Gtk.Box(spacing=6, halign=Gtk.Align.END)
    caixa.append(horas)
    caixa.append(Gtk.Label(label=":"))
    caixa.append(minutos)
    return caixa, horas, minutos


def _dois_digitos(campo: Gtk.SpinButton) -> bool:
    campo.set_text(f"{campo.get_value_as_int():02d}")
    return True


def _rotulo(texto: str, dica: str) -> Gtk.Box:
    caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, valign=Gtk.Align.CENTER, hexpand=True)
    caixa.append(Gtk.Label(label=texto, xalign=0))
    detalhe = Gtk.Label(label=dica, xalign=0, wrap=True, max_width_chars=38)
    detalhe.add_css_class("dim-label")
    caixa.append(detalhe)
    return caixa


class Painel(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(application_id=APP_ID)
        self._janela: Gtk.ApplicationWindow | None = None

    def do_activate(self) -> None:
        if self._janela is not None:
            self._janela.present()
            return

        atual = config.carregar(config.caminho_padrao())
        entrada, self._entrada_h, self._entrada_m = _campo_hora(atual.entrada)
        saida, self._saida_h, self._saida_m = _campo_hora(atual.saida)
        self._alarme = Gtk.Switch(active=atual.alarme_ligado, valign=Gtk.Align.CENTER)
        self._fechar = Gtk.Switch(active=atual.fechar_janela, valign=Gtk.Align.CENTER)
        self._alarme.set_halign(Gtk.Align.END)
        self._fechar.set_halign(Gtk.Align.END)

        grade = Gtk.Grid(row_spacing=16, column_spacing=24)
        linhas = (
            ("Horário de entrada", "Nessa hora o rato aparece e toca o alarme.", entrada),
            ("Horário de saída", "Nessa hora o rato aparece de novo.", saida),
            ("Alarme ligado", "Desligado, o rato some e não volta até você ligar de novo.", self._alarme),
            ("Rato pode fechar janelas", "Desligado, ele continua com as outras travessuras.", self._fechar),
        )
        for linha, (texto, dica, controle) in enumerate(linhas):
            grade.attach(_rotulo(texto, dica), 0, linha, 1, 1)
            grade.attach(controle, 1, linha, 1, 1)

        self._aviso = Gtk.Label(xalign=0, hexpand=True, wrap=True)
        salvar = Gtk.Button(label="Salvar")
        salvar.add_css_class("suggested-action")
        salvar.connect("clicked", self._salvar)
        rodape = Gtk.Box(spacing=12)
        rodape.append(self._aviso)
        rodape.append(salvar)

        corpo = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=20,
            margin_top=20,
            margin_bottom=20,
            margin_start=20,
            margin_end=20,
        )
        corpo.append(grade)
        corpo.append(rodape)

        self._janela = Gtk.ApplicationWindow(
            application=self, title="Rato-Alarme", resizable=False, child=corpo
        )
        self._janela.present()

    def _salvar(self, *_args: object) -> None:
        novo = config.Config(
            time(self._entrada_h.get_value_as_int(), self._entrada_m.get_value_as_int()),
            time(self._saida_h.get_value_as_int(), self._saida_m.get_value_as_int()),
            self._alarme.get_active(),
            self._fechar.get_active(),
        )
        try:
            config.salvar(config.caminho_padrao(), novo)
        except ValueError:
            self._aviso.set_label("A entrada precisa ser antes da saída.")
        except OSError:
            self._aviso.set_label("Não consegui salvar a configuração.")
        else:
            self._aviso.set_label("Salvo.")


def main() -> int:
    return Painel().run(None)


if __name__ == "__main__":
    raise SystemExit(main())
