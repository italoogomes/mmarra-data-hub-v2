# -*- coding: utf-8 -*-
"""
Extrai TODOS os cadastros do Sankhya
Usa faixas de 5000 para contornar limite da API
"""

import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
import pandas as pd

logging.basicConfig(level=logging.WARNING)

from src.utils.sankhya_client import SankhyaClient
from src.utils.azure_storage import AzureDataLakeClient
from src.config import RAW_DATA_DIR


def extrair_completo(
    client: SankhyaClient,
    query_template: str,
    campo_id: str,
    colunas: list,
    nome: str,
    id_max: int = 600000,
    faixa_size: int = 5000
) -> pd.DataFrame:
    """Extrai todos os dados usando faixas pequenas de 5000"""
    all_dfs = []
    id_inicio = 0
    total = 0

    print(f"  Extraindo em faixas de {faixa_size}...")

    while id_inicio <= id_max:
        id_fim = id_inicio + faixa_size
        where_faixa = f"{campo_id} >= {id_inicio} AND {campo_id} < {id_fim}"
        query = query_template.replace("{WHERE_FAIXA}", where_faixa)

        result = client.executar_query(query, timeout=180)

        if result and result.get("rows"):
            rows = result["rows"]
            df_faixa = pd.DataFrame(rows, columns=colunas)
            all_dfs.append(df_faixa)
            total += len(rows)
            print(f"    {id_inicio:>6}-{id_fim:<6}: +{len(rows):>5} (total: {total:>6})")

        id_inicio = id_fim

        # Se 3 faixas consecutivas vazias, parar
        if id_inicio > id_max:
            break

    if not all_dfs:
        return pd.DataFrame(columns=colunas)

    return pd.concat(all_dfs, ignore_index=True)


