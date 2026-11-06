#!/bin/sh
# Liga o rato, se estiver parado, e abre o painel de controle.
cd "$(dirname "$0")" || exit 1
systemctl --user start alarma-meme.service
exec .venv/bin/python -m alarma
