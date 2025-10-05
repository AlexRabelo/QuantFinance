# Setups Técnicos

Este diretório reúne ideias de *setups* construídas em cima dos indicadores e
diagnósticos já calculados pelo projeto. A intenção é manter uma referência
organizada para evoluir os estudos de análise técnica e, posteriormente,
transformar em rotinas automatizadas (backtests, dashboards, notebooks).

## Estrutura inicial

- [`moving_average_cross/`](moving_average_cross/README.md) – Estratégias
  baseadas no cruzamento de médias móveis curtas × longas (EMA9/21/72/200,
  SMA200) e confirmação da tendência.
- [`rsi_band/`](rsi_band/README.md) – Setups que exploram as zonas clássicas do
  RSI (30/70) e seus gatilhos de retomada “barato/caro”, com filtro de volume e
  Bollinger.
- [`trend_following/`](trend_following/README.md) – Combinações de sinais
  consagrados (Setups 1, 2, 3 de Larry Williams, rompimentos, pullbacks) para
  navegar em tendências fortes.

Cada subdiretório traz um `README.md` descrevendo hipóteses, indicadores
utilizados, gatilhos de entrada/saída e sugestões de validação.

> **Próximos passos sugeridos**
>
> - Documentar padrões de candles que reforçam continuidade ou reversão (ex.:
>   martelo, engolfo) e como combiná-los com os setups abaixo.
> - Validar estatisticamente cada setup (backtests) e registrar resultados.
> - Evoluir para setups de derivativos (estruturas de opções) usando a mesma
>   abordagem declarativa.
