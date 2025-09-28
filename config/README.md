# Configurações de Carteira

Arquivos YAML que descrevem carteiras de ativos para download automatizado.

## Yahoo Finance

Usa `config/carteira_base.yaml` com os tickers trabalhados no pipeline do Yahoo (`examples/portfolio_runner.py`).

## B3 (COTAHIST)

`config/carteira_b3.yaml` lista os ativos que serão extraídos ao processar arquivos COTAHIST (`examples/b3_runner.py`).

```yaml
carteira:
  tickers:
    - PETR4
    - VALE3
    - BOVA11
    # ... demais ativos desejados
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
   Filtra os tickers definidos em `carteira_b3.yaml`, atualiza Parquets raw/enriched em `data/processed/b3` e cria planilhas enriquecidas por ticker em `data/processed/b3/excel`.
