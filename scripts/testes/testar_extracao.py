# -*- coding: utf-8 -*-
"""
Teste rapido de extracao - Data Hub
Extrai uma amostra pequena de cada tipo de dado para validar funcionamento.
"""

import sys
import os

# Adicionar src ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import logging
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    print("=" * 70)
    print("TESTE DE EXTRACAO - MMARRA DATA HUB")
    print("=" * 70)
    print(f"Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Limite: 10 registros por extrator")
    print("=" * 70)

    from src.extractors import (
        VendasExtractor,
        ClientesExtractor,
        ProdutosExtractor,
        EstoqueExtractor
    )

    # Data de teste: ultimos 7 dias
    data_fim = datetime.now().strftime("%Y-%m-%d")
    data_inicio = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    testes = [
        ("VENDAS", VendasExtractor(), {"data_inicio": data_inicio, "data_fim": data_fim}),
        ("CLIENTES", ClientesExtractor(), {"apenas_ativos": True}),
        ("PRODUTOS", ProdutosExtractor(), {"apenas_ativos": True}),
        ("ESTOQUE", EstoqueExtractor(), {"codemp": 1, "apenas_com_estoque": True}),
    ]

    resultados = []

    for nome, extrator, kwargs in testes:
        print(f"\n>>> Testando: {nome}")

        try:
            df = extrator.extrair(limite=10, **kwargs)

            if df is not None and not df.empty:
                print(f"    [OK] {len(df)} registros extraidos")
                print(f"    Colunas: {list(df.columns[:5])}...")

                # Salvar amostra em CSV para visualizacao
                arquivo = extrator.salvar_csv(df, "teste")
                print(f"    Arquivo: {arquivo}")

                resultados.append({"nome": nome, "status": "OK", "registros": len(df)})
            else:
                print(f"    [VAZIO] Nenhum registro")
                resultados.append({"nome": nome, "status": "VAZIO", "registros": 0})

        except Exception as e:
            print(f"    [ERRO] {e}")
            resultados.append({"nome": nome, "status": "ERRO", "erro": str(e)})

    # Resumo
    print("\n" + "=" * 70)
    print("RESUMO DO TESTE")
    print("=" * 70)

    ok_count = sum(1 for r in resultados if r["status"] == "OK")
    total = len(resultados)

    for r in resultados:
        status_icon = "OK" if r["status"] == "OK" else "X " if r["status"] == "ERRO" else "- "
        print(f"  [{status_icon}] {r['nome']}: {r.get('registros', r.get('erro', 'N/A'))}")

    print("=" * 70)
    print(f"Resultado: {ok_count}/{total} extratores funcionando")
    print("=" * 70)

    if ok_count == total:
        print("\n*** SUCESSO! Todos os extratores estao funcionando! ***")
        print("\nProximos comandos disponiveis:")
        print("  python -m src.main --extrator vendas --data-inicio 2026-01-01 --data-fim 2026-01-31")
        print("  python -m src.main --extrator clientes")
        print("  python -m src.main --extrator produtos --limite 1000")
        print("  python -m src.main --extrator estoque --empresa 1")
        print("  python -m src.main --todos --limite 100")

    return 0 if ok_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
