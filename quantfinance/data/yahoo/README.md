# Pipeline Yahoo Finance

Ferramentas para baixar e persistir históricos diários (ou intradiários) a partir do Yahoo Finance.

## Funções Principais

- `download_history` – baixa um ticker e devolve um `DataFrame` normalizado
- `YahooConfig` + `download_batch` – configuração declarativa para downloads em lote
- `save_to_parquet` – salva o mapeamento ticker -> `DataFrame` em `data/processed/yahoo`

## Fluxo Típico

```python
from quantfinance.data.yahoo.client import YahooConfig, download_batch, save_to_parquet

config = YahooConfig(tickers=["PETR4.SA", "VALE3.SA"], start="2023-01-01")
series = download_batch(config)
save_to_parquet(series, "data/processed/yahoo")
```

## Observações

- Os dados do Yahoo são práticos, mas sujeitos a limites de requisição; faça cache local assim que possível.
- O preço ajustado aparece na coluna `AdjClose`; o `Close` permanece bruto.
- Amplie o módulo com lógica de retry ou paralelização se precisar de grandes volumes.
