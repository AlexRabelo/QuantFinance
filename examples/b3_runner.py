"""Executa o pipeline da B3 usando os arquivos COTAHIST presentes em data/raw/b3.

Os arquivos oficiais podem ser baixados no portal de séries históricas da B3:
https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/series-historicas/
"""

from __future__ import annotations

from quantfinance.workflows import run_b3_pipeline


def main() -> None:
    run_b3_pipeline()


if __name__ == "__main__":
    main()
