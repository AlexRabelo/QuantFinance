# Configuracoes de Carteira

Arquivos YAML que descrevem carteiras de ativos para download automatizado.

## Yahoo Finance

Usa `config/tickets.yaml` no pipeline do Yahoo (`examples/portfolio_runner.py`). O arquivo replica a carteira teorica do IBrX-100 e adiciona ETFs/ETNs de diagnostico (BOVA11, SMAL11, XFIX11, IMAB11, IRFM11, HASH11, IVVB11, USDB11.SA).

## B3 (COTAHIST)

Os mesmos tickers da B3 moram em `config/tickets.yaml`, na chave `b3.tickers`, reutilizada pelo pipeline `examples/b3_runner.py`. A lista vem de `config/IBXX.xlsx` (composicao oficial do IBrX-100) e inclui ETFs/ETNs auxiliares para leitura macro (BOVA11, SMAL11, XFIX11, IMAB11, IRFM11, HASH11, IVVB11, USDB11).

```yaml
portfolio:
  ...

b3:
  tickers:
    - PETR4
    - VALE3
    - BOVA11
    # ... demais ativos do IBrX-100 e ETFs auxiliares
```

## Execucao

1. **Yahoo Finance**
   ```bash
   $env:PYTHONPATH = "$PWD"
   python examples/portfolio_runner.py
   ```
   Gera Parquets raw/enriched e um Excel consolidado com indicadores.

2. **B3**
   ```bash
   # coloque os arquivos COTAHIST_AAAAA.ZIP em data/raw/b3
   $env:PYTHONPATH = "$PWD"
   python examples/b3_runner.py
   ```
   Filtra os tickers definidos em `b3.tickers`, atualiza Parquets raw/enriched em `data/processed/b3` e cria planilhas enriquecidas em `data/processed/b3/excel`.
