# Rato-Alarme

Um rato que foge pela tela até você bater o ponto. Nos horários de entrada e de saída, ele aparece, toca um alarme e apronta travessuras até ser pego com 3 cliques.

Fora do alarme, ele é um bichinho de estimação: aparece do nada, senta num canto da tela, segura plaquinhas com notícias e a previsão do tempo, conversa, traz coisas na boca, apronta e aprende com você o que pode e o que não pode fazer.

Funciona no Windows, no macOS e no Linux com Hyprland. A versão para Windows e macOS é nova e ainda está em teste.

## Instalar no Windows

Precisa do Windows 10 ou 11 de 64 bits. Não precisa de administrador.

1. Baixe `Rato-Alarme-Windows.exe` na [página de versões](https://github.com/ArturLT/Rato-Alarme/releases/latest).
2. Abra o arquivo.
3. Se aparecer o aviso "O Windows protegeu o computador", clique em **Mais informações** e depois em **Executar assim mesmo**. O aviso aparece porque o app não tem assinatura digital.
4. Siga o instalador.

O ícone do rato fica na bandeja, perto do relógio. Se não aparecer, clique na setinha **^** ao lado do relógio.

## Instalar no macOS

Precisa do macOS 14 (Sonoma) ou mais novo.

1. Na [página de versões](https://github.com/ArturLT/Rato-Alarme/releases/latest), baixe o arquivo do seu Mac:
   - Chip Apple (M1 ou mais novo): `Rato-Alarme-macOS-AppleSilicon.dmg`
   - Processador Intel: `Rato-Alarme-macOS-Intel.dmg`

   Para saber qual é o seu, abra o menu  > **Sobre Este Mac**.
2. Abra o arquivo e arraste o Rato-Alarme para a pasta **Aplicativos**.
3. Abra o Rato-Alarme. O macOS vai bloquear, porque o app não tem assinatura digital.
4. Vá em **Ajustes do Sistema > Privacidade e Segurança**, role até o aviso do Rato-Alarme e clique em **Abrir Mesmo Assim**.

O ícone do rato fica na barra de menus, no topo da tela. O app não aparece no Dock.

## Primeiro uso

Na primeira vez, o painel de controle abre sozinho. Coloque seus horários de entrada e de saída e clique em **Salvar**. Os horários padrão são 06:50 e 12:49.

Se você abrir o app até 1 hora depois de um desses horários, o rato aparece na hora.

Depois disso, o rato inicia junto com o computador e fica escondido até o próximo horário. Para desligar isso, use **Iniciar com o computador** no painel.

## Como funciona

O rato aparece no horário e foge do cursor. De tempos em tempos ele cansa e para, e fica mais fácil clicar. São 3 cliques para pegar.

Enquanto está solto, ele pode:

- abrir um bloco de notas e escrever nele;
- abrir um vídeo de queijo no navegador, no máximo uma vez por alarme;
- deixar o computador sem som. O som volta quando você pega o rato.

Se o computador ligar até 1 hora depois do horário, ele aparece assim que o programa iniciar. Depois disso, espera o próximo horário.

No Linux com Hyprland, ele também mexe e fecha janelas de outros programas. Isso não existe no Windows e no macOS.

## O rato de estimação

Toda vez que o computador liga, o rato aparece, dá oi e traz alguma coisa: a previsão do tempo, o próximo feriado, uma notícia ou um presente. Depois disso ele volta sozinho de tempos em tempos e passeia por todas as telas, inclusive de um monitor para o outro.

Quando aparece, ele pode:

- sentar e segurar uma placa com o clima, notícias, cotação do dólar, um fato do dia na história ou informações do seu computador;
- contar piadas e curiosidades, provocar, falar com carinho e perguntar coisas sobre você (e usar as respostas depois);
- repetir as frases que você ensinar;
- trazer coisas na boca e largar na tela: queijo, meia, bilhete, moeda, flor, presente, bolinha, biscoito, maçã, clipe, lápis, pena, folha, estrela, cogumelo, botão e papel. Presente, papel e estrela fazem algo quando clicados;
- aprontar: fechar uma aba do navegador, minimizar ou empurrar a janela da frente, morder e arrastar o cursor, abrir a calculadora, mandar notificações, abaixar o volume por um tempinho, escrever no bloco de notas.

São quase 180 interações. As travessuras só acontecem se estiverem liberadas em **Permissões**.

### Como brincar com ele

- **Tapa:** clique nele. Ele foge e passa a evitar o que tinha acabado de fazer. Três tapas seguidos expulsam o rato por pelo menos 20 minutos.
- **Colo:** clique e arraste. Ele fica pendurado pela nuca e cai onde você soltar.
- **Carinho:** passe o mouse por cima dele, indo e voltando, sem clicar.
- **Comida:** botão direito nele, **Dar comida**: queijo, biscoito ou maçã. A comida aparece perto do cursor e ele corre para comer.
- **Bolinha:** botão direito, **Brincar de bolinha**. Clique na bolinha para chutar; ele corre atrás.
- **♥ e ✕ no balão:** dizem se você gostou daquela fala em especial.

### Vida, fome, tédio e tristeza

O rato tem **vida**, **barriga**, **diversão** e **felicidade**. Com o tempo, barriga, diversão e felicidade caem; quando ficam baixas, ele pede comida ou brincadeira e fica tristinho. Se alguma chegar a zero, a vida começa a cair, e com vida zero **ele morre** (de fome, de tédio ou de tristeza) e deixa uma lápide na tela. No painel dá para se despedir e **adotar outro rato**, ou desligar a morte em **Início › Geral**.

O tempo só conta com o programa aberto: com o computador desligado, ele dorme.

### Aprendizado

Carinho, comida, bolinha e ♥ fazem ele repetir o que fez há pouco; tapa e ✕ fazem ele evitar. Depois de muitos tapas na mesma travessura ele desiste dela. Com a **Liberdade de escolha** alta, de vez em quando ele teima. Com carinho e comida ele sobe de nível e aprende falas novas.

### Lembretes

Em **Lembretes**, crie avisos para horários e dias da semana: beber água, pausa, alongar, almoço, remédio, reunião, ir dormir, bater o ponto, previsão do tempo, notícias do dia ou uma mensagem sua. No horário, o rato aparece com a placa (mesmo dormindo, se você quiser), toca um bipe e o computador mostra uma notificação.

### Painel do rato

O painel é todo em pixel art. No topo fica o HUD: retrato do rato, nome, humor, nível, as quatro barras e os atributos (inteligência, afeto, travessura, gula, energia). As páginas:

- **Início:** dar comida, bolinha, carinho, chamar, mandar embora, limpar a tela, pôr para dormir, e a história de vocês.
- **Personalizar:** nome, personalidade (brincalhão, curioso, carinhoso, travesso, preguiçoso), cor do pelo, roupa com estampa e cor, chapéu, cabelo e cor, coisas do rosto e do pescoço, com prévia animada.
- **Comportamento**, **Permissões**, **Falas**, **Lembretes**, **Aprendizado** e **Ponto** (o alarme de sempre).

No Mac, na primeira vez que o rato fechar uma aba, minimizar ou empurrar uma janela, o sistema pede permissão de **Acessibilidade** e de **Automação** para o Rato-Alarme. Sem ela, ele continua com o resto.

As notícias vêm do Google Notícias, o clima do Open-Meteo, as cotações da AwesomeAPI, os fatos da Wikipédia e os feriados da BrasilAPI. Nada seu é enviado.

Para ver o pet sem esperar, rode `python -m alarma --pet`.

## Menu do ícone

- **Chamar o rato**, **Dar comida**, **Brincar de bolinha**, **Tirar as coisas da tela** e **Pôr o rato para dormir** (ou **Acordar**).
- **Painel de controle:** horários do alarme e tudo do pet.
- **Sair:** encerra o rato até o próximo boot.

No Windows, um clique no ícone abre o painel, e o botão direito abre o menu. No macOS, um clique abre o menu.

Para ligar de novo depois de sair, abra o Rato-Alarme pelo menu Iniciar ou pela pasta **Aplicativos**. Abrir o app com ele já rodando mostra o painel.

## Atualizar

Quando sai uma versão nova, o ícone avisa e o menu mostra **Atualizar para a versão X**. Seus horários continuam iguais depois de atualizar.

- **Windows:** clique na opção para baixar o instalador novo e abra o arquivo. Ele troca a versão antiga.
- **macOS:** clique na opção para baixar o DMG novo, clique em **Sair** no menu e arraste o app para **Aplicativos**, escolhendo **Substituir**. Pode ser preciso liberar o app de novo em **Privacidade e Segurança**.
- **Linux:** clique na opção e ele atualiza e reinicia sozinho. Também dá para rodar `./atualizar.sh`.

Para isso, o programa consulta o GitHub de tempos em tempos. Ele não envia seus horários nem dados pessoais.

## Problemas comuns

**O rato não apareceu.** Confira no painel se **Alarme ligado** está marcado e se o horário está certo. Ele só aparece se o computador estiver ligado até 1 hora depois do horário.

**O computador ficou sem som.** O som volta quando você pega o rato ou quando o programa abre de novo. Se você mesmo tinha deixado sem som, ele continua assim.

**Abri o app e nada aconteceu.** Procure o ícone na bandeja ou na barra de menus. No Mac com muitos ícones, ele pode ficar escondido atrás do entalhe da tela.

## Remover

**Windows:** clique em **Sair** no menu do ícone. Depois, vá em **Configurações > Aplicativos > Aplicativos instalados** e desinstale o Rato-Alarme. Seus horários ficam em `%APPDATA%\alarma-meme`, e a pasta pode ser apagada à mão.

**macOS:** desmarque **Iniciar com o computador** no painel, clique em **Salvar** e depois em **Sair**. Apague o app da pasta **Aplicativos**. Seus horários ficam em `~/Library/Application Support/alarma-meme`, e a pasta pode ser apagada à mão.

## Linux

Precisa de Hyprland, PipeWire, Python 3.10 ou mais novo, Git e uma barra compatível com StatusNotifierItem.

```sh
git clone https://github.com/ArturLT/Rato-Alarme.git
cd Rato-Alarme
./instalar.sh
```

As dependências ficam em `.venv`, dentro da pasta. Se você instalar até 1 hora depois de um horário, o alarme toca na hora. Para evitar isso, use `./instalar.sh --sem-iniciar`, e ele começa só no próximo boot.

Não mova a pasta depois de instalar. Se mover, rode `./instalar.sh` de novo.

Para remover, rode `./desinstalar.sh`. A configuração fica em `~/.config/alarma-meme` e pode ser apagada à mão.

Se você instalou antes da versão 1.0.0, atualize uma vez à mão:

```sh
git pull
./instalar.sh --sem-iniciar
systemctl --user restart alarma-meme.service
```

## Publicar uma versão

1. Mude o número em `alarma/versao.py` e faça o commit.
2. Crie e envie a tag com o mesmo número:

   ```sh
   git tag v1.1.0
   git push origin main v1.1.0
   ```

O GitHub Actions roda os testes, monta os instaladores e publica o Release. Se a tag não bater com `alarma/versao.py`, nada é publicado.

## Desenvolver

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
QT_QPA_PLATFORM=offscreen .venv/bin/python -m unittest discover -s tests
```

## Para quem mexe no código

Os sprites são feitos com o [PixelFX](ferramentas/pixelfx). O rato fica em `ferramentas/pixelfx/src/fx/critters/`: `_rato.js` e `_rato-sentado.js` (o corpo), `_acessorios.js` (chapéus, cabelos, rosto e pescoço), `_itens.js` (as coisas que ele carrega) e um arquivo por animação. Depois de mudar um desenho, gere as folhas de novo:

```
node ferramentas/exportar-folhas.mjs
```

Cada folha sai com os pontos de encaixe da cabeça, do olho e do pescoço quadro a quadro e com uma máscara do tronco; o app usa isso para vestir o rato (`alarma/aparencia.py`).

Testes: `python -m unittest discover -s tests`.

Gerar o app e o DMG no Mac: `bash empacotar/gerar-dmg-mac.sh`.

Subir esta pasta para o GitHub (ela veio de um .zip, sem git): `bash ferramentas/preparar-github.sh`. O script liga a pasta ao repositório, cria a branch `pet-pixel-art` com um commit e mostra o comando de push.
