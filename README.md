# A Little Universe, Just for You

Uma pequena experiência web, feita à mão, com a Lua no centro.
HTML, CSS e JavaScript puros — sem frameworks, sem build, sem dependências, sem rastreamento.

---

## 1. Estrutura

```
a-little-universe/
├── index.html              # conteúdo: introdução, poema, final
├── styles.css              # visual (tokens de cor e tipografia no topo)
├── script.js               # estrelas, toque na Lua, rolagem, revelações
├── assets/
│   ├── moon.webp           # Lua 1200×1200 (com transparência) — telas de alta densidade
│   ├── moon-720.webp       # Lua 720×720 — escolhida automaticamente em telas menores
│   ├── moon.jpg            # fallback para navegadores sem WebP
│   ├── moon-mark.webp      # Lua minúscula da assinatura
│   ├── moon-wash.webp      # aguadas de aquarela prateadas que florescem ao tocar a Lua
│   ├── og-image.jpg        # imagem da prévia do link no WhatsApp
│   ├── favicon.png, apple-touch-icon.png
│   └── fonts/              # Newsreader + Hanken Grotesk (auto-hospedadas, licença OFL)
├── tools/
│   ├── render_moon.py      # script que gerou a imagem da Lua a partir dos dados da NASA
│   ├── make_wash.py        # script que pintou as aguadas de aquarela (moon-wash.webp)
│   └── make_rose.py        # script que gera os traços da rosa em giz pastel oleoso
└── README.md
```

Por que as fontes estão dentro do projeto: assim o site não faz nenhuma requisição a terceiros (nem ao Google Fonts) e continua bonito mesmo se uma CDN estiver lenta no lugar onde ela estiver.

## 2. O que personalizar antes de enviar

| O quê | Onde |
|---|---|
| Assinatura | `index.html`, procure `signature__name` |
| URL absoluta da prévia do WhatsApp | `index.html`, `og:image` e `twitter:image` (veja a seção 5) |
| Ritmo da interação | `script.js`, objeto `TIMING` no topo |
| Cores e escala tipográfica | `styles.css`, bloco `:root` |
| Tamanho da Lua | `styles.css`, variável `--moon` |

O poema está em `index.html`, um `<p class="stanza">` por estrofe e um `<span class="verse">` por verso. O texto foi reproduzido exatamente como você enviou.

## 3. Sobre a imagem da Lua (origem e licença)

A Lua **não é desenho em CSS** nem imagem de banco genérico. Ela foi renderizada a partir de **dados reais da sonda Lunar Reconnaissance Orbiter (NASA)**:

