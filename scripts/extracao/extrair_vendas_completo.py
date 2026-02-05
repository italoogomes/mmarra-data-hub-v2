# -*- coding: utf-8 -*-
"""
Extrai TODAS as vendas do Sankhya por faixas de NUNOTA.
Salva apenas localmente (sem Azure).
"""

import sys
from pathlib import Path
from datetime import datetime

# Adicionar diretório raiz do projeto ao path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.utils.sankhya_client import SankhyaClient
from src.config import RAW_DATA_DIR


def extrair_vendas_por_faixas(
    client: SankhyaClient,
    nunota_max: int = 2000000,
    faixa_size: int = 10000
) -> pd.DataFrame:
    """
    Extrai vendas em faixas de NUNOTA para contornar limite da API.

    Args:
        client: Cliente Sankhya autenticado
        nunota_max: NUNOTA máximo esperado
        faixa_size: Tamanho de cada faixa

    Returns:
        DataFrame com todas as vendas
    """
    colunas = [
        "NUNOTA", "NUMNOTA", "CODEMP", "CODPARC", "NOMEPARC",
        "DTNEG", "DTFATUR", "VLRNOTA", "PENDENTE", "STATUSNOTA",
        "TIPMOV", "CODTIPOPER", "DESCROPER", "CODVEND", "APELIDO_VEND",
        "CODCENCUS", "SEQUENCIA", "CODPROD", "DESCRPROD", "QTDNEG",
        "VLRUNIT", "VLRTOT", "VLRDESC", "CODLOCALORIG", "CONTROLE", "REFERENCIA"
    ]

    query_template = """
    SELECT
        c.NUNOTA, c.NUMNOTA, c.CODEMP, c.CODPARC, p.NOMEPARC,
        TO_CHAR(c.DTNEG, 'YYYY-MM-DD') AS DTNEG,
        TO_CHAR(c.DTFATUR, 'YYYY-MM-DD') AS DTFATUR,
        c.VLRNOTA, c.PENDENTE, c.STATUSNOTA,
        c.TIPMOV, c.CODTIPOPER, t.DESCROPER, c.CODVEND, v.APELIDO AS APELIDO_VEND,
        c.CODCENCUS, i.SEQUENCIA, i.CODPROD, pr.DESCRPROD, i.QTDNEG,
        i.VLRUNIT, i.VLRTOT, i.VLRDESC, i.CODLOCALORIG, i.CONTROLE, pr.REFERENCIA
    FROM TGFCAB c
    INNER JOIN TGFITE i ON i.NUNOTA = c.NUNOTA
    LEFT JOIN TGFPAR p ON p.CODPARC = c.CODPARC
    LEFT JOIN TGFPRO pr ON pr.CODPROD = i.CODPROD
    LEFT JOIN TGFVEN v ON v.CODVEND = c.CODVEND
    LEFT JOIN (
        SELECT CODTIPOPER, DESCROPER,
               ROW_NUMBER() OVER (PARTITION BY CODTIPOPER ORDER BY DHALTER DESC) AS RN
        FROM TGFTOP
    ) t ON t.CODTIPOPER = c.CODTIPOPER AND t.RN = 1
    WHERE c.TIPMOV = 'V'
      AND c.NUNOTA >= {NUNOTA_INI} AND c.NUNOTA < {NUNOTA_FIM}
    ORDER BY c.NUNOTA, i.SEQUENCIA
    """

    all_dfs = []
    nunota_ini = 0
    total = 0
    faixas_vazias = 0

    print(f"\nExtraindo vendas em faixas de {faixa_size}...")
    print("-" * 60)

    while nunota_ini <= nunota_max:
        nunota_fim = nunota_ini + faixa_size
        query = query_template.format(NUNOTA_INI=nunota_ini, NUNOTA_FIM=nunota_fim)

        try:
            result = client.executar_query(query, timeout=180)
        except Exception as e:
            logger.warning(f"Erro na faixa {nunota_ini}-{nunota_fim}: {e}")
            nunota_ini = nunota_fim
            continue

        if result and result.get("rows"):
            rows = result["rows"]
            df_faixa = pd.DataFrame(rows, columns=colunas)
            all_dfs.append(df_faixa)
            total += len(rows)
            faixas_vazias = 0
            print(f"  NUNOTA {nunota_ini:>7}-{nunota_fim:<7}: +{len(rows):>5} (total: {total:>7})")
        else:
            faixas_vazias += 1
            # Se muitas faixas vazias consecutivas, pular
            if faixas_vazias >= 10:
                print(f"  NUNOTA {nunota_ini:>7}: 10 faixas vazias, pulando 100k...")
                nunota_ini += 100000 - faixa_size
                faixas_vazias = 0

        nunota_ini = nunota_fim

    if not all_dfs:
        return pd.DataFrame(columns=colunas)

    return pd.concat(all_dfs, ignore_index=True)


def main():
    print("=" * 60)
    print("EXTRACAO COMPLETA DE VENDAS")
    print("=" * 60)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Autenticar
    client = SankhyaClient()
    if not client.autenticar():
        print("[ERRO] Falha na autenticacao")
        return 1

    # Extrair
    df = extrair_vendas_por_faixas(client, nunota_max=2000000, faixa_size=10000)

    if df.empty:
        print("[ERRO] Nenhum dado extraido")
        return 1

    print("-" * 60)
    print(f"Total extraido: {len(df)} registros")

    # Converter datas
    if 'DTNEG' in df.columns:
        df['DTNEG'] = pd.to_datetime(df['DTNEG'], errors='coerce')
    if 'DTFATUR' in df.columns:
        df['DTFATUR'] = pd.to_datetime(df['DTFATUR'], errors='coerce')

    # Salvar
    pasta = RAW_DATA_DIR / "vendas"
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = pasta / "vendas.parquet"

    df.to_parquet(arquivo, index=False)

    tamanho_mb = arquivo.stat().st_size / (1024 * 1024)
    print(f"Salvo em: {arquivo}")
    print(f"Tamanho: {tamanho_mb:.2f} MB")

    # Estatísticas
    print("\n" + "=" * 60)
    print("ESTATISTICAS")
    print("=" * 60)
    print(f"Registros: {len(df):,}".replace(",", "."))
    print(f"Produtos unicos: {df['CODPROD'].nunique():,}".replace(",", "."))
    print(f"Clientes unicos: {df['CODPARC'].nunique():,}".replace(",", "."))

    if 'DTNEG' in df.columns and df['DTNEG'].notna().any():
        print(f"Periodo: {df['DTNEG'].min().strftime('%Y-%m-%d')} a {df['DTNEG'].max().strftime('%Y-%m-%d')}")

    print("=" * 60)
    print(f"Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
