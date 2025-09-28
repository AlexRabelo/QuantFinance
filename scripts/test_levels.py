import sys
import os

# Adiciona a raiz do projeto ao PATH para encontrar o pacote scripts
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import scripts.levels as levels

def exemplo_uso_niveis():
    # Ajuste o caminho do arquivo Excel conforme o seu projeto
    df = pd.read_excel('data/PETR4.xlsx')
    df.rename(columns={'Data': 'Date', 'Fechamento': 'Close'}, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    df.sort_index(inplace=True)

    niveis = levels.detectar_todos_niveis(df, order=5, column='Close', intervalo_redondo=5)

    print("Suportes locais:", niveis['suportes_locais'])
    print("Resistências locais:", niveis['resistencias_locais'])
    print("Mínima histórica:", niveis['minima_historica'])
    print("Máxima histórica:", niveis['maxima_historica'])
    print("Mínima 52 semanas:", niveis['minima_52_semanas'])
    print("Máxima 52 semanas:", niveis['maxima_52_semanas'])
    print("Números redondos próximos:", niveis['numeros_redondos'])

if __name__ == '__main__':
    exemplo_uso_niveis()
