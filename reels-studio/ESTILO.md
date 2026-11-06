# Estilo de edição — Reels do Guilherme

Fonte da verdade para editar. Os valores numéricos ficam em `estilo.json`; os termos do nicho em `glossario.txt`.
Regra do **Style Lab**: nada muda por gosto do editor. Estilo novo só entra por **rodada** (3 opções por item → Guilherme marca **Manter / Talvez / Descartar** + nota) e o que for "Manter" é **travado** aqui, com data.

## 1. Travado (aplicar sempre, sem perguntar)

| Item | Regra | Desde |
|---|---|---|
| Legenda | máx **3 palavras** por take, **Montserrat 800**, tudo **minúsculo**, sem pontuação final | 20/10/2026 |
| Cor da legenda | **branca** com **sombra esfumaçada** (3 drop-shadows largos, sem contorno) | 20/10/2026 |
| Destaque | palavras-chave na **paleta da campanha** (atual: ouro `#F0DCA8 → #E4CB93 → #C9A45C → #B8914A`), pop 0,7→1 | 20/10/2026 |
| Posição | centro da linha em y≈1300 (abaixo dos rostos, acima da UI do Reels); tamanho único pelo take mais longo | 20/10/2026 |
| Câmera | **punch-in** (zoom rápido + tremida curta + flash marfim) nas falas de efeito; **zoom-out** (entra perto e abre) em números/datas; corte de zoom 1,0/1,08 a cada frase nova | 20/10/2026 |
| Som | SFX discretos só onde há ação na tela: whip/whoosh alternados no punch, **ding** em termo de impacto, whoosh no zoom-out, click em "link". Nunca o mesmo som em todo efeito | 20/10/2026 |
| Música | só se o Guilherme pedir (vídeos com diálogo já têm o próprio som) | 20/10/2026 |
| Corte | vídeo chega já filtrado; **cortar silêncio inicial, repetições e pausas quando o Guilherme pedir** (pediu em 05/11/2026, junto com cor viva); não recolorir sem pedido | 05/11/2026 |

## 2. Regras de leitura (HyperFrames + experiência)

- Take na tela por **≥ 0,4 s**; take curto junta com o vizinho (o `paginar.py` já faz).
- Nunca terminar take em artigo/preposição ("um", "no", "de"…); nunca partir termo do glossário ("janela de / ouro").
- Legenda entra 0,05 s antes da palavra; some 0,35 s após a fala quando há pausa longa.
- Faixa segura 9:16: nada nos 168 px de cima; texto entre 168 e 1330 px; nada sob a barra de ações à direita.
- Efeitos no máximo **1 a cada 3 s**; prioridade: termo de impacto (`!` no glossário) > número/data > termo comum.
- Transcrição com prob < 0,5 = conferir; termo de nicho errado vira correção no glossário (`errado => certo`) pra nunca mais repetir.

## 3. Repertório para pedir (Inspiration Vault — 451 refs, estilo Iman Gadzhi/Ali Abdaal)

Usar como cardápio quando o Guilherme quiser "mais efeito". Cada item é uma rodada Style Lab antes de virar padrão.

| Categoria do Vault | O que é | Como fazemos aqui |
|---|---|---|
| Text Screens | tela escura com 1–3 palavras grandes, glow/gradiente, kinetic type ("VALUE", "$20,000", "HOW CAN YOU DOUBLE") | cartela full-screen HyperFrames entre frases, sem legenda por cima |
| Visual/Animation | ícones/emojis/apps flutuando ao lado da pessoa, cards de número, gráfico subindo, mockup de navegador/busca | overlay ao lado do rosto (nunca em cima), entra na palavra |
| Style | texto grande **atrás da pessoa** (recorte), split-screen, moldura de "post"/perfil | `remove-background` do HyperFrames + texto atrás (padrão já usado no IMG_5483) |
| Transitions | whip/blur swap, zoom through, flash | catálogo `npx hyperframes catalog --tag transition` |
| Intro | gancho no 1º frame: rosto + frase forte já na tela | título do gancho nos 2 primeiros segundos |
| General / How to | B-roll, mapa, timeline, livro/lista, UI real | B-roll via plugin get-brolls (gasta crédito: avisar) |

## 4. Histórico de rodadas Style Lab

- 07/10/2026 exemplo 1: Poppins + contorno, 3–4 palavras → **substituído** em 20/10.
- 20/10/2026 exemplo 2: estilo da seção 1 aprovado.

## 5. Pastas de trabalho (fixas)

| Pasta | Uso |
|---|---|
| `..\Videos de referência\` (videoJB-01/02/03) | Modelo de edição a seguir. Consultar antes de propor efeito novo. Guilherme pode adicionar/remover vídeos. |
| `..\Videos para editar\` | Fila de entrada. Quando ele pedir "edita", pegar daqui (listar a pasta na hora; o conteúdo muda sempre). |

## 6. Modelo das referências (videoJB, 720×1280, Jordan Belfort, 40–55 s)

Observado em 20+ quadros de cada vídeo. **Ainda não travado**: entra em `## 1` só depois de rodada Style Lab (Manter/Talvez/Descartar). Até lá, é o alvo de repertório.

- **Legenda**: Poppins bold, 2–4 palavras por take, branca com sombra suave; fica **no peito/microfone** (y ≈ 55–65% da tela), abaixo do rosto. Maiúscula só em ênfase ("AS SOON AS WE").
- **Destaque**: palavra-chave em **amarelo vivo** (`#F5D90A`-ish), maior que o resto, em 2ª linha embaixo da legenda ("WORK FOR THEM", "skill", "Prices", "COST", "ARRIVING", "the same team"). Às vezes itálico.
- **Cartelas de lista**: número amarelo itálico grande + título em itálico cinza no topo ("6 OBJECTIONS", "3 I NEED TO TALK TO MY WIFE", "4 IT'S NOT THE RIGHT TIME").
- **Props animados ao lado da pessoa** (nunca sobre o rosto): contador/timer num laptop (01:00 → 00:17), caixas/ícones em moldura amarela tracejada, papéis "CONTRACT" voando, emoji 3D (despertador), foto polaroid desfocada.
- **Cenas de apoio (B-roll)**: 1–2 s, tela cheia, trecho de filme/foto de cena (sala de aula, escritório, telefone) com a legenda por cima; fundo escuro com texto grande desfocando para entrar.
- **Cartela escura**: fundo preto, 1 frase central com blur-in + objeto 3D/emoji embaixo.
- **Ritmo**: troca de plano (rosto ↔ b-roll ↔ cartela) a cada 2–4 s; legenda troca a cada ~1 s; rosto nunca fica 5 s sem nada novo na tela.
- **Zoom**: micro-zoom lento no rosto entre frases, sem tremida pesada.

Diferenças em relação ao estilo travado (seção 1): fonte (Poppins vs Montserrat), cor de destaque (amarelo vs ouro da campanha), legenda minúscula vs maiúscula em ênfase, e uso pesado de props/b-roll. Perguntar ao Guilherme qual vale para cada vídeo.