- **Superfície (albedo):** mosaico colorido da câmera LROC WAC.
- **Relevo:** mapa de normais calculado a partir do modelo de elevação LOLA (altímetro a laser).
- **Fonte:** NASA Scientific Visualization Studio — *CGI Moon Kit* (SVS #4720), visualizações de Ernie Wright (USRA/NASA GSFC). Os mapas 2048×1024 usados foram obtidos já preparados no repositório público `hadealahmad/kde-moonphase-wallpaper` (`contents/images/`), que documenta essa mesma origem.
- **Licença:** material da NASA em domínio público, segundo as NASA Media Usage Guidelines. Não exige permissão; o crédito acima é uma cortesia recomendada.

O script `tools/render_moon.py` projeta esses mapas numa esfera, aplica o modelo de iluminação *Lunar-Lambert* (o que faz a Lua real parecer "achatada" e brilhante até a borda, e não uma bola de plástico) e posiciona o Sol a 24° do observador — uma Lua quase cheia, com as crateras ganhando sombra e relevo perto da borda direita. Ele é determinístico: rodando de novo com os mesmos mapas, sai exatamente o mesmo arquivo.

```bash
pip install numpy pillow
python3 tools/render_moon.py moon_albedo.jpg moon_normal.png moon.png 1200 24
```

**Se preferir uma fotografia propriamente dita**, uma opção clássica é *FullMoon2010.jpg*, de Gregory H. Revera, no Wikimedia Commons (licença CC BY-SA 3.0 — exige crédito ao autor). Basta recortar em quadrado com a Lua encostando nas bordas, exportar como `assets/moon.webp` (1200 px) e `assets/moon-720.webp` (720 px), e adicionar o crédito no rodapé.

## 4. Testar localmente

Abrir o `index.html` com dois cliques funciona, mas o ideal é servir a pasta:

```bash
cd a-little-universe
python3 -m http.server 8000
```

Abra `http://localhost:8000` no computador.

**No celular, na mesma rede Wi‑Fi:** descubra o IP do computador (`ipconfig` no Windows, `ip addr` no Linux, Ajustes › Wi‑Fi no Mac) e abra `http://SEU_IP:8000` no celular.

**Simulando um celular no computador:** Chrome › F12 › ícone de celular (Ctrl+Shift+M) › escolha "iPhone SE" e "iPhone 14 Pro". Na aba *Network*, teste "Slow 4G" para ver o carregamento lento.

## 5. Publicar grátis no GitHub Pages

1. Crie uma conta em github.com (se ainda não tiver).
2. Clique em **New repository**. Nome: `a-little-universe`. Marque **Public**. Crie.
3. Na página do repositório: **Add file › Upload files**. Arraste **o conteúdo** da pasta `a-little-universe` (o `index.html` precisa ficar na raiz do repositório, não dentro de outra pasta). Clique em **Commit changes**.
   - Pelo terminal, se preferir:
     ```bash
     cd a-little-universe
     git init && git add . && git commit -m "A little universe"
     git branch -M main
     git remote add origin https://github.com/SEU_USUARIO/a-little-universe.git
     git push -u origin main
     ```
4. Vá em **Settings › Pages**. Em *Build and deployment*, escolha **Deploy from a branch**, branch **main**, pasta **/ (root)**. Salve.
5. Espere 1–2 minutos. O link aparece no topo dessa mesma página:
   `https://SEU_USUARIO.github.io/a-little-universe/`

**Prévia do WhatsApp:** o WhatsApp só mostra a imagem da prévia com URL absoluta. Ela já está apontando para `https://krebski-gabriel.github.io/Jessica-s-universe/assets/og-image.jpg`; se o endereço do site mudar, atualize `og:image` e `twitter:image` em `index.html`.

> Observação: repositório público significa que o código fica visível no GitHub. O link em si não aparece em buscadores (a página tem `noindex`). Se quiser o código privado, use **Netlify Drop** (app.netlify.com/drop): arraste a pasta, e ele gera um link público na hora, sem repositório.

## 6. Verificar no celular antes de enviar

- Abra o link no **seu** celular, pelos dados móveis (não pelo Wi‑Fi), para simular a conexão dela.
- Confira: a primeira tela cabe inteira sem rolar; a Lua aparece nítida; um toque nela acende o halo e leva até a carta; o poema aparece estrofe por estrofe; a declaração final e a rosa surgem no fim.
- Teste também abrindo **dentro do WhatsApp** (mande o link para você mesmo ou para o grupo "só eu"): ele abre no navegador interno, que é exatamente o que ela vai usar.
- Se mudou algo e o celular mostra a versão antiga, adicione `?v=2` no fim do link para furar o cache.

## 7. Compartilhar pelo WhatsApp

Cole o link sozinho na conversa e espere a prévia carregar (a Lua sobre fundo preto) antes de enviar. Se a prévia não aparecer, confira a URL absoluta do `og:image` (seção 5). O WhatsApp guarda a prévia em cache — se você corrigir depois, mande o link com `?v=2` no fim.

Ela não precisa instalar nada: o site abre direto no navegador do celular.

## 8. Decisões técnicas

- **Sem JavaScript**, a página continua funcionando: a carta aparece abaixo da Lua, sem animações.
- **`prefers-reduced-motion`:** com "Reduzir movimento" ativado no celular, não há animações, a rolagem é instantânea e as estrelas ficam paradas.
- **Teclado:** a Lua é um `<button>` de verdade — Tab foca (com anel visível), Enter/Espaço abrem. Depois da rolagem, o foco vai para a carta (útil para leitores de tela).
- **Segundo toque na Lua:** não repete o efeito; apenas leva de volta à carta.
- **Rolagem até a carta:** própria (2,2 s, suave), e qualquer toque ou rolagem dela interrompe imediatamente — nunca "briga" com o dedo.
- **Conexão lenta:** enquanto a imagem carrega, uma silhueta discreta ocupa o lugar da Lua; quando chega, ela aparece com um fade (decodificada antes, para não "pintar aos pedaços"). O navegador escolhe sozinho entre a versão de 720 px e a de 1200 px.
- **Imagem ausente:** se a Lua não carregar de jeito nenhum, um disco cinza sóbrio assume o lugar e a interação continua funcionando.
- **A rosa em giz pastel oleoso:** um SVG com ~110 traços gerados por `tools/make_rose.py`. As pétalas e folhas são preenchidas por camadas de traços que acompanham a forma, como se faz com o bastão de pastel, em rosa antigo e verde-sálvia acinzentado. Um filtro SVG (`#rose-pastel`) cria o "dente" do papel (as falhas onde o pastel pula a textura) e as bordas levemente irregulares. Ela se desenha sozinha depois da última linha: caule, folhas, pétalas, em cerca de 3,5 s. A velocidade se ajusta em `styles.css`, variável `--rose-pace`. O caractere 🌹 continua no texto, invisível, para leitores de tela e para quem copiar o poema.
- **Aquarela ao tocar a Lua:** aguadas translúcidas prateadas (`assets/moon-wash.webp`, pintadas por `tools/make_wash.py`) ficam **atrás** da foto da Lua, então nunca cobrem as crateras. No toque, elas se espalham para fora como pigmento levado pela água (cerca de 2,5 s), ao mesmo tempo que o brilho e o halo que já existiam. Não atrasam o poema: o tempo até a carta continua igual. Para mudar a intensidade, ajuste `opacity` em `.moon.is-lit .moon__wash`.
- **Sem música:** por decisão. Nada toca sozinho e não há botão extra na tela.
- **Peso total da primeira tela:** ~120–270 KB de Lua + ~310 KB de fontes (em cache depois da primeira visita).
