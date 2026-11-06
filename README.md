# Rato-Alarme

Um rato que foge pela tela até você bater o ponto. Ele aparece nos horários de entrada e de saída, toca um alarme e apronta travessuras até ser pego com 3 cliques. Se o computador ligar até 1 hora depois do horário, ele aparece assim que o programa iniciar. Depois disso, espera o próximo horário.

## Requisitos

Funciona só no Linux, com Hyprland e PipeWire. A bandeja precisa de uma barra compatível com StatusNotifierItem.

No Arch:

```sh
sudo pacman -S git python-gobject gtk4 libayatana-appindicator
```

## Instalar

```sh
git clone https://github.com/ArturLT/Rato-Alarme.git
cd Rato-Alarme
./instalar.sh
```

O rato passa a iniciar com o computador e o ícone dele aparece na bandeja. Se você instalar até 1 hora depois de um horário, o alarme toca na hora. Para evitar isso, use `./instalar.sh --sem-iniciar`, e ele começa só no próximo boot.

Não mova a pasta depois de instalar. Se mover, rode `./instalar.sh` de novo.

## Usar

Clique no ícone da bandeja para ver o estado do alarme e abrir o menu:

- **Painel de controle:** muda os horários de entrada e saída, desliga o alarme e impede o rato de fechar janelas.
- **Sair:** encerra o rato e a bandeja até o próximo boot.

Para ligar de novo depois de sair, abra **Rato-Alarme** no menu de aplicativos.

## Desinstalar

```sh
./desinstalar.sh
```

A configuração fica em `~/.config/alarma-meme` e pode ser apagada à mão.
