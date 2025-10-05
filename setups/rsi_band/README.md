# RSI em Faixas (30/70)

## Fundamento Teórico

O Relative Strength Index (RSI) foi desenvolvido por J. Welles Wilder em 1978
com o objetivo de medir a velocidade e a mudança de movimentos de preço. As
faixas de 30 (sobrevenda) e 70 (sobrecompra) ficaram populares porque sinalizam
extremos de curto prazo – ideia reforçada por analistas como Linda Raschke e
Andrew Cardwell, que defendem o uso do RSI para detectar “reacelerações” em
mercados tendenciais.

Em termos matemáticos, o RSI é calculado como `100 - 100 / (1 + RS)`, onde `RS`
é a média dos ganhos dividida pela média das perdas em uma janela (14 períodos
por convenção). Cruza 30 ou 70 quando há mudança de equilíbrio entre ganhos e
perdas recentes.

## Parametrização adotada

- **Período**: 14 dias (padrão Wilder).
- **Faixas**: 30/70 (pode-se testar 20/80 em ativos mais voláteis).
- **Filtros**: tendência semanal (evitar operar contra tendências fortes),
  volume/OBV, Bollinger para confirmar se há estiramento do preço.

## Setups Propostos

1. **Compra em sobrevenda (RSI Rebound)**
   - RSI cruza de baixo para cima a faixa 30.
   - Tendência semanal neutra/positiva e volume voltando para a média.
   - Saída na SMA 21 ou nas resistências próximas.

2. **Venda em sobrecompra**
   - RSI cruza de cima para baixo a faixa 70 ou 80.
   - Divergências de MACD/OBV reforçam o sinal de exaustão.

3. **Faixa 50 como suporte/resistência**
   - Em tendência de alta, comprar quando o RSI recua até 40–50 e volta a subir.
   - Em tendência de baixa, vender quando sobe até 50–60 e retorna.

## Retorno Empírico

- Larry Connors popularizou o “RSI 2/3 dias” em índices americanos, mostrando
  que compras em sobrevenda têm alto percentual de acerto quando combinadas com
  filtros de tendência.
- No mercado brasileiro, estudos simples indicam que cruzamentos em 30/70 perdem
  eficiência se usados isoladamente; filtros de tendência diária/semanal e
  volume reduzem falsos sinais.

## Métricas para Backtest

- Taxa de acerto do cruzamento 30→40 versus 30→50.
- Retorno médio até atingir RSI 50/70 (swing curto) e ratio ganho/risco.
- Número de sinais falsos quando o RSI cruza 30, mas o OBV aponta divergência
  negativa.

## Referências

- Wilder, J. W. (1978). *New Concepts in Technical Trading Systems*. Greensboro: Trend Research.
- Connors, L., & Raschke, L. (1995). *Street Smarts: High Probability Short-Term Trading Strategies*. Windsor Books.
- Cardwell, A. (1993). “Relative Strength Index: The Complete Guide”. RSI Edge.
- Sweeney, R. J. (1988). *Some New Filter Rule Tests: Methods and Results*. Journal of Financial and Quantitative Analysis, 23(3), 285-300. https://doi.org/10.2307/2331063
