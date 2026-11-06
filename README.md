# Rato-Alarme

Um rato que foge pela tela até você bater o ponto. Nos horários de entrada e de saída, ele aparece, toca um alarme e apronta travessuras até ser pego com 3 cliques.

Fora do alarme, ele é um bichinho de estimação: aparece do nada, senta num canto da tela, segura plaquinhas com notícias e a previsão do tempo, conversa, traz coisas na boca, apronta e aprende com você o que pode e o que não pode fazer.

Funciona no Windows, no macOS e no Linux com Hyprland. A versão para Windows e macOS é nova e ainda está em teste.

## Instalar no Windows

Precisa do Windows 10 ou 11 de 64 bits. Não precisa de administrador.

1. Baixe `Rato-Alarme-Windows.exe` na [página de versões](https://github.com/ArturLT/Rato-Alarme/releases/latest).
2. Abra o arquivo.
3. Se aparecer o aviso "O Windows protegeu o computador", clique em **Mais informações** e depois em **Executar assim mesmo**. O aviso aparece porque o app não tem assinatura digital.
4. Siga o instalador. Ele sugere uma pasta, e você pode clicar em **Procurar** para escolher outra. Use uma pasta em que sua conta possa gravar: `Arquivos de Programas`, por exemplo, exige administrador.

As atualizações usam a mesma pasta. Para trocar de pasta depois, desinstale e instale de novo. Seus horários continuam salvos.

O ícone do rato fica na bandeja, perto do relógio. Se não aparecer, clique na setinha **^** ao lado do relógio.

## Instalar no macOS

Precisa do macOS 14 (Sonoma) ou mais novo.

1. Na [página de versões](https://github.com/ArturLT/Rato-Alarme/releases/latest), baixe o arquivo do seu Mac:
   - Chip Apple (M1 ou mais novo): `Rato-Alarme-macOS-AppleSilicon.dmg`
   - Processador Intel: `Rato-Alarme-macOS-Intel.dmg`

   Para saber qual é o seu, abra o menu  > **Sobre Este Mac**.
2. Abra o arquivo e arraste o Rato-Alarme para a pasta **Aplicativos** ou para outra pasta do Mac. Não abra o app direto do arquivo baixado.
3. Abra o Rato-Alarme. O macOS vai bloquear, porque o app não tem assinatura digital.
4. Vá em **Ajustes do Sistema > Privacidade e Segurança**, role até o aviso do Rato-Alarme e clique em **Abrir Mesmo Assim**.

O ícone do rato fica na barra de menus, no topo da tela. O app não aparece no Dock.

## Primeiro uso

Na primeira vez, o painel de controle abre sozinho. Coloque seus horários de entrada e de saída e clique em **Salvar**. Os horários padrão são 06:50 e 12:49.

Se você abrir o app entre a entrada e a saída, ou até 1 hora depois da saída, o rato aparece na hora.

Depois disso, o rato inicia junto com o computador e fica escondido até o próximo horário. Para desligar isso, use **Iniciar com o computador** no painel.

## Como funciona

O rato aparece no horário e foge do cursor. De tempos em tempos ele cansa e para, e fica mais fácil clicar. Ele também para de correr para reclamar do computador e do seu atraso em um balão de fala. Um clique nessa hora conta como acerto, interrompe a fala e ele volta a fugir. São 3 cliques para pegar.

Enquanto está solto, ele pode:

- abrir um bloco de notas e escrever nele;
- abrir um vídeo de queijo no navegador, no máximo uma vez por alarme;
- deixar o computador sem som. O som volta quando você pega o rato.

Se você se atrasar, o rato da entrada aparece assim que o programa iniciar, a qualquer momento antes da saída. O rato da saída aparece se o computador ligar até 1 hora depois do horário. Depois disso, ele espera o dia seguinte.

Se você mudar um horário para mais tarde no painel, o rato aparece no horário novo, mesmo que já tenha sido pego naquele dia.

No Linux com Hyprland, ele também mexe e fecha janelas de outros programas. Isso não existe no Windows e no macOS.

## O rato de estimação

Toda vez que o computador liga, o rato aparece, dá oi e traz alguma coisa: a previsão do tempo, o próximo feriado, uma notícia ou um presente. Depois disso ele volta sozinho de tempos em tempos.

Quando aparece, ele pode:

- sentar e segurar uma placa com o clima, notícias, cotação do dólar, um fato do dia na história ou informações do seu computador (bateria, memória, disco, há quanto tempo está ligado);
- contar piadas e curiosidades, fazer provocações e falar com carinho;
- perguntar coisas sobre você (nome, comida favorita, time...) e usar as respostas depois;
- repetir as frases que você ensinar no painel;
- trazer queijo, meia, bilhete, moeda ou flor na boca e largar na tela (clique neles para sumirem);
- fechar uma aba do navegador, minimizar a janela da frente, morder e arrastar o cursor, escrever no bloco de notas ou abrir um vídeo de queijo.

São mais de 150 interações. As travessuras só acontecem se estiverem liberadas na aba **Permissões** do painel.

### Como ensinar o rato

- **Tapa:** clique nele. Ele foge e passa a evitar o que tinha acabado de fazer. Três tapas seguidos expulsam o rato por pelo menos 20 minutos.
- **Carinho:** passe o mouse por cima dele, indo e voltando, sem clicar. Ele fica feliz e repete mais o que fez há pouco.
- **Queijo:** botão direito nele, **Dar queijo**. Vale mais que carinho.
- **♥ e ✕ no balão:** dizem se você gostou daquela fala em especial.

Com carinho e queijo ele sobe de nível e aprende falas novas. Depois de muitos tapas na mesma travessura ele desiste dela e às vezes avisa que lembrou que você não gosta. Com a **Liberdade de escolha** alta, de vez em quando ele teima. Tudo o que ele aprendeu aparece na aba **Aprendizado**, com um botão para ele esquecer tudo.

### Painel do pet

- **Rato:** chamar agora, dar queijo, mandar embora, tirar as coisas da tela e **pôr para dormir** (30 minutos, 1 hora, 3 horas, até amanhã ou até você acordar). Dormindo, ele não apronta nada.
- **Comportamento:** intensidade (de quanto em quanto tempo ele aparece), travessura (quantas das coisas que ele faz são travessuras) e liberdade de escolha.
- **Permissões:** internet, falar em voz alta e cada travessura.
- **Falas:** o que ele pode dizer, a cidade do clima, as frases que você ensinou e o que ele sabe de você.

No Mac, na primeira vez que o rato fechar uma aba ou minimizar uma janela, o sistema pede permissão de **Acessibilidade** e de **Automação** para o Rato-Alarme. Sem ela, ele continua com o resto.

As notícias vêm do Google Notícias, o clima do Open-Meteo, as cotações da AwesomeAPI, os fatos da Wikipédia e os feriados da BrasilAPI. A cidade é descoberta pelo endereço de internet, a não ser que você escreva uma no painel. Nada seu é enviado.

Para ver o pet sem esperar, rode `python -m alarma --pet`.

## Menu do ícone

- **Chamar o rato**, **Dar queijo** e **Pôr o rato para dormir** (ou **Acordar**).
- **Painel de controle:** horários do alarme e tudo do pet.
- **Sair:** encerra o rato até o próximo boot.

No Windows, um clique no ícone abre o painel, e o botão direito abre o menu. No macOS, um clique abre o menu.

Para ligar de novo depois de sair, abra o Rato-Alarme pelo menu Iniciar ou pela pasta onde ele está no Mac. Abrir o app com ele já rodando mostra o painel.

## Atualizar

Quando sai uma versão nova, uma janela aparece na tela. Clique em **Atualizar agora**: o programa baixa a versão nova, instala e reabre sozinho. Seus horários continuam iguais.

Se clicar em **Depois**, a opção **Atualizar para a versão X** fica no menu do ícone e a janela volta na próxima vez que o programa abrir.

Quem está na versão 1.0.0 precisa instalar a versão seguinte à mão, pelo instalador do [Release](https://github.com/ArturLT/Rato-Alarme/releases/latest). Depois disso as atualizações são automáticas.

No Mac, a atualização automática precisa de uma conta com permissão de escrita na pasta onde o app está. Sem isso, o instalador abre no navegador. No Linux, também dá para rodar `./atualizar.sh`.

Para isso, o programa consulta o GitHub de tempos em tempos. Ele não envia seus horários nem dados pessoais.

## Problemas comuns

**O rato não apareceu.** Confira no painel se **Alarme ligado** está marcado e se o horário está certo. Ele só aparece se o computador estiver ligado entre a entrada e a saída, ou até 1 hora depois da saída.

**O computador ficou sem som.** O som volta quando você pega o rato ou quando o programa abre de novo. Se você mesmo tinha deixado sem som, ele continua assim.

**Abri o app e nada aconteceu.** Procure o ícone na bandeja ou na barra de menus. No Mac com muitos ícones, ele pode ficar escondido atrás do entalhe da tela.

## Remover

**Windows:** clique em **Sair** no menu do ícone. Depois, vá em **Configurações > Aplicativos > Aplicativos instalados** e desinstale o Rato-Alarme. Seus horários ficam em `%APPDATA%\alarma-meme`, e a pasta pode ser apagada à mão.

**macOS:** desmarque **Iniciar com o computador** no painel, clique em **Salvar** e depois em **Sair**. Apague o app da pasta onde ele está. Seus horários ficam em `~/Library/Application Support/alarma-meme`, e a pasta pode ser apagada à mão.

## Linux

Precisa de Hyprland, PipeWire, Python 3.10 ou mais novo, Git e uma barra compatível com StatusNotifierItem.

```sh
git clone https://github.com/ArturLT/Rato-Alarme.git
cd Rato-Alarme
./instalar.sh
```

O programa fica na pasta em que você rodar o `git clone`, então escolha o local antes. As dependências ficam em `.venv`, dentro dela. Se você instalar entre a entrada e a saída, ou até 1 hora depois da saída, o alarme toca na hora. Para evitar isso, use `./instalar.sh --sem-iniciar`, e ele começa só no próximo boot.

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

Os sprites são feitos com o [PixelFX](ferramentas/pixelfx). As poses do pet ficam em `ferramentas/pixelfx/src/fx/critters/` (`_rato-sentado.js`, `_itens.js`, `rato-*.js` e `objeto-tela.js`). Depois de mudar um desenho, gere as folhas de novo:

```
node ferramentas/exportar-folhas.mjs
```
