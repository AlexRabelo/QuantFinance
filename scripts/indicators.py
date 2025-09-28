import pandas as pd

def sma(df, window, column='Close'):
    return df[column].rolling(window=window).mean()

def ema(df, window, column='Close'):
    return df[column].ewm(span=window, adjust=False).mean()

def rsi(df, window=14, column='Close'):
    delta = df[column].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_all_moving_averages(df, column='Close'):
    df['SMA_9'] = sma(df, 9, column)
    df['SMA_21'] = sma(df, 21, column)
    df['SMA_72'] = sma(df, 72, column)
    df['EMA_9'] = ema(df, 9, column)
    df['EMA_21'] = ema(df, 21, column)
    df['EMA_72'] = ema(df, 72, column)
    return df

def macd(df, short_window=12, long_window=26, signal_window=9, column='Close'):
    ema_short = df[column].ewm(span=short_window, adjust=False).mean()
    ema_long = df[column].ewm(span=long_window, adjust=False).mean()
    macd_line = (ema_short - ema_long).squeeze()
    signal_line = macd_line.ewm(span=signal_window, adjust=False).mean().squeeze()
    histogram = (macd_line - signal_line).squeeze()
    return pd.DataFrame({
        'MACD': macd_line,
        'Signal': signal_line,
        'Histogram': histogram
    }, index=df.index)

def bollinger_bands(df, window=21, num_std=2, column='Close'):
    sma_val = df[column].rolling(window=window).mean()
    std = df[column].rolling(window=window).std()
    upper_band = sma_val + (std * num_std)
    lower_band = sma_val - (std * num_std)
    return pd.DataFrame({
        'MiddleBand': sma_val,
        'UpperBand': upper_band,
        'LowerBand': lower_band
    }, index=df.index)
