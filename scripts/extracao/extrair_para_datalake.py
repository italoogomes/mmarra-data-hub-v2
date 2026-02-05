# -*- coding: utf-8 -*-
"""
Extrai dados do Sankhya e envia para o Azure Data Lake
Sobrescreve arquivos existentes (sem timestamp)
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Adicionar diretório raiz do projeto ao path
ROOT_DIR = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))

import logging
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from src.extractors import (
    VendasExtractor,
    ClientesExtractor,
    ProdutosExtractor,
    EstoqueExtractor,
    VendedoresExtractor
)
from src.utils.azure_storage import AzureDataLakeClient


def extrair_e_enviar(
    extrator,
    caminho_datalake: str,
    **kwargs
) -> bool:
    """
    Extrai dados e envia para o Data Lake.

    Args:
        extrator: Instancia do extrator
        caminho_datalake: Caminho no Data Lake (ex: 'raw/vendedores/vendedores.parquet')
        **kwargs: Argumentos para o extrator

    Returns:
        True se sucesso
    """
    nome = extrator.nome

    print(f"\n>>> {nome.upper()}")
    print("-" * 40)

    # 1. Extrair
    print(f"  [1] Extraindo do Sankhya...")
    df = extrator.extrair(**kwargs)

    if df is None or df.empty:
        print(f"  [X] Nenhum dado extraido")
        return False

    print(f"      {len(df)} registros")

    # 2. Salvar localmente
    print(f"  [2] Salvando Parquet local...")
    arquivo_local = extrator.salvar_parquet(df, sufixo="")
    tamanho_kb = arquivo_local.stat().st_size / 1024
    print(f"      {tamanho_kb:.1f} KB")

    # 3. Enviar para Data Lake
    print(f"  [3] Enviando para Data Lake...")
    azure = AzureDataLakeClient()

    if azure.upload_arquivo(arquivo_local, caminho_datalake, sobrescrever=True):
        print(f"      [OK] {caminho_datalake}")
        return True
    else:
        print(f"      [X] Falha no upload")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Extrai dados do Sankhya e envia para Azure Data Lake"
    )
    parser.add_argument(
        "--extrator",
        choices=["vendedores", "clientes", "produtos", "estoque", "vendas", "todos"],
        default="todos",
        help="Qual extrator executar"
    )
    parser.add_argument("--limite", type=int, help="Limite de registros (para teste)")

    args = parser.parse_args()

    print("=" * 60)
    print("EXTRACAO SANKHYA -> AZURE DATA LAKE")
    print("=" * 60)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Extrator: {args.extrator}")
    if args.limite:
        print(f"Limite: {args.limite} registros")

    # Configuracao dos extratores
    extratores = {
        "vendedores": {
            "extrator": VendedoresExtractor(),
            "caminho": "raw/vendedores/vendedores.parquet",
            "kwargs": {}
        },
        "clientes": {
            "extrator": ClientesExtractor(),
            "caminho": "raw/clientes/clientes.parquet",
            "kwargs": {"apenas_ativos": True}
        },
        "produtos": {
            "extrator": ProdutosExtractor(),
            "caminho": "raw/produtos/produtos.parquet",
            "kwargs": {"apenas_ativos": True}
        },
        "estoque": {
            "extrator": EstoqueExtractor(),
            "caminho": "raw/estoque/estoque.parquet",
            "kwargs": {"codemp": 1, "apenas_com_estoque": True}
        },
        "vendas": {
            "extrator": VendasExtractor(),
            "caminho": "raw/vendas/vendas.parquet",
            "kwargs": {}
        }
    }

    # Determinar quais executar
    if args.extrator == "todos":
        lista = list(extratores.keys())
    else:
        lista = [args.extrator]

    resultados = []

    for nome in lista:
        config = extratores[nome]
        kwargs = config["kwargs"].copy()

        if args.limite:
            kwargs["limite"] = args.limite

        sucesso = extrair_e_enviar(
            config["extrator"],
            config["caminho"],
            **kwargs
        )

        resultados.append({
            "extrator": nome,
            "sucesso": sucesso
        })

    # Resumo
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)

    ok = sum(1 for r in resultados if r["sucesso"])
    total = len(resultados)

    for r in resultados:
        status = "[OK]" if r["sucesso"] else "[X] "
        print(f"  {status} {r['extrator']}")

    print(f"\n{ok}/{total} extracoes concluidas")
    print("=" * 60)

    return 0 if ok == total else 1


if __name__ == "__main__":
    sys.exit(main())
