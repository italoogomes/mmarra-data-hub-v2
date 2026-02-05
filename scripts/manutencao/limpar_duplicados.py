# -*- coding: utf-8 -*-
"""
Limpa arquivos duplicados/antigos do Data Lake
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.azure_storage import AzureDataLakeClient

def main():
    print("Limpando arquivos duplicados...")

    azure = AzureDataLakeClient()

    # Arquivos para deletar
    arquivos_deletar = [
        "raw/vendedores/vendedores_20260203_104218.parquet",
        "raw/vendedores/vendedores_20260203_104243.parquet"
    ]

    for arquivo in arquivos_deletar:
        if azure.deletar_arquivo(arquivo):
            print(f"  [OK] Deletado: {arquivo}")
        else:
            print(f"  [X]  Erro: {arquivo}")

    print("\nConcluido!")

if __name__ == "__main__":
    main()
