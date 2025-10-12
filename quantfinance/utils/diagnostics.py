"""Utilidades de diagnóstico e saneamento de Parquets (duplicatas/escala)."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple

import pandas as pd


OHLCV_KEYS = ("Open", "High", "Low", "Close", "AdjClose", "Volume")


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        df = df.copy()
        df.columns = [str(col[0] if col[0] else col[1]) for col in df.columns]
    return df


def has_duplicate_columns(df: pd.DataFrame) -> bool:
    return bool(pd.Index(df.columns).duplicated().any())


def coalesce_ohlcv(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Coalesce de colunas duplicadas OHLCV tomando o máximo numérico por linha.

    Retorna (dataframe_saneado, lista_de_ajustes_realizados)
    """
    data = _flatten_columns(df)
    actions: List[str] = []

    for name in OHLCV_KEYS:
        if name not in data.columns:
            continue
        mask = data.columns == name
        if int(mask.sum()) <= 1:
            continue
        subset = data.loc[:, mask]
        # Converte possíveis duplicatas em numérico e escolhe maior valor por linha
        numeric_subset = subset.apply(pd.to_numeric, errors="coerce")
        data[name] = numeric_subset.max(axis=1)
        actions.append(f"coalesce:{name}[{subset.shape[1]}]")

    if actions:
        # remove duplicatas mantendo a primeira ocorrência
        data = data.loc[:, ~data.columns.duplicated()]
    return data, actions


def sanitize_parquet_file(path: Path, *, backup: bool = True) -> Tuple[bool, List[str]]:
    """Saneia um arquivo Parquet no local, opcionalmente gerando backup .bak.

    Retorna (alterado, ações)
    """
    try:
        df = pd.read_parquet(path)
    except Exception as exc:  # pragma: no cover - leitura defensiva
        return False, [f"erro: {exc}"]

    before = has_duplicate_columns(df)
    fixed_df, actions = coalesce_ohlcv(df)
    after = has_duplicate_columns(fixed_df)

    if not actions and not before:
        return False, []

    if backup:
        bak = path.with_suffix(path.suffix + ".bak")
        try:
            path.replace(bak)
            # reescreve o Parquet saneado
            fixed_df.to_parquet(path, index=False)
            return True, actions + [f"backup:{bak.name}"]
        except Exception as exc:  # pragma: no cover
            # tenta restaurar
            try:
                if path.exists():
                    path.unlink(missing_ok=True)
                bak.replace(path)
            finally:
                return False, [f"erro_escrita:{exc}"]
    else:
        fixed_df.to_parquet(path, index=False)
        return True, actions


def scan_and_fix(
    directory: Path,
    patterns: Iterable[str] = ("*.parquet",),
    *,
    fix: bool = False,
    backup: bool = True,
) -> List[Tuple[Path, bool, List[str]]]:
    """Varre o diretório e (opcionalmente) corrige duplicatas de OHLCV nos Parquets.

    Retorna lista de (caminho, alterado, ações)
    """
    results: List[Tuple[Path, bool, List[str]]] = []
    files: List[Path] = []
    for pat in patterns:
        files.extend(sorted(directory.glob(pat)))
    for p in files:
        if fix:
            changed, actions = sanitize_parquet_file(p, backup=backup)
            results.append((p, changed, actions))
        else:
            try:
                df = pd.read_parquet(p)
                dup = has_duplicate_columns(df)
                actions = []
                if dup:
                    actions.append("duplicated_columns")
                results.append((p, False, actions))
            except Exception as exc:  # pragma: no cover
                results.append((p, False, [f"erro_leitura:{exc}"]))
    return results

