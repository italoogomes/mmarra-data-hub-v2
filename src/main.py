# -*- coding: utf-8 -*-
"""
MMarra Data Hub - Script Principal de Extracao

Uso:
    python -m src.main --extrator vendas --limite 100
    python -m src.main --extrator clientes --formato csv
    python -m src.main --extrator produtos
    python -m src.main --extrator estoque --empresa 1
    python -m src.main --todos --limite 50
"""

import logging
import argparse
from datetime import datetime

from src.extractors import (
    VendasExtractor,
    ClientesExtractor,
    ProdutosExtractor,
    EstoqueExtractor
)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="MMarra Data Hub - Extracao de dados do Sankhya"
    )

    parser.add_argument(
        "--extrator",
        choices=["vendas", "clientes", "produtos", "estoque"],
        help="Qual extrator executar"
    )
    parser.add_argument(
        "--todos",
        action="store_true",
        help="Executar todos os extratores"
    )
    parser.add_argument(
        "--data-inicio",
        help="Data inicial (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--data-fim",
        help="Data final (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--limite",
        type=int,
        help="Limite de registros (para testes)"
    )
    parser.add_argument(
        "--formato",
        default="parquet",
        choices=["parquet", "csv"],
        help="Formato de saida"
    )
    parser.add_argument(
        "--empresa",
        type=int,
        default=1,
        help="Codigo da empresa (para estoque)"
    )

    args = parser.parse_args()

    if not args.extrator and not args.todos:
        parser.print_help()
        return

    # Extratores disponiveis
    extratores = {
        "vendas": VendasExtractor,
        "clientes": ClientesExtractor,
        "produtos": ProdutosExtractor,
        "estoque": EstoqueExtractor
    }

    # Determinar quais executar
    if args.todos:
        lista_extratores = list(extratores.keys())
    else:
        lista_extratores = [args.extrator]

    print("=" * 70)
    print("MMARRA DATA HUB - EXTRACAO DE DADOS")
    print("=" * 70)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Extratores: {', '.join(lista_extratores)}")
    print(f"Formato: {args.formato}")
    if args.limite:
        print(f"Limite: {args.limite} registros")
    print("=" * 70)

    resultados = []

    for nome in lista_extratores:
        print(f"\n>>> Iniciando: {nome.upper()}")

        extrator_class = extratores[nome]
        extrator = extrator_class()

        kwargs = {
            "formato": args.formato,
            "limite": args.limite
        }

        # Argumentos especificos
        if args.data_inicio:
            kwargs["data_inicio"] = args.data_inicio
        if args.data_fim:
            kwargs["data_fim"] = args.data_fim
        if nome == "estoque":
            kwargs["codemp"] = args.empresa

        try:
            arquivo = extrator.executar(**kwargs)

            if arquivo:
                resultados.append({
                    "extrator": nome,
                    "status": "OK",
                    "arquivo": str(arquivo)
                })
                print(f"    [OK] Arquivo: {arquivo}")
            else:
                resultados.append({
                    "extrator": nome,
                    "status": "VAZIO",
                    "arquivo": None
                })
                print(f"    [VAZIO] Nenhum dado extraido")

        except Exception as e:
            resultados.append({
                "extrator": nome,
                "status": "ERRO",
                "arquivo": None,
                "erro": str(e)
            })
            print(f"    [ERRO] {e}")
            logger.exception(f"Erro no extrator {nome}")

    # Resumo final
    print("\n" + "=" * 70)
    print("RESUMO DA EXTRACAO")
    print("=" * 70)

    for r in resultados:
        status = r["status"]
        if status == "OK":
            print(f"  [OK]    {r['extrator']}: {r['arquivo']}")
        elif status == "VAZIO":
            print(f"  [VAZIO] {r['extrator']}: Sem dados")
        else:
            print(f"  [ERRO]  {r['extrator']}: {r.get('erro', 'Erro desconhecido')}")

    print("=" * 70)


if __name__ == "__main__":
    main()
