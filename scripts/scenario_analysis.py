import sys
import os

# Ajuste do path para importar módulos locais da pasta scripts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import scripts.levels as levels
import scripts.indicators as ind

def agrupar_niveis(niveis, tolerancia_pct=0.5):
    if not niveis:
        return []
    niveis = sorted(niveis)
    agrupados = []
    grupo_atual = [niveis[0]]
    for nivel in niveis[1:]:
        ultimo = grupo_atual[-1]
        if abs(nivel - ultimo) / ultimo * 100 <= tolerancia_pct:
            grupo_atual.append(nivel)
        else:
            agrupados.append(sum(grupo_atual)/len(grupo_atual))
            grupo_atual = [nivel]
    agrupados.append(sum(grupo_atual)/len(grupo_atual))
    return agrupados

def gerar_insights(preco_atual, niveis, indicadores):
    tolerancia = preco_atual * 0.005  # 0.5% do preço
    def perto_de_lista(valor, lista):
        return any(abs(valor - x) <= tolerancia for x in lista)
    insights = []
    if perto_de_lista(preco_atual, niveis['suportes_locais']):
        insights.append("Preço próximo a um suporte local importante.")
    if preco_atual <= niveis['minima_52_semanas'] * 1.01:
        insights.append("Preço próximo da mínima em 52 semanas, possível zona de compra.")
    if preco_atual <= niveis['minima_historica'] * 1.01:
        insights.append("Preço próximo da mínima histórica, atenção redobrada.")
    if perto_de_lista(preco_atual, niveis['resistencias_locais']):
        insights.append("Preço próximo a uma resistência local importante.")
    if preco_atual >= niveis['maxima_52_semanas'] * 0.99:
        insights.append("Preço próximo da máxima em 52 semanas, possível pressão para venda.")
    if preco_atual >= niveis['maxima_historica'] * 0.99:
        insights.append("Preço próximo da máxima histórica, monitorar sinais de reversão.")
    rsi = indicadores.get('RSI_14')
    if rsi is not None:
        if rsi >= 70:
            insights.append("RSI indica sobrecompra, possibilidade de correção.")
        elif rsi <= 30:
            insights.append("RSI indica sobrevenda, possibilidade de recuperação.")
    if not insights:
        insights.append("Preço está em zona neutra, sem sinais de suporte ou resistência próximos relevantes.")
    return '\n'.join(insights)

def niveis_proximos(preco_atual, suportes, resistencias, max_resultados=3):
    def mais_proximos(preco, niveis, n):
        niveis_sorted = sorted(niveis, key=lambda x: abs(x - preco))
        return niveis_sorted[:n]
    prox_suportes = mais_proximos(preco_atual, suportes, max_resultados)
    prox_resistencias = mais_proximos(preco_atual, resistencias, max_resultados)
    return {
        'suportes_proximos': prox_suportes,
        'resistencias_proximas': prox_resistencias
    }

def main():
    # Carregar dados do Excel e preparar DataFrame
    df = pd.read_excel('data/PETR4.xlsx')
    df.rename(columns={'Data': 'Date', 'Fechamento': 'Close'}, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    df = df.sort_index()

    # Calcular indicadores (exemplo RSI)
    df['RSI_14'] = ind.rsi(df, 14)

    # Detectar níveis totais
    niveis_brutos = levels.detectar_todos_niveis(df, order=5, column='Close', intervalo_redondo=5)

    # Agrupar níveis de suporte, resistência e números redondos
    niveis = {}
    for chave in ['suportes_locais', 'resistencias_locais', 'numeros_redondos']:
        niveis[chave] = agrupar_niveis(niveis_brutos[chave])
    for chave in ['minima_historica', 'maxima_historica', 'minima_52_semanas', 'maxima_52_semanas']:
        niveis[chave] = niveis_brutos[chave]

    preco_atual = df['Close'].iloc[-1]
    indicadores_atuais = {'RSI_14': df['RSI_14'].iloc[-1]}

    texto_insights = gerar_insights(preco_atual, niveis, indicadores_atuais)
    proximos = niveis_proximos(preco_atual, niveis['suportes_locais'], niveis['resistencias_locais'])

    print(f"Preço Atual: {preco_atual}")
    print("Insights sobre cenário:")
    print(texto_insights)
    print("Suportes mais próximos:", proximos['suportes_proximos'])
    print("Resistências mais próximas:", proximos['resistencias_proximas'])

if __name__ == '__main__':
    main()
