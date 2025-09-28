# Pipeline Offline B3

Ferramentas para transformar os arquivos oficiais COTAHIST da B3 em uma base de pesquisa offline.

## Funções Principais

- `load_cotahist` – interpreta arquivos TXT ou ZIP e devolve um `DataFrame` com colunas OHLCV
- `save_daily_history` – salva arquivos Parquet particionados (por ticker, por padrão)
- `latest_session` – informa o último pregão disponível no `DataFrame`

## Montando a Base

1. Baixe os arquivos `COTAHIST_AAAA.ZIP` no portal de Market Data da B3.
2. Rode `load_cotahist` para cada arquivo e filtre com `tickers=["PETR4", "VALE3"]` se necessário.
3. Concatene os anos e utilize `save_daily_history` para gravar em `data/processed/b3`.

## Observações

- O parser ignora registros de cabeçalho/rodapé e converte os preços (divididos por 100 no arquivo original).
- O volume é informado em quantidade de papéis; o número de negócios fica na coluna `Trades`.
- Estenda o módulo para incorporar arquivos de eventos (dividendos, splits) e dados intradiários quando necessário.
