# /reels-editor (versão em português deste SKILL.md)

> O Claude lê o `SKILL.md` em inglês. Este arquivo é a mesma instrução, em português, para quem quer
> entender ou adaptar a skill. Mantenha os dois iguais ao editar.

Um vídeo de uma pessoa falando entra, um Reel editado sai. Quem usa escolhe um **estilo** do catálogo em
`references/styles.md` (20 no catálogo; `impact`, `card` e `data` estão implementados em
`scripts/build.py`; os outros estão especificados, esperando o código). A IA nunca escreve HTML ou GSAP
para um vídeo: ela escreve o `plan.json` (o que ganha destaque, quando, onde) e o estilo renderiza. É isso
que mantém todo vídeo consistente, barato e rápido.

Leia antes da primeira edição: `references/pipeline.md` (as etapas e os arquivos que elas produzem),
`references/plan.md` (o formato do plano e as regras de validação), `references/layout.md` (zona segura e
a fórmula do texto atrás da cabeça), `references/gotchas.md` (as armadilhas já encontradas).

Funciona em macOS e Linux (Windows não testado). Precisa de ffmpeg, Node 22+ e Python 3.9+.
`scripts/setup.py` confere os três, baixa as fontes de licença aberta e sintetiza os efeitos sonoros
(nenhum áudio de terceiros é embutido nem baixado).

## Regras fixas
1. **Nenhum código de render livre por vídeo.** Tudo na tela vem do `plan.json` por um estilo do
   `build.py`. Se um estilo não expressa o que o vídeo pede, diga isso e proponha uma mudança no estilo,
   nunca um remendo no HTML.
2. **Zona segura do Reels**, sempre: nada nos 220 px do topo, nada abaixo de y 1470, 35 px de cada lado,
   e a coluna direita de 100 px livre a partir de y 1155. `build.py --safe` desenha a zona; confira os
   snapshots com ela ligada e renderize com ela desligada.
3. **Nunca cubra o rosto** (dos olhos ao queixo). Palavra atrás da cabeça mantém ~70% de cada letra
   visível; o `validate_plan.py` rebaixa a palavra para a faixa do peito quando a cabeça a esconderia.
4. **A legenda diz o que foi dito.** Corrija os erros do transcritor em nomes, produtos e números, pelo
   roteiro ou ouvindo. Número na tela só se a pessoa o disse.
5. **Efeitos sonoros abaixo da voz**, nunca acima (`SFX_GAIN` 0,7).
6. **Prove cortes e batidas pelo render final** (`check.py`), não pelos snapshots.
7. **Nunca apague nem altere os arquivos originais da pessoa.** Tudo é escrito dentro da pasta do projeto.

## Fluxo
0. `python3 SK/scripts/setup.py` até imprimir READY.
1. **Entrada:** o vídeo, o estilo (ofereça os três implementados; `impact` na dúvida), a marca (cor de
   destaque e logo opcional; padrões em `template/brand.json`), a língua e os nomes que o transcritor erra.
2. **`ingest.py`:** normaliza para 1080x1920 a 30 fps constantes, tira pausas acima de 0,6 s (deixa 0,2 s),
   escreve `assets/aroll.mp4`, `work/cuts.json` e `words.json`. Corrija os erros em `words.json`.
3. **`cutout.py` e `headpos.py`** só nos estilos que pedem recorte (marcados em `styles.md`).
4. **`draft_plan.py`** rascunha o `plan.json`; **você o edita como editor**: marca as palavras de impacto,
   acrescenta cartões, números e comparações onde a fala os nomeia, tira o que vira poluição. Ritmo em vídeos
   longos: uma batida grande a cada 6 a 10 s, nunca duas sobrepostas, um reenquadramento a cada 15 a 30 s.
   `validate_plan.py` até zero erros; leia cada aviso.
5. **`build.py --safe`**, `hf.py lint`, `hf.py snapshot`, olhe os snapshots, conserte o plano (não o HTML);
   `build.py`, `hf.py render`, `check.py` com a cópia de celular.
6. **Entrega e ajustes:** as notas da pessoa mudam o `plan.json` ou o `brand.json`, nunca o HTML; cada versão
   fica em `renders/`.

## Padrões que vieram de feedback real (não rediscutir)
- O estilo é uma receita fixa; o vídeo muda, a receita não.
- Sem zoom que vai e volta: reenquadramento é corte seco mantido até o próximo, ou aproximação lenta.
- Grade escura mantém a pessoa iluminada. Sem granulado. Sem fundo gerado por IA.
- Legenda centrada na faixa do peito lê melhor do que presa a uma borda.
- Palavra grande atrás da cabeça é o movimento de assinatura, só quando legível.
- Português e inglês de igual para igual.
