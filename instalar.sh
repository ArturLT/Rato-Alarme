#!/bin/bash
# Instala o Rato-Alarme para o usuário atual, sem sudo.
# Use --sem-iniciar para só deixar pronto para o próximo boot.
set -eu

PASTA="$(cd "$(dirname "$0")" && pwd)"
UNIDADES="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
ATALHOS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
SERVICOS="alarma-meme.service alarma-meme-bandeja.service"

faltando=""
for comando in systemctl hyprctl wpctl pw-play flock xdg-open; do
    command -v "$comando" >/dev/null || faltando="$faltando $comando"
done
/usr/bin/python3 -c "
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk" 2>/dev/null || faltando="$faltando gtk4/python-gobject"
/usr/bin/python3 -c "
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')
from gi.repository import Gtk, AyatanaAppIndicator3" 2>/dev/null || faltando="$faltando libayatana-appindicator"
if [ -n "$faltando" ]; then
    echo "Falta instalar:$faltando" >&2
    exit 1
fi

mkdir -p "$UNIDADES" "$ATALHOS"

cat >"$UNIDADES/alarma-meme.service" <<UNIDADE
[Unit]
Description=Criatura do alarme do ponto
PartOf=graphical-session.target
After=graphical-session.target
StartLimitIntervalSec=0

[Service]
ExecStart=/bin/sh "$PASTA/vigia.sh"
Restart=always
RestartSec=1

[Install]
WantedBy=graphical-session.target
UNIDADE

cat >"$UNIDADES/alarma-meme-bandeja.service" <<UNIDADE
[Unit]
Description=Ícone do Rato-Alarme na bandeja
PartOf=graphical-session.target
After=graphical-session.target
StartLimitIntervalSec=0

[Service]
WorkingDirectory=$PASTA
ExecStart=/usr/bin/python3 -m alarma.bandeja
Restart=on-failure
RestartSec=2

[Install]
WantedBy=graphical-session.target
UNIDADE

cat >"$ATALHOS/rato-alarme.desktop" <<ATALHO
[Desktop Entry]
Type=Application
Name=Rato-Alarme
Comment=Liga o alarme e abre o painel de controle
Exec="$PASTA/abrir.sh"
Icon=$PASTA/alarma/icones/rato-alarme.png
Terminal=false
Categories=Utility;
ATALHO

chmod +x "$PASTA/abrir.sh"
systemctl --user daemon-reload
systemctl --user enable $SERVICOS

if [ "${1:-}" = "--sem-iniciar" ]; then
    echo "Instalado. O Rato-Alarme começa no próximo boot."
else
    systemctl --user start $SERVICOS
    echo "Instalado e ligado. Procure o rato na bandeja."
fi
