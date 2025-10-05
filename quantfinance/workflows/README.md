# Workflows

Conjunto de fluxos que simplificam o uso do pacote.

## Yahoo Finance / Carteira

- `examples/portfolio_runner.py`
  - Lê `config/tickets.yaml`.
  - Baixa dados via Yahoo, gera Parquets raw/enriched, consolida Excel por ativo e imprime snapshot textual.

## B3 (COTAHIST)

- `examples/b3_runner.py`
  - Lê a seção `b3.tickers` de `config/tickets.yaml` e os arquivos ZIP em `data/raw/b3`.
  - Usa `quantfinance.workflows.b3.run_b3_pipeline` para converter os dados da B3 em Parquets raw/enriched e planilhas por ticker.

## Reporting

- `snapshot_from_dataframe`, `summarise_snapshot` – criam resumos textuais com tendências, suportes, resistências e Fibonacci.
- `render_visual_report` – gera HTML interativo com candles, indicadores e volume.

## Auditoria e Alertas

- `audit_yahoo_assets` / `audit_b3_tickers` – verificam cobertura dos Parquets e lacunas de negociação.
- `alerts.build_alert_report` – converte auditorias em alertas (usado pelo comando `manage.py audit`).

## Analytics

- `analysis.analytics.compute_momentum_scores` – calcula retornos acumulados e score de momentum.
- `analysis.analytics.compute_indicator_snapshot` – extrai indicadores personalizados do último pregão.

## Features / Enriquecimento

- `quantfinance.workflows.features.indicators.enrich_dataframe` adiciona indicadores (SMA/EMA, RSI, MACD, ATR, Bandas 2/2.5/3, mín/máx 52 semanas, flags de topo/fundo, retornos) a qualquer `DataFrame` que possua colunas OHLCV e `Date`.
