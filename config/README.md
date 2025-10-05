# Configurações de Carteira

Arquivos YAML que descrevem carteiras de ativos para download automatizado.

## Yahoo Finance

Usa `config/tickets.yaml` com os tickers trabalhados no pipeline do Yahoo (`examples/portfolio_runner.py`).
O arquivo replica a carteira teórica do IBrX-100 e adiciona ETFs/ETNs de diagnóstico (BOVA11, SMAL11, XFIX11, IMAB11, IRFM11, HASH11, IVVB11, USDB11.SA).

## B3 (COTAHIST)

Os mesmos tickers da B3 agora vivem em `config/tickets.yaml`, na chave `b3.tickers`, reutilizada pelo pipeline `examples/b3_runner.py`.
O conjunto foi carregado a partir de `config/IBXX.xlsx` (composição oficial do IBrX-100) e complementado com ETFs/ETNs usados para leitura macro (BOVA11, SMAL11, XFIX11, IMAB11, IRFM11, HASH11, IVVB11, USDB11).

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

## Execução

1. **Yahoo Finance**
   ```bash
   $env:PYTHONPATH = "$PWD"
   python examples/portfolio_runner.py
   ```
   Gera Parquets raw/enriched e um Excel consolidado com indicadores.

2. **B3**
   ```bash
   # Coloque os arquivos COTAHIST_AAAAA.ZIP em data/raw/b3
   $env:PYTHONPATH = "$PWD"
   python examples/b3_runner.py
   ```
   Filtra os tickers definidos na seção `b3.tickers` de `tickets.yaml`, atualiza Parquets raw/enriched em `data/processed/b3` e cria planilhas enriquecidas por ticker em `data/processed/b3/excel`.
