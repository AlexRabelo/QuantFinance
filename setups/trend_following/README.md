# Trend Following (Setups 1, 2 e 3)

## Fundamento Teórico

Seguir tendências (“trend following”) é uma das abordagens mais estudadas no
mercado financeiro. Desde as “Turtle Traders” de Richard Dennis (anos 1980) até
Larry Williams, diversos traders demonstraram que movimentos prolongados podem
ser explorados com regras simples, desde que haja disciplina para filtrar sinais
e aceitar stops curtos. Larry Williams popularizou no livro *Long-Term Secrets
to Short-Term Trading* a ideia de três setups básicos (1, 2 e 3) que combinam
rompimentos, pullbacks e divergências.

## Parametrização adotada

- Uso das classificações de tendência diária/semanal disponíveis no snapshot
  (com as EMAs 9/21/72/200).
- Confirmação de volume via `Volume_Ratio` e OBV.
- Combinação com Bollinger, RSI, MACD e Estocástico para filtrar reacelerações
  ou fraquezas.

## Setup 1 – Rompimento com confirmação

- **Condições**:
  - Tendência diária e semanal em “alta forte”.
  - Preço rompe resistência com Bollinger expandindo e volume ≥ média 20d.
  - MACD acima de Signal e Estocástico subindo da região neutra.
- **Estratégia**:
  - Entrada no rompimento; stop abaixo do suporte diário/EMA21.
  - Alvo na resistência semanal ou em projeções de Fibonacci (127%/161%).

## Setup 2 – Reentrada na tendência (pullback)

- **Condições**:
  - Tendência semanal forte; preço corrige até EMA 21 ou banda média.
  - Estocástico sai da sobrevenda; RSI > 50; volume volta para a média.
- **Estratégia**:
  - Entrada na retomada do candle; stop curto abaixo do suporte.
  - Saída parcial quando RSI toca 70 ou banda superior.

## Setup 3 – Reversão monitorada / Redução de posição

- **Condições**:
  - Divergência bearish (RSI/OBV/MACD) + falso rompimento.
  - Preço não sustenta banda superior e volume fraqueja.
- **Estratégia**:
  - Redução de posição ou venda contratendência com stop acima do topo recente.
  - Alvo nos suportes diários (ou retrações 38/50%).

## Retorno Empírico

- Estudos clássicos em índices americanos sugerem que rompimentos confirmados
  por volume têm melhor relação ganho/risco que simples “breakouts”.
- Pullbacks controlados costumam oferecer melhor R/R (stop curto) e alta taxa de
  acerto quando acompanhados por momentum (RSI/Estocástico).
- Sinais de reversão são valiosos para proteger lucros em tendências prolongadas
  e antecipar fases laterais.

## Métricas sugeridas para backtests

- Quantidade de sinais válidos por ano (filtrados por tendência).
- Ganho médio vs. perda média, drawdown e duração média da operação.
- Impacto de filtros adicionais (ex.: contexto macro, divergências).

## Referências

- Dennis, R., & Eckhardt, W. (1983). “Turtle Trading Rules”. Disponível em: https://www.tradingblox.com/originalturtles/rules.htm
- Williams, L. (1998). *Long-Term Secrets to Short-Term Trading*. John Wiley & Sons.
- Covel, M. (2004). *Trend Following: How Great Traders Make Millions in Up or Down Markets*. FT Press.
- Hurst, B., Ooi, Y. H., & Pedersen, L. H. (2017). “A Century of Evidence on Trend-Following Investing”. Journal of Portfolio Management, 44(1), 15-29. https://doi.org/10.3905/jpm.2017.44.1.015
