# Exemplos de Uso

Scripts simples para exercitar o pacote `quantfinance` sem precisar navegar pelo código fonte.

- `manual_smoke.py` – execução manual que baixa dados do Yahoo, calcula indicadores básicos e imprime um snapshot consolidado.
- `momentum_ranking.py` – gera um ranking de momentum (21/63/126 dias) usando os Parquets já baixados em `data/processed/carteira_base`.

Execute com:

```bash
python examples/manual_smoke.py
```

Adapte os exemplos como ponto de partida para notebooks ou fluxos automatizados.
