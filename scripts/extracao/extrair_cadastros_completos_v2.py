# -*- coding: utf-8 -*-
"""
Extrai cadastros COMPLETOS do Sankhya usando filtros por faixa
(API limita 5000 por consulta, contornamos dividindo por faixas)
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.utils.sankhya_client import SankhyaClient
from src.utils.azure_storage import AzureDataLakeClient
from src.config import RAW_DATA_DIR


def extrair_por_faixas(
    client: SankhyaClient,
    query_template: str,
    campo_id: str,
    colunas: list,
    nome: str,
    id_max: int,
    faixa_size: int = 50000
) -> pd.DataFrame:
    """
    Extrai dados dividindo por faixas de ID.

    Args:
        client: Cliente Sankhya
        query_template: Query com {WHERE_FAIXA} para substituir
        campo_id: Campo de ID para filtrar (ex: CODPROD)
        colunas: Lista de nomes das colunas
        nome: Nome para log
        id_max: ID maximo estimado
        faixa_size: Tamanho de cada faixa

    Returns:
        DataFrame com todos os dados
    """
    all_dfs = []
    faixa = 1
    id_inicio = 0

    while id_inicio <= id_max:
        id_fim = id_inicio + faixa_size

        where_faixa = f"{campo_id} >= {id_inicio} AND {campo_id} < {id_fim}"
        query = query_template.replace("{WHERE_FAIXA}", where_faixa)

        result = client.executar_query(query, timeout=180)

        if result and result.get("rows"):
            rows = result["rows"]
            df_faixa = pd.DataFrame(rows, columns=colunas)
            all_dfs.append(df_faixa)
            print(f"    Faixa {faixa} ({id_inicio}-{id_fim}): {len(rows)} registros")
        else:
            print(f"    Faixa {faixa} ({id_inicio}-{id_fim}): 0 registros")

        id_inicio = id_fim
        faixa += 1

    if not all_dfs:
        return pd.DataFrame(columns=colunas)

    return pd.concat(all_dfs, ignore_index=True)


def main():
    print("=" * 70)
    print("EXTRACAO COMPLETA DE CADASTROS - V2 (POR FAIXAS)")
    print("=" * 70)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Autenticar
    client = SankhyaClient()
    if not client.autenticar():
        print("[ERRO] Falha na autenticacao")
        return 1

    azure = AzureDataLakeClient()

    # ========================================
    # 1. VENDEDORES (pequeno, sem faixa)
    # ========================================
    print(f"\n{'='*70}")
    print(">>> VENDEDORES")
    print("=" * 70)

    query = """
        SELECT v.CODVEND, v.APELIDO, v.ATIVO, v.TIPVEND, v.EMAIL, v.CODGER
        FROM TGFVEN v ORDER BY v.CODVEND
    """
    result = client.executar_query(query)
    if result and result.get("rows"):
        df_vend = pd.DataFrame(result["rows"],
            columns=["CODVEND", "APELIDO", "ATIVO", "TIPVEND", "EMAIL", "CODGER"])
        print(f"    Total: {len(df_vend)} registros")

        arquivo = RAW_DATA_DIR / "vendedores" / "vendedores.parquet"
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        df_vend.to_parquet(arquivo, index=False)
        azure.upload_arquivo(arquivo, "raw/vendedores/vendedores.parquet")
        print(f"    [OK] Upload concluido")

    # ========================================
    # 2. CLIENTES (por faixas de CODPARC)
    # ========================================
    print(f"\n{'='*70}")
    print(">>> CLIENTES (por faixas)")
    print("=" * 70)

    query_clientes = """
        SELECT
            p.CODPARC, p.NOMEPARC, p.RAZAOSOCIAL, p.CGC_CPF,
            p.IDENTINSCESTAD, p.TIPPESSOA, p.CLIENTE, p.FORNECEDOR,
            p.VENDEDOR, p.TRANSPORTADORA, p.ATIVO, p.DTCAD, p.DTALTER,
            p.EMAIL, p.TELEFONE, p.CEP, p.NUMEND, p.COMPLEMENTO,
            p.CODCID, p.CODVEND, p.CODTAB, p.LIMCRED
        FROM TGFPAR p
        WHERE p.ATIVO = 'S' AND {WHERE_FAIXA}
        ORDER BY p.CODPARC
    """

    df_cli = extrair_por_faixas(
        client, query_clientes, "p.CODPARC",
        ["CODPARC", "NOMEPARC", "RAZAOSOCIAL", "CGC_CPF", "IDENTINSCESTAD",
         "TIPPESSOA", "CLIENTE", "FORNECEDOR", "VENDEDOR", "TRANSPORTADORA",
         "ATIVO", "DTCAD", "DTALTER", "EMAIL", "TELEFONE", "CEP", "NUMEND",
         "COMPLEMENTO", "CODCID", "CODVEND", "CODTAB", "LIMCRED"],
        "clientes", id_max=100000, faixa_size=20000
    )

    if not df_cli.empty:
        print(f"    TOTAL: {len(df_cli)} registros")
        arquivo = RAW_DATA_DIR / "clientes" / "clientes.parquet"
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        df_cli.to_parquet(arquivo, index=False)
        tamanho_mb = arquivo.stat().st_size / (1024*1024)
        print(f"    Tamanho: {tamanho_mb:.2f} MB")
        azure.upload_arquivo(arquivo, "raw/clientes/clientes.parquet")
        print(f"    [OK] Upload concluido")

    # ========================================
    # 3. PRODUTOS (por faixas de CODPROD)
    # ========================================
    print(f"\n{'='*70}")
    print(">>> PRODUTOS (por faixas)")
    print("=" * 70)

    query_produtos = """
        SELECT
            p.CODPROD, p.DESCRPROD, p.COMPLDESC, p.REFERENCIA, p.MARCA,
            p.CODGRUPOPROD, p.ATIVO, p.USOPROD, p.ORIGPROD, p.NCM,
            p.CODVOL, p.PESOBRUTO, p.PESOLIQ, p.DTALTER
        FROM TGFPRO p
        WHERE p.ATIVO = 'S' AND {WHERE_FAIXA}
        ORDER BY p.CODPROD
    """

    df_prod = extrair_por_faixas(
        client, query_produtos, "p.CODPROD",
        ["CODPROD", "DESCRPROD", "COMPLDESC", "REFERENCIA", "MARCA",
         "CODGRUPOPROD", "ATIVO", "USOPROD", "ORIGPROD", "NCM",
         "CODVOL", "PESOBRUTO", "PESOLIQ", "DTALTER"],
        "produtos", id_max=500000, faixa_size=50000
    )

    if not df_prod.empty:
        print(f"    TOTAL: {len(df_prod)} registros")
        arquivo = RAW_DATA_DIR / "produtos" / "produtos.parquet"
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        df_prod.to_parquet(arquivo, index=False)
        tamanho_mb = arquivo.stat().st_size / (1024*1024)
        print(f"    Tamanho: {tamanho_mb:.2f} MB")
        azure.upload_arquivo(arquivo, "raw/produtos/produtos.parquet")
        print(f"    [OK] Upload concluido")

    # ========================================
    # 4. ESTOQUE (por faixas de CODPROD)
    # ========================================
    print(f"\n{'='*70}")
    print(">>> ESTOQUE (por faixas)")
    print("=" * 70)

    query_estoque = """
        SELECT
            e.CODEMP, e.CODPROD, p.DESCRPROD, e.CODLOCAL, e.CONTROLE,
            NVL(e.ESTOQUE, 0) AS ESTOQUE,
            NVL(e.RESERVADO, 0) AS RESERVADO,
            NVL(e.ESTOQUE, 0) - NVL(e.RESERVADO, 0) AS DISPONIVEL
        FROM TGFEST e
        LEFT JOIN TGFPRO p ON p.CODPROD = e.CODPROD
        WHERE e.CODEMP = 1 AND NVL(e.ESTOQUE, 0) > 0 AND {WHERE_FAIXA}
        ORDER BY e.CODPROD
    """

    df_est = extrair_por_faixas(
        client, query_estoque, "e.CODPROD",
        ["CODEMP", "CODPROD", "DESCRPROD", "CODLOCAL", "CONTROLE",
         "ESTOQUE", "RESERVADO", "DISPONIVEL"],
        "estoque", id_max=500000, faixa_size=50000
    )

    if not df_est.empty:
        print(f"    TOTAL: {len(df_est)} registros")
        arquivo = RAW_DATA_DIR / "estoque" / "estoque.parquet"
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        df_est.to_parquet(arquivo, index=False)
        tamanho_mb = arquivo.stat().st_size / (1024*1024)
        print(f"    Tamanho: {tamanho_mb:.2f} MB")
        azure.upload_arquivo(arquivo, "raw/estoque/estoque.parquet")
        print(f"    [OK] Upload concluido")

    # ========================================
    # RESUMO FINAL
    # ========================================
    print("\n" + "=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)

    totais = [
        ("Vendedores", len(df_vend) if 'df_vend' in dir() else 0),
        ("Clientes", len(df_cli) if not df_cli.empty else 0),
        ("Produtos", len(df_prod) if not df_prod.empty else 0),
        ("Estoque", len(df_est) if not df_est.empty else 0),
    ]

    total_geral = 0
    for nome, qtd in totais:
        print(f"  {nome:<12}: {qtd:>10,} registros".replace(",", "."))
        total_geral += qtd

    print("-" * 70)
    print(f"  TOTAL GERAL: {total_geral:>10,} registros".replace(",", "."))
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
