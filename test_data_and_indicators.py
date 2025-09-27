import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts')))

import scripts.data_loader as dl
import scripts.indicators as ind

def main():
    # Parâmetros para teste
    excel_file = 'data/PETR4.xlsx'
    ticker = 'PETR4.SA'

    print("Testando leitura do arquivo Excel...")
    rename_cols = {'Data': 'Date', 'Abertura': 'Open', 'Máxima': 'High', 'Mínima': 'Low', 'Fechamento': 'Close', 'Volume Financeiro (Milhoes)': 'Volume'}
    df_excel = dl.carregar_excel(excel_file, date_col='Data', rename_cols=rename_cols)
    print(df_excel.head())
    print(f"Total linhas Excel: {len(df_excel)}")
    print()

    print("Testando download via Yahoo Finance...")
    df_yf = dl.baixar_yfinance(ticker=ticker, start='2023-01-01', end='2025-09-27')
    print(df_yf.head())
    print(f"Total linhas Yahoo Finance: {len(df_yf)}")
    print()

    print("Calculando indicadores sobre dados Excel carregados...")
    df_excel['SMA_20'] = ind.sma(df_excel, 20)
    df_excel['EMA_20'] = ind.ema(df_excel, 20)
    df_excel['RSI_14'] = ind.rsi(df_excel, 14)
    print(df_excel[['Date', 'Close', 'SMA_20', 'EMA_20', 'RSI_14']].tail())
    print()

    print("Calculando indicadores sobre dados Yahoo Finance...")
    df_yf['SMA_20'] = ind.sma(df_yf, 20)
    df_yf['EMA_20'] = ind.ema(df_yf, 20)
    df_yf['RSI_14'] = ind.rsi(df_yf, 14)
    print(df_yf[['Date', 'Close', 'SMA_20', 'EMA_20', 'RSI_14']].tail())

if __name__ == '__main__':
    main()
