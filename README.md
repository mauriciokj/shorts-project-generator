# shorts-project-generator

Ferramenta local para gerar projetos `.mepj` do Movavi a partir de:
- um template base
- um arquivo de áudio MP3
- uma lista de imagens

## Objetivo
Automatizar a montagem inicial de shorts com o mesmo estilo visual, abrindo depois no Movavi apenas para revisão/exportação.

## Status
Prova de conceito validada com sucesso usando um template real.

## Fluxo planejado
1. ler template `.mepj`
2. extrair `config.json` e `meta.json`
3. localizar clip de áudio principal
4. medir duração real do MP3
5. localizar os clips visuais principais
6. substituir paths das imagens
7. distribuir tempo proporcionalmente entre as imagens
8. remover legenda herdada do template
9. preservar efeitos/zoom dos clips principais
10. gerar novo `.mepj`

## Próximo passo
Criar um CLI simples tipo:

```bash
python main.py \
  --template /caminho/template.mepj \
  --audio /caminho/audio.mp3 \
  --images img1.png img2.png img3.png img4.png \
  --output /caminho/saida.mepj
```
