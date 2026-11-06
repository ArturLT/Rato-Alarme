#!/bin/sh
# Liga o rato e a bandeja, se estiverem parados, e abre o painel de controle.
cd "$(dirname "$0")" || exit 1
systemctl --user start alarma-meme.service alarma-meme-bandeja.service
exec /usr/bin/python3 -m alarma.painel
