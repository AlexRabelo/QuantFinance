-# Cruzamento de Médias

## Fundamento Teórico

O cruzamento de médias móveis é um dos métodos mais antigos e difundidos para
identificar mudanças de regime. A versão “Golden Cross” (média curta cruzando
para cima a média longa) ganhou notoriedade na década de 1970 por investidores
como Richard Donchian e, posteriormente, apareceu em estudos do *Market
Technician Association*. A ideia central é que o preço médio mais recente (curto
prazo) confirma uma inversão de tendência quando passa a superar o preço médio
de longo prazo. O inverso (“Death Cross”) sinaliza perda de força e início de
movimento baixista.

Matematicamente, o cruzamento ocorre quando a diferença entre as médias muda de
sinal. Esse evento pode ser visto como a resolução de uma equação simples
`SMA_curta - SMA_longa = 0`. Em séries com ruído, cruzamentos muito curtos
geram falsos positivos; por isso filtramos o contexto (tendência diária/semanal
e volume).

## Parametrização adotada

- **Médias móveis**: EMA 9, 21, 72, 200 e SMA 200 (configuráveis).
- **Condicionantes auxiliares**:
  - Tendência diária/semanal classificada como “alta moderada/forte” para sinais
    de compra; “baixa moderada/forte” para venda.
  - Volume Ratio ≥ 1 (volume atual acima da média 20d) para reforçar breaks.
  - OBV/RSI divergindo pode ser usado como alerta de saída.

## Variações do Setup

1. **Golden Cross / Death Cross (EMA 21 × 72)**
   - *Compra*: EMA 21 cruza acima da EMA 72, preço acima da SMA 200 e volume em
     linha. Clássico para swing de médio prazo.
   - *Venda*: EMA 21 cruza abaixo da EMA 72 em ambiente de baixa.

2. **Cruzamento rápido (EMA 9 × 21)**
   - Sinal mais sensível. Costuma antecipar mudanças, mas precisa de filtros
     (Bollinger, RSI) para evitar ruído.

3. **Pullback na média curta**
   - Após o cruzamento “Golden”, esperar correção até EMA 9/21 e entrada com
     estocástico saindo de sobrevenda.

4. **Stack completo (EMA 9 > 21 > 72 > SMA 200)**
   - Só operar no sentido da tendência quando todas as médias estiverem
     alinhadas. Corrige o problema de “whipsaw”.

## Retorno Empírico (ideias)

Estudos clássicos mostram que o Golden Cross no S&P 500 (200 vs 50 períodos)
tem desempenho superior ao *buy and hold* apenas quando combinado com filtros de
volatilidade. Para o mercado brasileiro, testes simples mostram que:

- Filtrar pelos sinais de volume melhora a relação ganho/risco.
- Cruzamentos curtos (9×21) funcionam melhor em ativos com alta liquidez e
  volatilidade moderada.
- O alinhamento com a tendência semanal reduz falsos positivos.

## Métricas para Backtest

- Percentual de cruzamentos que viram tendência (preço continua a favor ≥ X%).
- Relação ganho/perda usando suporte/resistência como alvo.
- Tempo médio até desmontagem do sinal (até EMA 9 cruzar de volta).
- Número de falsos positivos com volume abaixo da média.

## Referências

- Donchian, R. (1970). *Trading Rules that Work*. Commodity Traders Consumer Report.
- Murphy, J. J. (1999). *Technical Analysis of the Financial Markets*. New York: New York Institute of Finance.
- MTA Technician (2010). “Golden Crosses & Death Crosses”. Market Technicians Association. Disponível em: https://cmtassociation.org/wp-content/uploads/2012/09/Golden-Crosses.pdf
- Brock, W., Lakonishok, J., & LeBaron, B. (1992). *Simple Technical Trading Rules and the Stochastic Properties of Stock Returns*. Journal of Finance, 47(5), 1731-1764. https://doi.org/10.1111/j.1540-6261.1992.tb04681.x
