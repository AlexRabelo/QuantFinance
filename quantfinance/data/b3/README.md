# Pipeline Offline B3

Ferramentas para transformar os arquivos oficiais COTAHIST da B3 em uma base de pesquisa offline.

## Funções Principais

- `load_cotahist` – interpreta arquivos TXT ou ZIP e devolve um `DataFrame` com colunas OHLCV
- `save_daily_history` – salva arquivos Parquet particionados (por ticker, por padrão)
- `latest_session` – informa o último pregão disponível no `DataFrame`

## Workflow recomendado

1. Baixe `COTAHIST_AAAAA.ZIP` no portal de séries históricas da B3 (https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/series-historicas/) e coloque em `data/raw/b3/`.
2. Ajuste `config/carteira_b3.yaml` com os tickers desejados (por exemplo, carteira personalizada ou composição do índice).
3. Execute `python examples/b3_runner.py` com `PYTHONPATH` apontando para o projeto.
4. Os resultados ficam em `data/processed/b3/` (`*_raw.parquet`, `*_enriched.parquet`) e `data/processed/b3/excel/` (planilhas enriquecidas por ticker).

## Observações

- O parser ignora registros de cabeçalho/rodapé e converte os preços (divididos por 100 no arquivo original).
- O volume é informado em quantidade de papéis; o número de negócios fica na coluna `Trades`.
- Estenda o módulo para incorporar arquivos de eventos (dividendos, splits) e dados intradiários quando necessário.
