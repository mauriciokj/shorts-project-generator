#!/usr/bin/env bash
set -e
python3 main.py \
  --template /Users/mauriciokj/projetos/videos/cris.mepj \
  --audio /Users/mauriciokj/clawd/tmp/popo-whindersson-short.mp3 \
  --images \
    /Users/mauriciokj/clawd/tmp/popo-whindersson-images/2026-03-26-popo-whindersson-01-v2.png \
    /Users/mauriciokj/clawd/tmp/popo-whindersson-images/2026-03-26-popo-whindersson-02.png \
    /Users/mauriciokj/clawd/tmp/popo-whindersson-images/2026-03-26-popo-whindersson-03-v2.png \
    /Users/mauriciokj/clawd/tmp/popo-whindersson-images/2026-03-26-popo-whindersson-04.png \
  --output /Users/mauriciokj/projetos/videos/popo_whindersson_cli_test.mepj
