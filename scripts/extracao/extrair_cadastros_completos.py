# -*- coding: utf-8 -*-
"""
Extrai cadastros COMPLETOS do Sankhya com paginacao
- Clientes (~57k)
- Produtos (~393k)
- Estoque (~36k)
- Vendedores (~111)
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


def extrair_paginado(
    client: SankhyaClient,
    query_base: str,
    colunas: list,
    nome: str,
    lote_size: int = 10000
) -> pd.DataFrame:
    """
    Extrai dados com paginacao.

    Args:
        client: Cliente Sankhya autenticado
        query_base: Query SQL base (sem OFFSET/FETCH)
        colunas: Lista de nomes das colunas
        nome: Nome para log
        lote_size: Tamanho do lote

    Returns:
        DataFrame com todos os dados
    """
    all_rows = []
    offset = 0
    lote = 1

    while True:
        query = f"""
        {query_base}
        OFFSET {offset} ROWS
        FETCH NEXT {lote_size} ROWS ONLY
        """

        result = client.executar_query(query, timeout=180)

        if not result:
            logger.error(f"Erro na query (lote {lote})")
            break

        rows = result.get("rows", [])

        if not rows:
            break

        all_rows.extend(rows)
        print(f"    Lote {lote}: +{len(rows)} registros (total: {len(all_rows)})")

        if len(rows) < lote_size:
            break

        offset += lote_size
        lote += 1

    if not all_rows:
        return pd.DataFrame(columns=colunas)

    return pd.DataFrame(all_rows, columns=colunas)


def main():
    print("=" * 70)
    print("EXTRACAO COMPLETA DE CADASTROS - SANKHYA -> DATA LAKE")
    print("=" * 70)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Autenticar
    client = SankhyaClient()
    if not client.autenticar():
        print("[ERRO] Falha na autenticacao")
        return 1

    azure = AzureDataLakeClient()
    if not azure.testar_conexao():
        print("[ERRO] Falha na conexao Azure")
        return 1

    # Configuracao dos cadastros
    cadastros = [
        {
            "nome": "vendedores",
            "query": """
                SELECT v.CODVEND, v.APELIDO, v.ATIVO, v.TIPVEND, v.EMAIL, v.CODGER
                FROM TGFVEN v
                ORDER BY v.CODVEND
            """,
            "colunas": ["CODVEND", "APELIDO", "ATIVO", "TIPVEND", "EMAIL", "CODGER"],
            "caminho": "raw/vendedores/vendedores.parquet"
        },
        {
            "nome": "clientes",
            "query": """
                SELECT
                    p.CODPARC, p.NOMEPARC, p.RAZAOSOCIAL, p.CGC_CPF,
                    p.IDENTINSCESTAD, p.TIPPESSOA, p.CLIENTE, p.FORNECEDOR,
                    p.VENDEDOR, p.TRANSPORTADORA, p.ATIVO, p.DTCAD, p.DTALTER,
                    p.EMAIL, p.TELEFONE, p.FAX, p.CEP, p.CODEND, p.NUMEND,
                    p.COMPLEMENTO, p.CODBAI, b.NOMEBAI, p.CODCID, c.NOMECID,
                    c.UF, p.CODVEND, v.APELIDO AS APELIDO_VEND, p.CODTAB,
                    p.LIMCRED, p.CODREG
                FROM TGFPAR p
                LEFT JOIN TSIBAI b ON b.CODBAI = p.CODBAI
                LEFT JOIN TSICID c ON c.CODCID = p.CODCID
                LEFT JOIN TGFVEN v ON v.CODVEND = p.CODVEND
                WHERE p.ATIVO = 'S'
                ORDER BY p.CODPARC
            """,
            "colunas": [
                "CODPARC", "NOMEPARC", "RAZAOSOCIAL", "CGC_CPF", "IDENTINSCESTAD",
                "TIPPESSOA", "CLIENTE", "FORNECEDOR", "VENDEDOR", "TRANSPORTADORA",
                "ATIVO", "DTCAD", "DTALTER", "EMAIL", "TELEFONE", "FAX", "CEP",
                "CODEND", "NUMEND", "COMPLEMENTO", "CODBAI", "NOMEBAI", "CODCID",
                "NOMECID", "UF", "CODVEND", "APELIDO_VEND", "CODTAB", "LIMCRED", "CODREG"
            ],
            "caminho": "raw/clientes/clientes.parquet"
        },
        {
            "nome": "produtos",
            "query": """
                SELECT
                    p.CODPROD, p.DESCRPROD, p.COMPLDESC, p.REFERENCIA, p.MARCA,
                    p.CODGRUPOPROD, g.DESCRGRUPOPROD, p.ATIVO, p.USOPROD,
                    p.ORIGPROD, p.NCM, p.CODVOL, p.PESOBRUTO, p.PESOLIQ,
                    p.LARGURA, p.ALTURA, p.ESPESSURA, p.DTALTER
                FROM TGFPRO p
                LEFT JOIN TGFGRU g ON g.CODGRUPOPROD = p.CODGRUPOPROD
                WHERE p.ATIVO = 'S'
                ORDER BY p.CODPROD
            """,
            "colunas": [
                "CODPROD", "DESCRPROD", "COMPLDESC", "REFERENCIA", "MARCA",
                "CODGRUPOPROD", "DESCRGRUPOPROD", "ATIVO", "USOPROD", "ORIGPROD",
                "NCM", "CODVOL", "PESOBRUTO", "PESOLIQ", "LARGURA", "ALTURA",
                "ESPESSURA", "DTALTER"
            ],
            "caminho": "raw/produtos/produtos.parquet"
        },
        {
            "nome": "estoque",
            "query": """
                SELECT
                    e.CODEMP, e.CODPROD, p.DESCRPROD, e.CODLOCAL,
                    l.DESCRLOCAL AS CODLOCAL_DESCR, e.CONTROLE,
                    NVL(e.ESTOQUE, 0) AS ESTOQUE,
                    NVL(e.RESERVADO, 0) AS RESERVADO,
                    NVL(e.ESTOQUE, 0) - NVL(e.RESERVADO, 0) AS DISPONIVEL
                FROM TGFEST e
                LEFT JOIN TGFPRO p ON p.CODPROD = e.CODPROD
                LEFT JOIN TGFLOC l ON l.CODLOCAL = e.CODLOCAL
                WHERE e.CODEMP = 1 AND NVL(e.ESTOQUE, 0) > 0
                ORDER BY e.CODPROD, e.CODLOCAL
            """,
            "colunas": [
                "CODEMP", "CODPROD", "DESCRPROD", "CODLOCAL", "CODLOCAL_DESCR",
                "CONTROLE", "ESTOQUE", "RESERVADO", "DISPONIVEL"
            ],
            "caminho": "raw/estoque/estoque.parquet"
        }
    ]

    resultados = []

    for config in cadastros:
        nome = config["nome"]
        print(f"\n{'='*70}")
        print(f">>> {nome.upper()}")
        print("=" * 70)

        # Extrair com paginacao
        print("  [1] Extraindo do Sankhya (paginado)...")
        df = extrair_paginado(
            client,
            config["query"],
            config["colunas"],
            nome,
            lote_size=10000
        )

        if df.empty:
            print(f"  [X] Nenhum dado extraido")
            resultados.append({"nome": nome, "sucesso": False, "registros": 0})
            continue

        print(f"      TOTAL: {len(df)} registros")

        # Salvar localmente
        print("  [2] Salvando Parquet local...")
        output_dir = RAW_DATA_DIR / nome
        output_dir.mkdir(parents=True, exist_ok=True)
        arquivo_local = output_dir / f"{nome}.parquet"

        df.to_parquet(arquivo_local, index=False, engine='pyarrow')
        tamanho_mb = arquivo_local.stat().st_size / (1024 * 1024)
        print(f"      {tamanho_mb:.2f} MB")

        # Upload para Data Lake
        print("  [3] Enviando para Data Lake...")
        if azure.upload_arquivo(arquivo_local, config["caminho"], sobrescrever=True):
            print(f"      [OK] {config['caminho']}")
            resultados.append({"nome": nome, "sucesso": True, "registros": len(df), "tamanho_mb": tamanho_mb})
        else:
            print(f"      [X] Falha no upload")
            resultados.append({"nome": nome, "sucesso": False, "registros": len(df)})

    # Resumo final
    print("\n" + "=" * 70)
    print("RESUMO FINAL")
    print("=" * 70)

    total_registros = 0
    total_mb = 0

    for r in resultados:
        status = "[OK]" if r["sucesso"] else "[X] "
        registros = f"{r['registros']:,}".replace(",", ".")
        tamanho = f"{r.get('tamanho_mb', 0):.2f} MB" if r.get('tamanho_mb') else "-"
        print(f"  {status} {r['nome']:<12} {registros:>10} registros  {tamanho:>10}")

        if r["sucesso"]:
            total_registros += r["registros"]
            total_mb += r.get("tamanho_mb", 0)

    print("-" * 70)
    print(f"  TOTAL: {total_registros:,} registros | {total_mb:.2f} MB".replace(",", "."))
    print("=" * 70)

    ok = sum(1 for r in resultados if r["sucesso"])
    return 0 if ok == len(resultados) else 1


if __name__ == "__main__":
    sys.exit(main())
