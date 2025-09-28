import sys
import os

# Adiciona a raiz do projeto ao PATH para encontrar o pacote scripts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import scripts.indicators as ind

def plot_full_analysis(df):
    os.makedirs('reports', exist_ok=True)

    df = ind.calculate_all_moving_averages(df)
    df['RSI_14'] = ind.rsi(df, 14)
    macd_df = ind.macd(df)
    df = pd.concat([df, macd_df], axis=1)
    bb_df = ind.bollinger_bands(df, window=21)  # ajustado para 21
    df = pd.concat([df, bb_df], axis=1)

    # Criar figura com 4 linhas
    fig = make_subplots(
        rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.03,
        row_heights=[0.4, 0.1, 0.25, 0.25],
        subplot_titles=('Preço com Médias e Bollinger', 'Volume', 'MACD', 'RSI')
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df['Date'], open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name='Preço'), row=1, col=1)

    # Médias móveis SMA 9,21,72
    for ma in ['SMA_9', 'SMA_21', 'SMA_72']:
        fig.add_trace(go.Scatter(x=df['Date'], y=df[ma], mode='lines', name=ma), row=1, col=1)

    # Médias móveis EMA 9,21,72
    for ma in ['EMA_9', 'EMA_21', 'EMA_72']:
        fig.add_trace(go.Scatter(x=df['Date'], y=df[ma], mode='lines', name=ma, line=dict(dash='dash')), row=1, col=1)

    # Bandas de Bollinger
    fig.add_trace(go.Scatter(x=df['Date'], y=df['UpperBand'], mode='lines', name='BB Upper', line=dict(color='rgba(255,0,0,0.2)')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MiddleBand'], mode='lines', name='BB Middle', line=dict(color='rgba(0,0,0,0.2)')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['LowerBand'], mode='lines', name='BB Lower', line=dict(color='rgba(0,0,255,0.2)')), row=1, col=1)

    # Volume
    fig.add_trace(go.Bar(x=df['Date'], y=df['Volume'], name='Volume'), row=2, col=1)

    # MACD + Signal + Histogram
    fig.add_trace(go.Scatter(x=df['Date'], y=df['MACD'], mode='lines', name='MACD'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Signal'], mode='lines', name='Signal'), row=3, col=1)
    fig.add_trace(go.Bar(x=df['Date'], y=df['Histogram'], name='Histogram'), row=3, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=df['Date'], y=df['RSI_14'], mode='lines', name='RSI'), row=4, col=1)
    fig.add_hline(y=70, line_dash='dash', line_color='red', row=4, col=1)
    fig.add_hline(y=30, line_dash='dash', line_color='green', row=4, col=1)

    fig.update_layout(
        height=900,
        title_text='Análise Técnica Completa',
        xaxis_rangeslider_visible=False,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )

    fig.update_yaxes(title_text='Preço', row=1, col=1)
    fig.update_yaxes(title_text='Volume', row=2, col=1)
    fig.update_yaxes(title_text='MACD', row=3, col=1)
    fig.update_yaxes(title_text='RSI', row=4, col=1, range=[0, 100])

    html_file = 'reports/grafico_completo.html'
    fig.write_html(html_file)
    print(f"Gráfico salvo em {html_file}. Abra no navegador para visualizar.")

def main():
    file_path = 'data/PETR4.xlsx'
    df = pd.read_excel(file_path)
    df.rename(columns={'Data': 'Date', 'Abertura': 'Open', 'Máxima': 'High', 
                       'Mínima': 'Low', 'Fechamento': 'Close', 'Volume Financeiro (Milhoes)': 'Volume'}, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df.sort_values('Date', inplace=True)

    plot_full_analysis(df)

if __name__ == '__main__':
    main()
