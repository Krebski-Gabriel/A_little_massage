# Experimento: folhas de outono

Uma versão experimental do site, com folhas secas caindo durante a leitura e um chão de folhas no final. **O site atual não foi alterado**: o experimento vive numa página à parte, `autumn.html`, para você comparar as duas lado a lado.

| Versão | Endereço (depois de publicar) |
|---|---|
| Atual | `https://krebski-gabriel.github.io/Jessica-s-universe/` |
| Experimento | `https://krebski-gabriel.github.io/Jessica-s-universe/autumn.html` |

## Arquivos do experimento (todos novos)

```
autumn.html               a mesma página do index.html + as três peças abaixo
autumn.css                canvases das folhas, o chão, a rosa apoiada no chão
autumn.js                 a queda das folhas ligada à rolagem (não mexe no script.js)
assets/autumn/
  leaves.webp             atlas: 12 folhas × (frente, verso) × (nítida, desfocada)   95 KB
  floor-1.webp            o chão: terra escura + as primeiras folhas                  ~75 KB
  floor-2.webp            mais folhas                                                ~185 KB
  floor-3.webp            as últimas folhas, por cima                                ~160 KB
tools/autumn_leaf.py      gerador das folhas (formas, nervuras, cor, relevo, luz)
tools/make_autumn.py      monta o atlas e o chão a partir do gerador
AUTUMN.md                 este arquivo
```

Nada disso é baixado antes de ela tocar na Lua: a primeira tela pesa o mesmo que hoje.

## Como funciona

**Fases, pela rolagem (não por um cronômetro):**
- **A — abertura:** antes do toque na Lua, nenhuma folha. Depois do toque, só uma folha perdida de vez em quando.
- **B — leitura:** cada trecho rolado "traz" folhas, e o tempo traz mais algumas, devagar. A quantidade cresce conforme ela avança na carta (no teste: de 1–2 folhas no ar no começo da carta até ~12 no celular e ~22 no computador no fim).
- **C — encerramento:** o chão aparece no fim da página em três camadas, que vão se acendendo uma depois da outra nos últimos trechos da rolagem, como se as folhas fossem se acumulando. As folhas que caem nessa hora pousam no chão e somem entre as outras.

**Detalhes:**
- As folhas caem **atrás do texto**, que continua 100 % legível. Só em telas largas, raramente, uma folha grande e desfocada passa **na frente**, sempre nas bordas, longe do texto.
- Profundidade: folhas distantes são menores, mais escuras e desfocadas; as próximas, maiores. Elas oscilam de um lado para o outro, giram, viram (aparece o verso, mais pálido) e caem mais rápido quando ficam de lado.
- Quando ela rola, as folhas se movem um pouco junto (paralaxe leve), como se estivessem no ar da cena.
- A rosa fica de pé sobre o chão, com uma sombra de contato onde o caule encontra as folhas.
- **Celular:** menos folhas (no máximo 12) e resolução menor no canvas.
- **"Reduzir movimento" ativado:** nenhuma folha cai; o chão aparece completo e parado.
- **Sem JavaScript:** a página funciona e o chão aparece no fim.

## Testar localmente

```bash
cd Jessica-s-universe
python3 -m http.server 8000
```

Abra `http://localhost:8000/autumn.html` (experimento) e `http://localhost:8000/` (atual). No celular, na mesma rede Wi-Fi: `http://SEU_IP:8000/autumn.html`.

No console do navegador, `__autumn.count()` mostra quantas folhas estão no ar naquele momento.

## Publicar no GitHub Pages (só quando você quiser)

Nada foi publicado. Para colocar o experimento no ar **sem mudar o site atual**, envie para o repositório apenas os arquivos novos listados acima (Add file › Upload files, arrastando `autumn.html`, `autumn.css`, `autumn.js`, `AUTUMN.md`, a pasta `assets/autumn` e os dois arquivos de `tools`) e faça o commit. Pelo terminal:

```bash
git add autumn.html autumn.css autumn.js AUTUMN.md assets/autumn tools/autumn_leaf.py tools/make_autumn.py
git commit -m "Experimento: folhas de outono"
git push
```

Depois de 1–2 minutos, abra `.../Jessica-s-universe/autumn.html?v=1` no celular.

## Se gostar: tornar o experimento a versão principal

Faça backup do `index.html` atual (por exemplo, copie para `index-sem-outono.html`) e então copie o conteúdo de `autumn.html` para `index.html`. Só isso: `autumn.html` já é a página completa.

Se depois você editar o texto da carta, lembre que `index.html` e `autumn.html` são arquivos separados; mude nos dois enquanto os dois existirem.

## Desfazer

Apague os arquivos novos listados acima. O site atual nunca dependeu deles.

## Ajustes rápidos

| O quê | Onde |
|---|---|
| Quantidade de folhas | `autumn.js` → `MAX_LEAVES`, `DENSITY`, `timeRate()`, `scrollRate()` |
| Tamanho das folhas | `autumn.js` → `var size = …` em `spawn()` |
| Velocidade da queda | `autumn.js` → `vy:` em `spawn()` |
| Altura do chão | `autumn.css` → `--ground-h` |
| Onde a rosa pisa no chão | `autumn.css` → `margin-top` de `.ground` |
| Regerar as imagens | `pip install numpy scipy pillow` e `python3 tools/make_autumn.py` (~2 min) |

## Limitações (leia antes de mostrar a ela)

1. **As folhas não são fotografias.** Daqui eu não consegui acessar nenhum banco de imagens livre (Wikimedia, Unsplash, Pexels, Poly Haven, ambientCG ficam bloqueados), e não encontrei um conjunto de fotos com licença livre num repositório acessível. Então as folhas foram **renderizadas por código**: silhuetas de bordo, carvalho, faia e bétula, nervuras de cada espécie, bordas secas e roídas, manchas, furos, superfície curvada iluminada pela Lua, desfoque de profundidade. De longe e em movimento convencem bem; olhando de perto, uma foto real teria mais textura.
   **Para trocar por fotos reais:** monte um `assets/autumn/leaves.webp` no mesmo formato (12 colunas × 4 linhas, quadrados de 128 px, fundo transparente: linha 1 frente, linha 2 verso, linhas 3–4 as mesmas desfocadas). O código não muda. Fontes com licença livre: as coleções "Leaf" do ambientCG (CC0) e as texturas de chão de folhas do Poly Haven (CC0).
2. **O chão é uma composição de ~1.500 dessas folhas** com perspectiva, sombras e luz. Lido como "um chão coberto de folhas à noite", mas não é uma fotografia de chão.
3. **Testei** no Chromium sem interface (o motor do Chrome), em 360×640, 375×553, 390×664, 844×390 (celular deitado), 1440×900 e 1920×1080: as três fases, legibilidade, posição da rosa, "reduzir movimento", sem JavaScript, rolagem lateral e erros de JavaScript. O custo extra medido foi de poucos milissegundos de script por segundo em relação ao site atual. **Não testei** em Safari nem em celulares reais; confira no seu celular antes de mandar.
4. O site publicado hoje está **sem a assinatura** e **sem a tag `<title>`** (saíram no commit "Mudei para um estilo de conversa"). Não mexi nisso; `autumn.html` segue igual ao `index.html` nesse ponto.
