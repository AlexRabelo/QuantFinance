import pandas as pd
import yfinance as yf

def carregar_csv(file_path, date_col='Date', rename_cols=None):
    """
    Lê um arquivo CSV contendo dados financeiros históricos, faz parsing da data e renomeia colunas.

    Parâmetros:
    - file_path: caminho do arquivo CSV
    - date_col: nome da coluna de data para parsing (default: 'Date')
    - rename_cols: dicionário para renomear colunas {nome_antigo: nome_novo}

    Retorna:
    DataFrame pandas com colunas padronizadas e coluna Date em datetime.
    """
    df = pd.read_csv(file_path, parse_dates=[date_col])
    if rename_cols:
        df.rename(columns=rename_cols, inplace=True)
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df.dropna(subset=[date_col], inplace=True)
    return df

def carregar_excel(file_path, date_col='Data', rename_cols=None):
    """
    Lê um arquivo Excel contendo dados financeiros históricos, faz parsing da data e renomeia colunas.

    Parâmetros:
    - file_path: caminho do arquivo Excel
    - date_col: nome da coluna de data original para parsing (ex: 'Data')
    - rename_cols: dicionário para renomear colunas após o parsing
    
    Retorna:
    DataFrame pandas com colunas padronizadas e coluna Date em datetime.
    """
    df = pd.read_excel(file_path)

    # Convertendo antes de renomear
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
    df.dropna(subset=[date_col], inplace=True)

    # Renomear colunas depois
    if rename_cols:
        df.rename(columns=rename_cols, inplace=True)
    
    return df


def baixar_yfinance(ticker, start=None, end=None, interval='1d', auto_adjust=True):
    """
    Baixa dados históricos via yfinance para o ticker informado.

    Parâmetros:
    - ticker: código do ativo, ex: 'PETR4.SA'
    - start: data inicial string 'AAAA-MM-DD'
    - end: data final string 'AAAA-MM-DD'
    - interval: intervalo dos dados ('1d', '1wk', '1mo', etc)
    - auto_adjust: se ajusta os preços automaticamente

    Retorna:
    DataFrame com colunas padronizadas: ['Date','Open','High','Low','Close','Volume']
    """
    df = yf.download(ticker, start=start, end=end, interval=interval, auto_adjust=auto_adjust)
    df.reset_index(inplace=True)
    # Garantir nomes padronizados
    df.rename(columns={
        'Date': 'Date',
        'Open': 'Open',
        'High': 'High',
        'Low': 'Low',
        'Close': 'Close',
        'Volume': 'Volume'
    }, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    return df
