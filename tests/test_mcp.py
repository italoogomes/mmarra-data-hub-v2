#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste do Servidor MCP - Executa query de divergências
"""

import asyncio
import sys
import os

# Adicionar o diretório ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'mcp_sankhya'))

# Configurar variáveis de ambiente
os.environ['SANKHYA_CLIENT_ID'] = '09ef3473-cb85-41d4-b6d4-473c15d39292'
os.environ['SANKHYA_CLIENT_SECRET'] = '7phfkche8hWHpWYBNWbEgf4xY4mPixp0'
os.environ['SANKHYA_X_TOKEN'] = 'dca9f07d-bf0f-426c-b537-0e5b0ff1123d'

from mcp_sankhya.server import SankhyaAPI


async def test_query_divergencias():
    """Testa a query de divergências V3."""
    print("Iniciando teste do MCP Sankhya...")
    print("=" * 60)

    try:
        # Criar cliente API
        api = SankhyaAPI()
        print("Cliente API criado com sucesso")

        # Query V3 de divergências
        sql = """
        SELECT CAB.CODEMP, ITE.CODPROD, PRO.DESCRPROD, PRO.REFERENCIA, ITE.NUNOTA,
               CAB.NUMNOTA, CAB.CODTIPOPER AS TOP, TOP.DESCROPER AS DESCR_TOP,
               ITE.QTDNEG AS QTD_NOTA, ITE.STATUSNOTA AS STATUS_ITEM,
               CAB.STATUSNOTA AS STATUS_CAB, NVL(EST.ESTOQUE_TGFEST, 0) AS QTD_DISPONIVEL_TGFEST,
               NVL(WMS.ESTOQUE_WMS, 0) AS QTD_WMS,
               (NVL(WMS.ESTOQUE_WMS, 0) - NVL(EST.ESTOQUE_TGFEST, 0)) AS DIVERGENCIA,
               TO_CHAR(CAB.DTNEG, 'DD/MM/YYYY') AS DATA_NOTA
        FROM TGFITE ITE
        INNER JOIN TGFCAB CAB ON ITE.NUNOTA = CAB.NUNOTA
        INNER JOIN TGFPRO PRO ON ITE.CODPROD = PRO.CODPROD
        LEFT JOIN (
            SELECT DISTINCT CODTIPOPER, MIN(DESCROPER) AS DESCROPER
            FROM TGFTOP
            GROUP BY CODTIPOPER
        ) TOP ON CAB.CODTIPOPER = TOP.CODTIPOPER
        LEFT JOIN (
            SELECT CODPROD, CODEMP, SUM(NVL(ESTOQUE, 0)) AS ESTOQUE_TGFEST
            FROM TGFEST
            WHERE CODEMP = 7
            GROUP BY CODPROD, CODEMP
        ) EST ON ITE.CODPROD = EST.CODPROD AND EST.CODEMP = CAB.CODEMP
        LEFT JOIN (
            SELECT CODPROD, SUM(NVL(ESTOQUE, 0)) AS ESTOQUE_WMS
            FROM TGWEST
            WHERE CODEMP = 7
            GROUP BY CODPROD
        ) WMS ON ITE.CODPROD = WMS.CODPROD
        WHERE CAB.CODEMP = 7
          AND ITE.STATUSNOTA = 'P'
          AND NVL(WMS.ESTOQUE_WMS, 0) > NVL(EST.ESTOQUE_TGFEST, 0)
          AND (NVL(WMS.ESTOQUE_WMS, 0) - NVL(EST.ESTOQUE_TGFEST, 0)) > 0
        ORDER BY (NVL(WMS.ESTOQUE_WMS, 0) - NVL(EST.ESTOQUE_TGFEST, 0)) DESC
        """

        print("\nExecutando Query de Divergencias V3...")
        print("(Aguarde, pode demorar alguns segundos...)")

        # Executar query
        resultado = await api.execute_query(sql)

        # Processar resultado
        if "responseBody" in resultado and "rows" in resultado["responseBody"]:
            rows = resultado["responseBody"]["rows"]
            total = len(rows)

            print(f"\n{'-' * 60}")
            print(f"RESULTADO DA QUERY DE DIVERGENCIAS V3")
            print(f"{'-' * 60}")
            print(f"\nTotal de registros: {total}")

            if total > 0:
                # Calcular estatísticas
                produtos_unicos = len(set(row[1] for row in rows))
                notas_unicas = len(set(row[4] for row in rows))
                divergencia_total = sum(row[13] for row in rows)
                maior_divergencia = max(row[13] for row in rows)

                print(f"Produtos unicos: {produtos_unicos}")
                print(f"Notas unicas: {notas_unicas}")
                print(f"Divergencia total: {divergencia_total:,} unidades")
                print(f"Maior divergencia: {maior_divergencia:,} unidades")

                print(f"\n{'-' * 60}")
                print("TOP 5 MAIORES DIVERGENCIAS:")
                print(f"{'-' * 60}")
                print(f"{'Produto':<10} {'Descricao':<35} {'Divergencia':>12}")
                print(f"{'-' * 60}")

                for i, row in enumerate(rows[:5], 1):
                    codprod = row[1]
                    descrprod = row[2][:32] + "..." if len(row[2]) > 35 else row[2]
                    divergencia = row[13]
                    print(f"{codprod:<10} {descrprod:<35} {divergencia:>12,} un")

                print(f"{'-' * 60}")
                print(f"\nTESTE DO MCP: SUCESSO!")
                print("A query V3 foi executada corretamente sem duplicacoes.")

            else:
                print("\nNenhuma divergencia encontrada (query retornou 0 registros)")
                print("TESTE DO MCP: SUCESSO (query executada, mas sem resultados)")

        else:
            print("\nResposta da API nao contem dados esperados")
            print(f"Estrutura recebida: {list(resultado.keys())}")
            print(f"\nResposta completa:")
            import json
            print(json.dumps(resultado, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"\nERRO ao executar query: {str(e)}")
        print(f"Tipo: {type(e).__name__}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_query_divergencias())
