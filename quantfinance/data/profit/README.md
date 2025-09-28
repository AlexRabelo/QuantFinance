# Pipeline Profit Pro

Utilitários para ler workbooks Excel exportados do Profit Pro com uma aba por ativo.

## Funções Principais

- `load_profit_sheet` – carrega e normaliza uma aba (fusão de Data/Hora opcional)
- `load_profit_workbook` – percorre todas as abas e devolve um dicionário de `DataFrame`

## Fluxo Típico

```python
from quantfinance.data.profit.excel import load_profit_workbook

series = load_profit_workbook("data/raw/profit/export.xlsx")
for ticker, df in series.items():
    print(ticker, df.head())
```

## Observações

- O mapa de renome padrão cobre os cabeçalhos em português emitidos pelo Profit.
- Quando `Hora` está presente, o loader mescla com `Data` para gerar um timestamp completo.
- É possível passar um mapa de renome customizado caso você inclua indicadores adicionais na planilha.
