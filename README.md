# Pixel Aim Lab

**Overlay e trigger por cor no Windows.** O programa captura a janela em foco, encontra áreas amarelas, roxas ou vermelhas e desenha caixas transparentes sobre elas. O modo de disparo é opcional.

![Demo com caixas de detecção ao redor dos três alvos](demo.png)

| Perfil | Alvo de exemplo | Detecção |
| --- | --- | --- |
| `amarelo` | `#FFD51C` | Amarelo saturado |
| `roxo` | `#A63FFF` | Violeta e roxo saturados |
| `vermelho` | `#F02B3E` | As duas pontas da escala de matiz |

## Trigger na área de trabalho

Com as dependências instaladas, abra **`Trigger-Amarelo.cmd`**. Aponte para uma área neutra, segure **F8** e passe sobre um elemento amarelo. O programa envia um clique esquerdo no ponto atual do cursor. Para outro clique, saia da cor e entre novamente. **F9** encerra. Esse modo atua no navegador e na área de trabalho, então escolha uma área de teste sem botões ou links importantes.

```powershell
py -3 desktop.py --trigger --colors amarelo roxo vermelho
```

Sem `--trigger`, o terminal apenas registra a cor encontrada. O modo área de trabalho usa `GetPixel` e roda como processo externo, separado dos aplicativos que você usa.

## Overlay com mira central

Use Python 3.10+ no Windows. Na pasta do projeto, instale as dependências e abra a demo:

```powershell
py -3 -m pip install -r requirements.txt
py -3 demo.py
```

Em outro terminal, inicie o overlay e volte à janela da demo:

```powershell
py -3 overlay.py --window "Pixel Aim Lab Demo" --colors amarelo roxo vermelho --trigger
```

- **F8 pressionado** habilita o clique enquanto uma região aceita estiver sob a mira central. Mantenha o cursor dentro da demo para ver o contador subir. Em jogos que usam a mira central, a entrada segue o comportamento do jogo.
- **F9** fecha o overlay. Sem `--trigger`, o programa só desenha e sinaliza quando o centro está sobre um alvo.
- `--min-area 100` descarta componentes menores. `--cooldown 250` aumenta o intervalo mínimo entre os cliques, em milissegundos.

## Compatibilidade

Para outra janela, passe o título exato em `--window` e comece no modo visual, com um único perfil. Use janela ou tela cheia sem bordas. O método depende das cores renderizadas e da captura do Windows. HUDs com a mesma cor podem gerar caixas falsas. Alvos escondidos ficam fora da detecção, e a automação pode ser ignorada por alguns aplicativos. Use o trigger em ambientes próprios ou de treino local autorizados.

## Como funciona

1. Pillow captura a área cliente da janela selecionada. O overlay some quando a janela perde o foco.
2. OpenCV converte o quadro em HSV, filtra por cor, remove pixels isolados e agrupa as regiões aceitas.
3. O indicador de mira usa pixels da região detectada perto do centro da janela. Uma caixa vazia no centro não aciona o clique.
4. O clique usa `SendInput` e exige `--trigger`, F8 pressionado e a janela selecionada em foco.

Execute `py -3 -m unittest -v` para testar as três cores, os dois intervalos do vermelho e a rejeição de ruído no centro.
