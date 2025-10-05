# Setups Tecnicos

Este diretorio reune ideias de *setups* construidas em cima dos indicadores e diagnosticos ja calculados pelo projeto. A intencao e manter uma referencia organizada para evoluir os estudos de analise tecnica e, posteriormente, transformar em rotinas automatizadas (backtests, dashboards, notebooks).

## Estrutura inicial

- [`moving_average_cross/`](moving_average_cross/README.md) - Estrategias baseadas no cruzamento de medias moveis curtas e longas (EMA9/21/72/200, SMA200) e confirmacao de tendencia.
- [`rsi_band/`](rsi_band/README.md) - Setups que exploram as zonas classicas do RSI (30/70) e gatilhos de retomada "barato/caro", com filtro de volume e Bollinger.
- [`trend_following/`](trend_following/README.md) - Combinacoes de sinais consagrados (Setups 1, 2, 3 de Larry Williams, rompimentos, pullbacks) para navegar em tendencias fortes.

Cada subdiretorio traz um `README.md` descrevendo hipoteses, indicadores usados, gatilhos de entrada/saida e sugestoes de validacao.

> **Proximos passos sugeridos**
>
> - Documentar padroes de candles que reforcam continuidade ou reversao (ex.: martelo, engolfo) e como combina-los com os setups acima.
> - Validar estatisticamente cada setup (backtests) e registrar resultados.
> - Evoluir para setups de derivativos (estruturas de opcoes) usando a mesma abordagem declarativa.
