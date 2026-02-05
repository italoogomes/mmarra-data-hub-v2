# -*- coding: utf-8 -*-
"""
Teste de upload para o Data Lake
Extrai tabela pequena (vendedores/compradores) e envia para o Azure
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

from src.utils.sankhya_client import SankhyaClient
from src.utils.azure_storage import AzureDataLakeClient

def main():
    print("=" * 60)
    print("TESTE DE UPLOAD - SANKHYA -> DATA LAKE")
    print("=" * 60)

    # 1. Extrair dados do Sankhya (tabela de vendedores/compradores)
    print("\n[1] Extraindo vendedores/compradores do Sankhya...")

    sankhya = SankhyaClient()
    if not sankhya.autenticar():
        print("[ERRO] Falha na autenticacao Sankhya")
        return 1

    query = """
    SELECT
        v.CODVEND,
        v.APELIDO,
        v.ATIVO,
        v.TIPVEND,
        v.EMAIL,
        v.CODGER
    FROM TGFVEN v
    ORDER BY v.CODVEND
    """

    result = sankhya.executar_query(query)

    if not result or not result.get("rows"):
        print("[ERRO] Nenhum dado retornado")
        return 1

    rows = result["rows"]
    colunas = ["CODVEND", "APELIDO", "ATIVO", "TIPVEND", "EMAIL", "CODGER"]

    df = pd.DataFrame(rows, columns=colunas)
    print(f"    Extraidos {len(df)} registros")
    print(f"    Colunas: {list(df.columns)}")

    # 2. Salvar localmente como Parquet
    print("\n[2] Salvando arquivo Parquet local...")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arquivo_local = Path(f"src/data/raw/vendedores_{timestamp}.parquet")
    arquivo_local.parent.mkdir(parents=True, exist_ok=True)

    df.to_parquet(arquivo_local, index=False, engine='pyarrow')
    tamanho_kb = arquivo_local.stat().st_size / 1024
    print(f"    Arquivo: {arquivo_local}")
    print(f"    Tamanho: {tamanho_kb:.1f} KB")

    # 3. Upload para o Data Lake
    print("\n[3] Enviando para Azure Data Lake...")

    azure = AzureDataLakeClient()

    if not azure.testar_conexao():
        print("[ERRO] Falha na conexao com Azure")
        return 1

    # Caminho no Data Lake: raw/vendedores/arquivo.parquet
    caminho_destino = f"raw/vendedores/vendedores_{timestamp}.parquet"

    if azure.upload_arquivo(arquivo_local, caminho_destino):
        print(f"    [OK] Upload concluido!")
        print(f"    Destino: {caminho_destino}")
    else:
        print("    [ERRO] Falha no upload")
        return 1

    # 4. Verificar se chegou
    print("\n[4] Verificando arquivo no Data Lake...")

    itens = azure.listar_pastas("raw/vendedores")
    if itens:
        print("    Arquivos encontrados:")
        for item in itens:
            print(f"      - {item}")
    else:
        print("    (pasta vazia ou erro)")

    print("\n" + "=" * 60)
    print("TESTE CONCLUIDO COM SUCESSO!")
    print("=" * 60)
    print(f"\nResumo:")
    print(f"  - Registros extraidos: {len(df)}")
    print(f"  - Arquivo local: {arquivo_local}")
    print(f"  - Arquivo no Azure: datahub/{caminho_destino}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
