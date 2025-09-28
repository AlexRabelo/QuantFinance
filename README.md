# QuantFinance

QuantFinance centraliza experimentos de análise técnica, pesquisa quantitativa e geração de relatórios para ações brasileiras e globais. O projeto agora funciona como um pacote Python (`quantfinance`) com pipelines de dados modulares, indicadores reutilizáveis e ferramentas de reporte em texto e visual.

---

## Objetivos do Projeto

- Explorar gráficos e indicadores (médias móveis, osciladores, bandas de volatilidade)
- Gerar cenários a partir de suportes, resistências, rompimentos e níveis de Fibonacci
- Manter fluxos offline com arquivos oficiais da B3 e exports do Profit Pro
- Evoluir para análises multiativos, estruturas de opções e backtesting completo

---

## Estrutura do Repositório

```
QuantFinance/
├── quantfinance/           # Pacote Python com módulos reutilizáveis
│   ├── data/               # Subprojeto: ingestão de dados (Yahoo, B3, Profit)
│   ├── indicators/         # Indicadores técnicos organizados por tema
│   ├── analysis/           # Análises de níveis de preço, divergências e tendência
│   └── reporting/          # Relatórios textuais e visuais
├── scripts/                # Exemplos CLI e camadas de compatibilidade
├── notebooks/              # Notebooks exploratórios
├── data/                   # Dados locais (fora do versionamento)
├── reports/                # Saídas geradas (HTML, imagens)
├── requirements.txt        # Dependências de runtime
└── README.md               # Este arquivo
```

Cada pasta relevante possui um `README.md` próprio descrevendo o fluxo local.

---

## Como Começar

1. **Instalar dependências**
   ```bash
   pip install -r requirements.txt
   ```

2. **Preparar os dados**
   - Use o pipeline do Yahoo (`quantfinance.data.yahoo`) para benchmarks rápidos
   - Monte a base offline da B3 com os parsers `quantfinance.data.b3`
   - Importe exports do Profit Pro via `quantfinance.data.profit`

3. **Gerar insights**
   ```python
   from quantfinance.data.providers import download_yfinance
   from quantfinance.reporting import build_market_snapshot, summarise_snapshot

   df = download_yfinance("PETR4.SA", start="2023-01-01")
   snapshot = build_market_snapshot(df)
   print(summarise_snapshot(snapshot))
   ```

4. **Criar relatórios visuais** com `scripts/visualization.py` ou diretamente com `quantfinance.reporting.plot_full_analysis`.

---

## Subprojetos de Dados

- `quantfinance/data/yahoo` – downloads em lote, exportação para Parquet e cache do Yahoo Finance
- `quantfinance/data/b3` – parsers dos arquivos oficiais COTAHIST e persistência para um data lake offline
- `quantfinance/data/profit` – leitura de workbooks do Profit Pro com uma aba por ativo

Consulte os README de cada pasta para instruções detalhadas, pressupostos e dicas.

---

## Roadmap

- [x] Reorganizar o pacote e o pipeline de relatórios
- [x] Separar a ingestão de dados em Yahoo, B3 e Profit
- [ ] Implementar testes automatizados para loaders, indicadores e análises
- [ ] Incorporar eventos da B3 (splits, dividendos) e preços ajustados
- [ ] Construir um motor de backtesting com sizing e custos de transação
- [ ] Integrar dados de opções e análises de estruturas estruturadas

---

## Contribuindo

1. Faça um fork do repositório e crie uma branch temática
2. Rode os scripts de verificação em `scripts/` ou adicione cobertura `pytest` para novas funcionalidades
3. Abra um pull request explicando a mudança e requisitos de dados adicionais

Estrelas, issues e ideias são muito bem-vindas. Bons trades quantitativos!
