# QuantFinance

QuantFinance centraliza experimentos de analise tecnica, pesquisa quantitativa e geracao de relatorios para acoes brasileiras e globais. O projeto virou um pacote Python (`quantfinance`) com pipelines modulares de dados, indicadores reutilizaveis e ferramentas de reporte em texto e visual.

---

## Objetivos

- Explorar graficos e indicadores (medias moveis, osciladores, bandas de volatilidade)
- Gerar cenarios a partir de suportes, resistencias, rompimentos e niveis de Fibonacci
- Manter fluxos offline com arquivos oficiais da B3 e exports do Profit Pro
- Evoluir para analises multiativos, estruturas de opcoes e backtesting completo

---

## Estrutura do repositorio

```
QuantFinance/
??? quantfinance/           # Pacote com modulos reutilizaveis
?   ??? data/               # Pipelines de ingestao (Yahoo, B3, Profit)
?   ??? indicators/         # Indicadores tecnicos por tema
?   ??? analysis/           # Niveis de preco, divergencias, tendencia
?   ??? reporting/          # Relatorios textuais e visuais
?   ??? workflows/          # Fluxos prontos (snapshots, auditorias, carteiras)
??? config/                 # Configuracoes (ex.: carteiras de ativos)
??? examples/               # Scripts de exemplo usando o pacote
??? notebooks/              # Notebooks exploratorios
??? setups/                 # Catalogo de setups tecnicos documentados
??? requirements.txt        # Dependencias de runtime
??? manage.py               # CLI principal
??? README.md               # Este arquivo
```

Pastas `data/` e `reports/` sao geradas em tempo de execucao (ja estao no `.gitignore`).

---

## Como come?ar

1. **Instale as dependencias**
   ```bash
   pip install -r requirements.txt
   ```

2. **Monte um snapshot rapido via Yahoo**
   ```python
   from quantfinance.data.providers import download_yfinance
   from quantfinance.workflows.snapshot import snapshot_from_dataframe, print_snapshot

   df = download_yfinance("PETR4.SA", start="2023-01-01")
   snapshot = snapshot_from_dataframe(df)
   print_snapshot(snapshot)
   ```

3. **Renderize um relatorio visual**
   ```python
   from quantfinance.workflows.visualization import plot_full_analysis

    # usa um DataFrame ou arquivo processado local
   fig = plot_full_analysis(df)
   fig.write_html("reports/petr4.html")
   ```

4. **Rodando pipelines principais**
   ```bash
   python manage.py yahoo   # baixa series conforme config/tickets.yaml (secao portfolio)
   python manage.py b3      # processa arquivos COTAHIST conforme config/tickets.yaml (secao b3)
   python manage.py audit   # verifica cobertura das series geradas e aponta gaps
   python manage.py snapshot --source yahoo BOVA11
   ```

5. **Validacao rapida**
   ```bash
   pytest
   ```

---

## Subprojetos de dados

- `quantfinance/data/yahoo` ? download em lote, exportacao para Parquet e cache simples de Yahoo Finance
- `quantfinance/data/b3` ? parsers dos arquivos oficiais COTAHIST e persistencia local
- `quantfinance/data/profit` ? leitura de planilhas exportadas do Profit Pro

Consulte o README de cada pasta para detalhes de parametros, formatos e dicas operacionais.

---

## Conceitos ja implementados

- **Medias moveis**: SMA e EMA de 9/21/72/200 periodos, usadas para ritmo de swing e regime longo prazo.
- **Classificacao de tendencia**: avaliacao do stack de EMAs e posicao vs. SMA200 para gerar labels como "alta forte" ou "baixa moderada".
- **Momentum e divergencias**: divergencias preco x RSI/OBV/MACD em janelas curtas e rankings de retornos (21/63/126 dias).
- **Volume e volatilidade**: comparacao com media de 20 dias, estocastico lento e ATR normalizado.
- **Niveis de preco**: combinacao de suportes/resistencias (intraday e semanal), numeros redondos e Fibonacci.
- **Auditoria**: `manage.py audit` denuncia lacunas de dados e exporta JSON com alertas.

---

## Roadmap imediato

- [ ] Aumentar cobertura de testes para workflows (audit, snapshot, portfolio)
- [ ] Padronizar geracao de dados locais (scripts de limpeza/seed em `data/`)
- [ ] Documentar processo de deploy do pacote como CLI instalavel (`pip install -e .`)
- [ ] Incorporar ajustes corporativos (splits, dividendos) nos loaders
- [ ] Planejar motor de backtesting com custos de transacao e sizing

---

## Contribuicoes

1. Crie uma branch dedicada a melhoria desejada
2. Rode `pytest` antes de abrir o PR
3. Descreva requisitos de dados adicionais (arquivos B3, Profit, etc.) para reproduzir o fluxo

Ideas, issues e melhorias sao sempre bem-vindas.
