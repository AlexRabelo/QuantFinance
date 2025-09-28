from scipy.signal import argrelextrema
import numpy as np
import pandas as pd

def detectar_suportes_resistencias_locais(df, order=5, column='Close'):
    """
    Detecta níveis locais de suporte (mínimos locais) e resistência (máximos locais) 
    no histórico de preços.

    Parâmetros:
    - df: DataFrame com colunas de preços e índice datetime.
    - order: número de pontos vizinhos para verificar se é pico/local mínimo.
    - column: coluna do preço para análise.

    Retorna:
    - suportes_locais: lista de preços de mínimos locais (suportes).
    - resistencias_locais: lista de preços de máximos locais (resistências).
    """
    # Detecta máximos locais (resistências)
    max_idx = argrelextrema(df[column].values, np.greater_equal, order=order)[0]
    resistencias_locais = df[column].iloc[max_idx].values.tolist()

    # Detecta mínimos locais (suportes)
    min_idx = argrelextrema(df[column].values, np.less_equal, order=order)[0]
    suportes_locais = df[column].iloc[min_idx].values.tolist()

    return suportes_locais, resistencias_locais

def calcular_niveis_especiais(df, column='Close'):
    """
    Calcula níveis especiais de preço que podem atuar como suporte ou resistência:
    mínima e máxima histórica e mínima e máxima móvel de 52 semanas.

    Parâmetros:
    - df: DataFrame com índice datetime.
    - column: coluna do preço para análise.

    Retorna:
    - dicionário com os níveis especiais.
    """
    minima_historica = df[column].min()
    maxima_historica = df[column].max()

    df_semanal = df[column].resample('W').agg(['min','max'])

    minima_52_semanas = df_semanal['min'].rolling(window=52).min().iloc[-1]
    maxima_52_semanas = df_semanal['max'].rolling(window=52).max().iloc[-1]

    return {
        'minima_historica': minima_historica,
        'maxima_historica': maxima_historica,
        'minima_52_semanas': minima_52_semanas,
        'maxima_52_semanas': maxima_52_semanas
    }

def detectar_numeros_redondos(df, interval=5):
    """
    Detecta níveis psicológicos próximos (números redondos) baseado no preço atual.
    Exemplo: múltiplos de 5 ou 10 próximos ao preço médio.

    Parâmetros:
    - df: DataFrame com coluna 'Close'.
    - interval: intervalo para arredondar os números redondos.

    Retorna:
    - lista de níveis arredondados próximos.
    """
    preco_medio = df['Close'].mean()
    arredondados = list(range(int(preco_medio - interval * 5), int(preco_medio + interval * 5 + 1), interval))
    return arredondados

def detectar_todos_niveis(df, order=5, column='Close', intervalo_redondo=5):
    """
    Função consolidada para detectar todos os níveis importantes:
    suporta e resistências locais, níveis especiais e números redondos.

    Retorna dicionário com todas as listas e valores.
    """
    suportes_locais, resistencias_locais = detectar_suportes_resistencias_locais(df, order=order, column=column)
    niveis_especiais = calcular_niveis_especiais(df, column=column)
    numeros_redondos = detectar_numeros_redondos(df, interval=intervalo_redondo)

    return {
        'suportes_locais': suportes_locais,
        'resistencias_locais': resistencias_locais,
        'minima_historica': niveis_especiais['minima_historica'],
        'maxima_historica': niveis_especiais['maxima_historica'],
        'minima_52_semanas': niveis_especiais['minima_52_semanas'],
        'maxima_52_semanas': niveis_especiais['maxima_52_semanas'],
        'numeros_redondos': numeros_redondos
    }