def main():
    print("=" * 70)
    print("EXTRACAO COMPLETA - TODOS OS CADASTROS")
    print("=" * 70)
    print(f"Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    client = SankhyaClient()
    if not client.autenticar():
        print("[ERRO] Falha na autenticacao")
        return 1

    azure = AzureDataLakeClient()

    resultados = []

    # ========================================
    # 1. VENDEDORES
    # ========================================
    print(f"\n>>> VENDEDORES")
    query = "SELECT v.CODVEND, v.APELIDO, v.ATIVO, v.TIPVEND, v.EMAIL, v.CODGER FROM TGFVEN v ORDER BY v.CODVEND"
    result = client.executar_query(query)
    if result and result.get("rows"):
        df = pd.DataFrame(result["rows"], columns=["CODVEND", "APELIDO", "ATIVO", "TIPVEND", "EMAIL", "CODGER"])
        print(f"  Total: {len(df)} registros")
        arquivo = RAW_DATA_DIR / "vendedores" / "vendedores.parquet"
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(arquivo, index=False)
        azure.upload_arquivo(arquivo, "raw/vendedores/vendedores.parquet")
        resultados.append(("Vendedores", len(df), arquivo.stat().st_size / (1024*1024)))

    # ========================================
    # 2. CLIENTES (faixas de 5000)
    # ========================================
    print(f"\n>>> CLIENTES")
    query_cli = """
        SELECT p.CODPARC, p.NOMEPARC, p.RAZAOSOCIAL, p.CGC_CPF, p.TIPPESSOA,
               p.CLIENTE, p.FORNECEDOR, p.ATIVO, p.EMAIL, p.TELEFONE, p.CEP,
               p.CODCID, p.CODVEND, p.LIMCRED
        FROM TGFPAR p
        WHERE p.ATIVO = 'S' AND {WHERE_FAIXA}
        ORDER BY p.CODPARC
    """
    df_cli = extrair_completo(client, query_cli, "p.CODPARC",
        ["CODPARC", "NOMEPARC", "RAZAOSOCIAL", "CGC_CPF", "TIPPESSOA",
         "CLIENTE", "FORNECEDOR", "ATIVO", "EMAIL", "TELEFONE", "CEP",
         "CODCID", "CODVEND", "LIMCRED"],
        "clientes", id_max=100000, faixa_size=5000)

    if not df_cli.empty:
        print(f"  TOTAL: {len(df_cli)} registros")
        arquivo = RAW_DATA_DIR / "clientes" / "clientes.parquet"
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        df_cli.to_parquet(arquivo, index=False)
        mb = arquivo.stat().st_size / (1024*1024)
        print(f"  Tamanho: {mb:.2f} MB")
        azure.upload_arquivo(arquivo, "raw/clientes/clientes.parquet")
        resultados.append(("Clientes", len(df_cli), mb))

    # ========================================
    # 3. PRODUTOS (faixas de 5000)
    # ========================================
    print(f"\n>>> PRODUTOS")
    query_prod = """
        SELECT p.CODPROD, p.DESCRPROD, p.REFERENCIA, p.MARCA, p.CODGRUPOPROD,
               p.ATIVO, p.USOPROD, p.NCM, p.CODVOL, p.PESOBRUTO, p.PESOLIQ
        FROM TGFPRO p
        WHERE p.ATIVO = 'S' AND {WHERE_FAIXA}
        ORDER BY p.CODPROD
    """
    df_prod = extrair_completo(client, query_prod, "p.CODPROD",
        ["CODPROD", "DESCRPROD", "REFERENCIA", "MARCA", "CODGRUPOPROD",
         "ATIVO", "USOPROD", "NCM", "CODVOL", "PESOBRUTO", "PESOLIQ"],
        "produtos", id_max=600000, faixa_size=5000)

    if not df_prod.empty:
        print(f"  TOTAL: {len(df_prod)} registros")
        arquivo = RAW_DATA_DIR / "produtos" / "produtos.parquet"
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        df_prod.to_parquet(arquivo, index=False)
        mb = arquivo.stat().st_size / (1024*1024)
        print(f"  Tamanho: {mb:.2f} MB")
        azure.upload_arquivo(arquivo, "raw/produtos/produtos.parquet")
        resultados.append(("Produtos", len(df_prod), mb))

    # ========================================
    # 4. ESTOQUE (faixas de 5000)
    # ========================================
    print(f"\n>>> ESTOQUE")
    query_est = """
        SELECT e.CODEMP, e.CODPROD, p.DESCRPROD, e.CODLOCAL, e.CONTROLE,
               NVL(e.ESTOQUE, 0) AS ESTOQUE, NVL(e.RESERVADO, 0) AS RESERVADO,
               NVL(e.ESTOQUE, 0) - NVL(e.RESERVADO, 0) AS DISPONIVEL
        FROM TGFEST e
        LEFT JOIN TGFPRO p ON p.CODPROD = e.CODPROD
        WHERE e.CODEMP = 1 AND NVL(e.ESTOQUE, 0) > 0 AND {WHERE_FAIXA}
        ORDER BY e.CODPROD
    """
    df_est = extrair_completo(client, query_est, "e.CODPROD",
        ["CODEMP", "CODPROD", "DESCRPROD", "CODLOCAL", "CONTROLE",
         "ESTOQUE", "RESERVADO", "DISPONIVEL"],
        "estoque", id_max=600000, faixa_size=5000)

    if not df_est.empty:
        print(f"  TOTAL: {len(df_est)} registros")
        arquivo = RAW_DATA_DIR / "estoque" / "estoque.parquet"
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        df_est.to_parquet(arquivo, index=False)
        mb = arquivo.stat().st_size / (1024*1024)
        print(f"  Tamanho: {mb:.2f} MB")
        azure.upload_arquivo(arquivo, "raw/estoque/estoque.parquet")
        resultados.append(("Estoque", len(df_est), mb))

    # ========================================
    # RESUMO
    # ========================================
    print("\n" + "=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)

    total_reg = 0
    total_mb = 0
    for nome, qtd, mb in resultados:
        print(f"  {nome:<12}: {qtd:>10,} registros | {mb:>6.2f} MB".replace(",", "."))
        total_reg += qtd
        total_mb += mb

    print("-" * 70)
    print(f"  TOTAL       : {total_reg:>10,} registros | {total_mb:>6.2f} MB".replace(",", "."))
    print("=" * 70)
    print(f"Fim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
