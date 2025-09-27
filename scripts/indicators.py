import pandas as pd

def sma(df, window, column='Close'):
    """
    Calcula a Média Móvel Simples (SMA) para uma coluna específica do DataFrame.
    
    Parâmetros:
    - df: pandas DataFrame contendo os dados dos preços.
    - window: número inteiro representando o tamanho da janela (dias) para calcular a média móvel.
    - column: nome da coluna do DataFrame a ser usada para cálculo (default: 'Close').
    
    Retorna:
    - Série pandas com a média móvel simples calculada.
    """
    return df[column].rolling(window=window).mean()

def ema(df, window, column='Close'):
    """
    Calcula a Média Móvel Exponencial (EMA) para uma coluna específica do DataFrame.
    
    Parâmetros:
    - df: pandas DataFrame contendo os dados dos preços.
    - window: número inteiro representando o período da média móvel exponencial.
    - column: nome da coluna para cálculo (default: 'Close').
    
    Retorna:
    - Série pandas com a média móvel exponencial calculada.
    """
    return df[column].ewm(span=window, adjust=False).mean()

def rsi(df, window=14, column='Close'):
    """
    Calcula o Índice de Força Relativa (RSI), indicador que mede a velocidade e mudança dos movimentos de preço.
    
    Parâmetros:
    - df: pandas DataFrame contendo os dados dos preços.
    - window: período para cálculo do RSI, geralmente 14 dias.
    - column: nome da coluna onde está o preço de fechamento (default: 'Close').
    
    Retorna:
    - Série pandas contendo os valores do RSI no período especificado.
    """
    delta = df[column].diff()            # Diferença diária do preço
    gain = delta.where(delta > 0, 0)     # Ganhos diários positivos
    loss = -delta.where(delta < 0, 0)    # Perdas diárias positivas (convertendo para positivo)

    avg_gain = gain.rolling(window=window).mean()  # Média dos ganhos no período
    avg_loss = loss.rolling(window=window).mean()  # Média das perdas no período
    
    rs = avg_gain / avg_loss      # Razão entre ganhos e perdas médias
    rsi = 100 - (100 / (1 + rs))  # Fórmula padrão do RSI
    
    return rsi
