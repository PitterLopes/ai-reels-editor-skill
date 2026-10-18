# AI Reels Editor — uma skill do Claude Code que edita vídeos falados em Reels com motion graphics

[English](README.md) · **Português**

`reels-editor` é uma skill do [Claude Code](https://claude.com/claude-code) (serve também no Claude Agent SDK) que transforma um take bruto, de uma pessoa falando para a câmera, num **vídeo vertical editado para Instagram Reels, TikTok e YouTube Shorts**: cortes das pausas, legendas cinéticas, palavras que aparecem *atrás* da pessoa, reenquadramentos secos (sem zoom que vai e volta), cartões de apresentação, números animados e efeitos sonoros sintetizados — renderizado com o [HyperFrames](https://github.com/heygen-com/hyperframes) (HTML + GSAP, código aberto).

A ideia central: **a IA não escreve código de animação a cada vídeo.** Ela escreve um *plano* curto (o que mostrar, quando, em que lugar da tela), o plano é validado em código, e um **estilo** fixo e medido transforma o plano numa composição. Vinte estilos estão especificados em [`references/styles.md`](references/styles.md); três estão implementados hoje (`impact`, `card`, `data`).

> Feita para o app [Scriptroom](https://scriptroom.online) ("roteiros com IA + teleprompter"). Este repositório é a versão aberta, testável no chat, desse conceito de edição.

## O que você recebe

- **Cortes**: pausas acima de 0,6 s saem, 0,2 s de respiro ficam, exato no quadro (CFR 30 fps).
- **Transcrição com o tempo de cada palavra** (Whisper, local) → a legenda nunca diz uma palavra que não foi dita.
- **Recorte da pessoa** (opcional, `hyperframes remove-background`) para a palavra grande ficar **entre a pessoa e o fundo**.
- **Posição da cabeça** lida da máscara: a palavra atrás da cabeça cai onde a cabeça está, segundo a segundo.
- **Zona segura** do Reels (220 px no alto, 1470 px embaixo, coluna da direita) respeitada por todo elemento.
- **Reenquadramentos secos e mantidos** (1,0 → 1,18 → 1,0): nunca um zoom que entra e volta.
- **Cartões de apresentação** (a pessoa vira um cartão emoldurado, os itens entram com a voz), cartões de **número** e de **comparação**.
- **Efeitos sonoros sintetizados** (whoosh, pop, click, thump, sparkle) em faixas próprias a no máximo 0,7 de ganho — sem redistribuir biblioteca de som de terceiros.
- **Conferência pelo vídeo final**: uma folha de contato com um quadro em cada batida, os picos do áudio, uma cópia 720p para o celular.

## Instalar

```bash
git clone https://github.com/PitterLopes/ai-reels-editor-skill ~/.claude/skills/reels-editor
cd ~/.claude/skills/reels-editor
python3 scripts/setup.py     # confere ffmpeg, node 22+, python 3.9+; baixa as fontes (OFL) e o GSAP, sintetiza os efeitos
```

Requisitos: `ffmpeg`/`ffprobe`, Node 22+ (o HyperFrames vem pelo `npx`, com versão fixa), Python 3.9+. O primeiro `hyperframes transcribe` baixa um modelo do Whisper.

Depois, no Claude Code, peça algo como:

> *Edita este take como um Reel no estilo impacto: `~/Videos/take.mov`*

A skill lê o [`SKILL.pt-BR.md`](SKILL.pt-BR.md) e roda o caminho abaixo.

## O caminho

```
ingest.py   vídeo → assets/aroll.mp4 (1080×1920, 30 fps, pausas cortadas) + words.json + work/cuts.json
cutout.py   (opcional) → assets/subject.webm      headpos.py → head.json
draft_plan.py --style impact → plan.json          (a IA então refina o plano: palavras grandes, cartões, números)
validate_plan.py → plan.resolved.json             (lugares, sobreposições, zona segura, palavra dita de verdade)
build.py → index.html                             hf.py lint / snapshot / render
check.py render.mp4 --phone → work/check.jpg      (olhe os quadros antes de entregar)
```

Cada passo é um script pequeno em Python em [`scripts/`](scripts/); o esquema do plano está em [`references/plan.md`](references/plan.md); as regras de layout em [`references/layout.md`](references/layout.md); o que já nos mordeu em [`references/gotchas.md`](references/gotchas.md).

## Estilos

| Família | Estilos |
|---|---|
| A — Palavras | Impacto, Máquina de escrever, Marca-texto, Pilha, Glitch |
| B — Cartões | Cartão, Passos, Checklist, Versus, Citação |
| C — Dados | Dados, Contador, Gráfico, Linha do tempo, Mapa |
| D — Cena | Fundo, Dividido, Moldura, Janela, Cinema |
| E — Marca | Mínimo, Editorial, Neon, Papel, Estúdio |

As especificações (valores, quando usar, o que pede do take): [`references/styles.md`](references/styles.md).

## Por que não um prompt por vídeo?

Tentamos. Dois protótipos em que o modelo escrevia o código da animação tiraram 3 de 10 com quem tinha de postar o vídeo, custaram US$ 7 cada e levaram 25 minutos. Estilos fixos com valores exatos mais um plano curto e validado é o que dá resultado consistente e profissional em minutos — e o que deixa o mesmo caminho rodar num servidor, para um app.

## Licença

MIT. As fontes são baixadas no setup sob a SIL Open Font License; o HyperFrames é Apache-2.0; o GSAP tem licença própria (grátis para a maior parte dos usos — ver [gsap.com/licensing](https://gsap.com/licensing)).

Palavras-chave: edição de vídeo com IA, skill do Claude Code, editor de reels, editor de tiktok, youtube shorts, legenda automática, tipografia cinética, vídeo falando para a câmera, motion graphics, hyperframes, gsap, ffmpeg, whisper, alternativa ao opusclip, alternativa ao submagic, ai video editing.
