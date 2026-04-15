# shorts-project-generator

Ferramenta local para gerar projetos `.mepj` do Movavi a partir de:
- um template base `.mepj`
- um arquivo de áudio MP3
- uma lista de imagens

## Objetivo
Automatizar a montagem inicial de shorts com o mesmo estilo visual, abrindo depois no Movavi apenas para revisão/exportação.

## Status
Prova de conceito validada com sucesso usando um template real.

## Como funciona
O gerador:
1. abre um template `.mepj`
2. extrai `config.json` e `meta.json`
3. localiza o clip de áudio principal
4. mede a duração real do MP3
5. localiza os clips visuais principais
6. substitui os paths das imagens
7. distribui o tempo proporcionalmente entre as imagens
8. remove legenda herdada do template
9. preserva efeitos/zoom dos clips principais
10. sincroniza metadata real das imagens (dimensões, codec e size)
11. gera um novo `.mepj`

## Template padrão embutido
Se nenhum `--template` for passado na linha de comando, o gerador usa o template embutido no próprio projeto:
- `assets/template-base/config.json`
- `assets/template-base/meta.json`

Isso evita depender de um arquivo modelo externo para testes rápidos.

## Como testar
### Com template explícito
```bash
python main.py \
  --template /caminho/template.mepj \
  --audio /caminho/audio.mp3 \
  --images img1.png img2.png img3.png img4.png \
  --output /caminho/saida.mepj
```

### Sem template (usa o template embutido)
```bash
python main.py \
  --audio /caminho/audio.mp3 \
  --images img1.png img2.png img3.png img4.png \
  --output /caminho/saida.mepj
```

## Observações
- O gerador espera **4 imagens** para o fluxo padrão.
- O template embutido deve ser mantido junto do código-fonte para não perder a base de teste.
- O projeto final deve abrir no Movavi para conferência e exportação.
