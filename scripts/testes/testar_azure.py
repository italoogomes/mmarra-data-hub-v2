# -*- coding: utf-8 -*-
"""
Teste de conexao com Azure Data Lake
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from src.utils.azure_storage import AzureDataLakeClient, criar_estrutura_datalake

def main():
    print("=" * 60)
    print("TESTE DE CONEXAO - AZURE DATA LAKE")
    print("=" * 60)

    client = AzureDataLakeClient()

    print(f"\nStorage Account: {client.account_name}")
    print(f"Container: {client.container_name}")

    print("\nTestando conexao...")

    if client.testar_conexao():
        print("\n[OK] Conexao estabelecida com sucesso!")

        # Listar conteúdo atual
        print("\nConteudo atual do container:")
        itens = client.listar_pastas("/")
        if itens:
            for item in itens[:20]:
                print(f"  - {item}")
            if len(itens) > 20:
                print(f"  ... e mais {len(itens) - 20} itens")
        else:
            print("  (vazio)")

        # Criar estrutura automaticamente
        print("\n" + "=" * 60)
        print("Criando estrutura de pastas...")
        criar_estrutura_datalake()

        return 0

    else:
        print("\n[ERRO] Falha na conexao!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
