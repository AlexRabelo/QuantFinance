import sys
import os
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts')))

import scripts.data_loader as dl
import scripts.indicators as ind

def main():
    # Parâmetros para teste
    excel_file = 'data/PETR4.xlsx'
    ticker = 'PETR4.SA'

    print("Testando leitura do arquivo Excel...")
    rename_cols = {
        'Data': 'Date', 'Abertura': 'Open', 'Máxima': 'High',
        'Mínima': 'Low', 'Fechamento': 'Close',
        'Volume Financeiro (Milhoes)': 'Volume'
    }
    df_excel = dl.carregar_excel(excel_file, date_col='Data', rename_cols=rename_cols)
    print(df_excel.head())
    print(f"Total linhas Excel: {len(df_excel)}\n")

    print("Testando download via Yahoo Finance...")
    df_yf = dl.baixar_yfinance(ticker=ticker, start='2023-01-01', end='2025-09-27')

    # Ajuste colunas multi-índice do Yahoo Finance
    if isinstance(df_yf.columns, pd.MultiIndex):
        df_yf.columns = df_yf.columns.get_level_values(1)
    if 'Date' not in df_yf.columns:
        df_yf.reset_index(inplace=True)

    print(df_yf.head())
    print(f"Total linhas Yahoo Finance: {len(df_yf)}\n")

    print("Calculando indicadores sobre dados Excel carregados...")
    df_excel['SMA_21'] = ind.sma(df_excel, 21)
    df_excel['EMA_21'] = ind.ema(df_excel, 21)
    df_excel['RSI_14'] = ind.rsi(df_excel, 14)

    macd_df = ind.macd(df_excel)
    df_excel = pd.concat([df_excel, macd_df], axis=1)

    bb_df = ind.bollinger_bands(df_excel)
    df_excel = pd.concat([df_excel, bb_df], axis=1)

    cols_to_show = ['Date', 'Close', 'SMA_21', 'EMA_21', 'RSI_14', 'MACD', 'Signal', 'Histogram', 'MiddleBand', 'UpperBand', 'LowerBand']
    print(df_excel[cols_to_show].tail())
    print()

    print("Calculando indicadores sobre dados Yahoo Finance...")
    df_yf['SMA_21'] = ind.sma(df_yf, 21)
    df_yf['EMA_21'] = ind.ema(df_yf, 21)
    df_yf['RSI_14'] = ind.rsi(df_yf, 14)

    macd_df = ind.macd(df_yf)
    df_yf = pd.concat([df_yf, macd_df], axis=1)

    bb_df = ind.bollinger_bands(df_yf)
    df_yf = pd.concat([df_yf, bb_df], axis=1)

    print(df_yf[cols_to_show].tail())

if __name__ == '__main__':
    main()
