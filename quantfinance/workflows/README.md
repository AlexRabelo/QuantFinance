# Workflows

Conjunto de fluxos que simplificam o uso do pacote.

## Yahoo Finance / Carteira

- `examples/portfolio_runner.py`
  - Lê `config/carteira_base.yaml`.
  - Baixa dados via Yahoo, gera Parquets raw/enriched, consolida Excel por ativo e imprime snapshot textual.

## B3 (COTAHIST)

- `examples/b3_runner.py`
  - Lê `config/carteira_b3.yaml` e os arquivos ZIP em `data/raw/b3`.
  - Usa `quantfinance.workflows.b3.run_b3_pipeline` para converter os dados da B3 em Parquets raw/enriched e planilhas por ticker.

## Reporting

- `snapshot_from_dataframe`, `summarise_snapshot` – criam resumos textuais com tendências, suportes, resistências e Fibonacci.
- `render_visual_report` – gera HTML interativo com candles, indicadores e volume.

## Features / Enriquecimento

- `quantfinance.workflows.features.indicators.enrich_dataframe` adiciona indicadores (SMA/EMA, RSI, MACD, ATR, Bandas 2/2.5/3, mín/máx 52 semanas, flags de topo/fundo, retornos) a qualquer `DataFrame` que possua colunas OHLCV e `Date`.
