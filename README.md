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
  O runner lê `config/tickets.yaml`, baixa a mesma lista de ativos usada na B3 (composição do IBrX‑100) e os ETFs/ETNs auxiliares de diagnóstico (BOVA11, SMAL11, XFIX11, IMAB11, IRFM11, HASH11, IVVB11, USDB11.SA), salva séries **raw** (`*_raw.parquet`), gera versões **enriched** com indicadores/flags (`*_enriched.parquet`) e cria `carteira_base.xlsx` com uma aba por ativo. Reexecuções são incrementais: apenas o “delta” diário é baixado (ajuste `--workers` para controlar o paralelismo).

6. **Processar arquivos COTAHIST da B3**
   Os arquivos oficiais podem ser baixados no portal de séries históricas da B3: https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/series-historicas/
   ```bash
   # baixe os arquivos COTAHIST_AAAAA.ZIP e coloque em data/raw/b3
   python examples/b3_runner.py
   ```
   O pipeline lê os arquivos, filtra os tickers definidos na seção `b3.tickers` de `config/tickets.yaml` (mesmo universo do Yahoo), atualiza `data/processed/b3` com Parquets raw/enriched e gera planilhas enriquecidas por ticker em `data/processed/b3/excel`. Para ver os resumos técnicos consolidados use o comando `python manage.py snapshot --source b3`.

7. **Exibir snapshots dos dados processados**
   ```bash
   # dados processados via Yahoo
   python manage.py snapshot --source yahoo --tickers PETR4.SA VALE3.SA

   # dados processados via B3 (tickers separados por vírgula ou espaço)
   python manage.py snapshot --source b3 --tickers BOVA11,CEAB3

   # omita --tickers para listar todos os ativos disponíveis na base
   python manage.py snapshot --source b3
   ```
   O comando procura os arquivos `*_enriched.parquet` nas pastas `data/processed/carteira_base` (Yahoo) ou `data/processed/b3` (B3) e imprime o resumo técnico dos ativos solicitados.
   O relatório agora inclui classificação de tendência diária/semanal (ex.: "alta forte", "baixa moderada") considerando o empilhamento das EMAs e a posição em relação à SMA200.

8. **Auditar cobertura e qualidade das séries**
 ```bash
  python manage.py audit --source both --max-gap-yahoo 7 --max-gap-b3 10 --json reports/audit.json
  ```
  O auditor verifica se todos os tickers de `tickets.yaml` possuem dados processados, alerta séries com lacunas acima do limite configurado e (opcionalmente) exporta um JSON consolidado com os alertas.

9. **Gerar rankings e análises**
   ```bash
   python examples/momentum_ranking.py
   ```
   Usa os Parquets em `data/processed/carteira_base` para calcular retornos de 21/63/126 dias e exporta o ranking consolidado.

10. **Explorar exemplos adicionais**
   ```bash
   python examples/manual_smoke.py
   ```

---

## Subprojetos de Dados

- `quantfinance/data/yahoo` – downloads em lote, exportação para Parquet e cache do Yahoo Finance
- `quantfinance/data/b3` – parsers dos arquivos oficiais COTAHIST e persistência para um data lake offline
- `quantfinance/data/profit` – leitura de workbooks do Profit Pro com uma aba por ativo
- `setups/` – catálogo de setups técnicos (médias, RSI, trend following) para documentar hipóteses antes de automatizar backtests/notebooks.

Consulte os README de cada pasta para instruções detalhadas, pressupostos e dicas.

---

## Conceitos Técnicos (evolução atual)

Estamos organizando os conceitos financeiros e de programação em ordem crescente:

- **Médias móveis**: já calculamos SMA/EMA de 9, 21, 72 e 200 períodos. As curtas (9/21) medem ritmo de swing, a 72 reflete ~3 meses e a 200 sinaliza regime de longo prazo.
- **Classificação de tendência**: `trend_strength` avalia inclinação das EMAs e o “stack”. O snapshot traduz isso em “alta/baixa moderada/forte” tanto para o diário quanto para o semanal, usando também a SMA200 como referência.
- **Momentum e divergências**: monitoramos divergências preço × RSI/OBV/MACD em janela curta (15 dias) e calculamos rankings de retornos acumulados (21/63/126 dias) para setups de continuação.
- **Volume e volatilidade**: o snapshot aponta se o volume atual está acima/abaixo da média de 20 dias, interpreta o estocástico lento (%K/%D) e classifica o ATR normalizado (baixa/moderada/elevada), deixando claro se o movimento tem “combustível”, se há ritmo ou excesso.
- **Níveis de preço**: combinamos suportes/resistências diários e semanais, números redondos e swings anteriores, além de retrações/extensões de Fibonacci para mapear alvos.
- **Contexto macro**: calculamos a correlação de 60 dias com ativos de referência (USD/BRL, USDB11, IVVB11, Brent), incorporando ao relatório como o ticker se comporta em relação ao dólar/mercado externo.
- **Auditoria e alertas**: `manage.py audit` gera alertas JSON quando há séries ausentes ou gaps superiores aos limites, permitindo monitoramento diário automatizado.

À medida que evoluirmos (ex.: volatilidade implícita, correlações, backtesting), a documentação será estendida seguindo essa progressão didática.

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
python manage.py yahoo   # baixa via Yahoo conforme tickets.yaml (seção portfolio)
python manage.py b3      # processa arquivos COTAHIST conforme tickets.yaml (seção b3)
python manage.py audit   # valida cobertura dos dados processados e identifica gaps
   python manage.py profit  # placeholder para integração Profit (em desenvolvimento)
   ```

