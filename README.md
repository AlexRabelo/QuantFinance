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
│   ├── data/               # Pipelines de ingestão (Yahoo, B3, Profit)
│   ├── indicators/         # Indicadores técnicos organizados por tema
│   ├── analysis/           # Níveis de preço, divergências e tendência
│   ├── reporting/          # Relatórios textuais e visuais
│   └── workflows/          # Fluxos prontos (snapshots, relatórios, carteiras)
├── config/                 # Configurações (ex.: carteiras de ativos)
├── examples/               # Exemplos manuais de uso do pacote
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

3. **Gerar insights para um ativo**
   ```python
   from quantfinance.data.providers import download_yfinance
   from quantfinance.workflows import snapshot_from_dataframe, print_snapshot

   df = download_yfinance("PETR4.SA", start="2023-01-01")
   snapshot = snapshot_from_dataframe(df)
   print_snapshot(snapshot)
   ```

4. **Criar relatórios visuais**
   ```python
   from quantfinance.workflows import render_visual_report

   render_visual_report("data/PETR4.xlsx")
   ```

5. **Coletar dados de uma carteira via Yahoo Finance**
   ```bash
   pip install -r requirements.txt
   $env:PYTHONPATH = "$PWD"   # PowerShell; em cmd use set PYTHONPATH=%CD%
   python examples/portfolio_runner.py
   ```
   O runner lê `config/carteira_base.yaml`, baixa os ativos suportados pelo Yahoo, salva séries **raw** (`*_raw.parquet`), gera versões **enriched** com indicadores/flags (`*_enriched.parquet`) e cria `carteira_base.xlsx` com uma aba por ativo.

6. **Processar arquivos COTAHIST da B3**
   Os arquivos oficiais podem ser baixados no portal de séries históricas da B3: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/series-historicas/
   ```bash
   # baixe os arquivos COTAHIST_AAAAA.ZIP e coloque em data/raw/b3
   python examples/b3_runner.py
   ```
   O pipeline lê os arquivos, filtra os tickers definidos em `config/carteira_b3.yaml`, atualiza `data/processed/b3` com Parquets raw/enriched e gera planilhas enriquecidas por ticker em `data/processed/b3/excel`.

7. **Explorar exemplos**
   ```bash
   python examples/manual_smoke.py
   ```

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
- [x] Substituir scripts antigos por fluxos em `quantfinance.workflows`
- [x] Introduzir carteiras configuráveis via YAML + enriquecimento de indicadores
- [x] Adicionar pipeline filtrado para arquivos COTAHIST da B3
- [ ] Implementar testes automatizados para loaders, indicadores e análises
- [ ] Incorporar eventos da B3 (splits, dividendos) e preços ajustados
- [ ] Construir um motor de backtesting com sizing e custos de transação
- [ ] Integrar dados de opções e análises de estruturas estruturadas

---

## Contribuindo

1. Faça um fork do repositório e crie uma branch temática
2. Rode os exemplos ou adicione cobertura `pytest` para novas funcionalidades
3. Abra um pull request explicando a mudança e requisitos de dados adicionais

Estrelas, issues e ideias são muito bem-vindas. Bons trades quantitativos!

8. **Executar via linha de comando (manage.py)**
   ```bash
   python manage.py yahoo   # baixa via Yahoo conforme carteira_base.yaml
   python manage.py b3      # processa arquivos COTAHIST conforme carteira_b3.yaml
   python manage.py profit  # placeholder para integração Profit (em desenvolvimento)
   ```

