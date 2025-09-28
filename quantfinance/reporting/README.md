# Módulo de Reporting

Responsável por gerar análises textuais e visuais a partir dos dados processados.

## Componentes

- `insights.py` – constrói snapshots consolidados (`MarketSnapshot`) e gera resumos em texto
- `visualization.py` – cria gráficos interativos (candlestick + indicadores)

## TrendSnapshot

Ao chamar `build_market_snapshot`, o campo `trend` traz um `TrendSnapshot` contendo:

- `direction` – classificado em alta (`uptrend`), baixa (`downtrend`) ou lateral (`sideways`)
- `slope_short` – inclinação da EMA de 9 períodos (≈ 2 semanas), indicando a força de curto prazo
- `slope_medium` – inclinação da EMA de 21 períodos (≈ 1 mês)
- `slope_long` – inclinação da EMA de 72 períodos (≈ 3 meses)
- `crossover` – situação das EMAs entre si:
  - `bullish_stack`: EMA 9 > EMA 21 > EMA 72 (configuração altista clássica)
  - `bearish_stack`: EMA 9 < EMA 21 < EMA 72 (configuração baixista)
  - `mixed`: médias cruzadas ou sem empilhamento claro

O resumo textual (`summarise_snapshot`) converte esses conceitos para português, explicando a direção do mercado, o preço/data mais recente, suportes/resistências próximos e divergências do RSI.

## Dados Enriquecidos

Os arquivos `*_enriched.parquet` gerados pelo workflow de carteiras já incluem os indicadores usados pelo módulo de reporting (SMA/EMA 9-21-72, RSI, MACD, Bandas de Bollinger 2/2.5/3, ATR, mín/máx 52 semanas e flags de topo/fundo). Assim, basta carregar o Parquet enriquecido para insumos completos do snapshot ou de outras análises.

## Exemplo de Uso

```python
from quantfinance.reporting import build_market_snapshot, summarise_snapshot

snapshot = build_market_snapshot(df)
print(summarise_snapshot(snapshot))
```

## Visualizações

`plot_full_analysis(df, output_path)` gera um HTML com candles, médias, MACD, RSI e volume. Ideal para complementar o texto do snapshot com gráficos interativos.
