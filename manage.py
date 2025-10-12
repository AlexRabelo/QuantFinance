#!/usr/bin/env python3

from quantfinance.cli import app
try:
    # Anexa comandos estendidos sem alterar o CLI principal
    from quantfinance.cli_ext import register as _register_cli_ext

    _register_cli_ext(app)
except Exception:
    # Registro opcional; falhas não devem quebrar o CLI base
    pass

if __name__ == "__main__":
    app()

