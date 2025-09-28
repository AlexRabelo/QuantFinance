# Subprojeto de Dados

Centraliza todos os pipelines de dados utilizados pelo pacote QuantFinance. Cada pasta oferece carregadores, rotinas de limpeza e utilitários de persistência para uma fonte específica.

## Layout

- `core.py` – utilidades comuns (normalização de datas, leitores genéricos de CSV/Excel)
- `io.py` – camadas de compatibilidade usadas por scripts e notebooks legados
- `providers.py` – fachada que expõe os provedores ativos para o restante do código
- `yahoo/` – download e cache para Yahoo Finance
- `b3/` – ingestão offline dos arquivos COTAHIST da B3
- `profit/` – leitores para exports do Profit Pro (aba única ou múltiplas)

## Boas Práticas

- Em código novo, prefira chamar os módulos especializados (`yahoo`, `b3`, `profit`).
- Use `providers.download_yfinance_batch` para preencher um cache local de vários tickers.
- Combine `b3.cotahist.save_daily_history` com um agendador (cron, Prefect) para manter o lake offline atualizado.
- Notebooks antigos podem continuar usando `scripts/data_loader.py`, que redireciona para este pacote.

## Próximos Passos Sugeridos

1. Adicionar verificações automatizadas (dias ausentes, preços negativos).
2. Guardar metadados de proveniência (nome do arquivo, checksum, data de ingestão) junto dos Parquets.
3. Suportar arquivos de eventos da B3 (dividendos, splits) para construir séries ajustadas.
