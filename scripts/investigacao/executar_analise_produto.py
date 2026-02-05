"""
Executa query de analise detalhada de um produto especifico
"""

import os
import json
import requests
from dotenv import load_dotenv

# Carregar credenciais
env_path = os.path.join(os.path.dirname(__file__), 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

print("=" * 80)
print("ANALISE DETALHADA DE PRODUTO")
print("=" * 80)

# Parametros
CODEMP = 7
CODPROD = 137216

print(f"\nEmpresa: {CODEMP}")
print(f"Produto: {CODPROD}")

# 1. AUTENTICACAO
print("\n[1] Autenticando...")
auth_response = requests.post(
    "https://api.sankhya.com.br/authenticate",
    headers={
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Token": X_TOKEN
    },
    data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials"
    },
    timeout=30
)

if auth_response.status_code != 200:
    print(f"[ERRO] Autenticacao falhou: {auth_response.text}")
    exit(1)

access_token = auth_response.json()["access_token"]
print("[OK] Token obtido!")

# 2. EXECUTAR QUERY
print("\n[2] Executando analise detalhada...")

query_sql = f"""
WITH
Parametros AS (
    SELECT
        {CODEMP}      AS CODEMP,
        {CODPROD}  AS CODPROD
    FROM DUAL
),
Empresa AS (
    SELECT
        EMP.CODEMP,
        NVL(EMP.WMSLOCALAJEST, (SELECT INTEIRO FROM TSIPAR WHERE CHAVE = 'WMSLOCALAJEST')) AS CODLOCAL_AJUSTE
    FROM TGFEMP EMP
    JOIN Parametros
      ON Parametros.CODEMP = EMP.CODEMP
),
SaldoWmsTela AS (
    SELECT
        SUM(NVL(ESTW.ESTOQUEVOLPAD - ESTW.SAIDPENDVOLPAD, 0)) AS SALDO_WMS_TELA
    FROM TGWEST ESTW
    JOIN TGWEND WEND
      ON WEND.CODEND = ESTW.CODEND
    JOIN TGFEMP EMP
      ON EMP.CODEMP = WEND.CODEMP
    JOIN Parametros
      ON Parametros.CODEMP  = EMP.CODEMP
     AND Parametros.CODPROD = ESTW.CODPROD
    JOIN Empresa
      ON Empresa.CODEMP = EMP.CODEMP
    WHERE EMP.UTILIZAWMS = 'S'
      AND WEND.BLOQUEADO = 'N'
      AND WEND.EXCLCONF = 'N'
      AND NOT EXISTS (
            SELECT 1
            FROM TGWDCA DCA
            WHERE DCA.TIPDOCA = 'S'
              AND DCA.CODEND  = WEND.CODEND
      )
      AND ESTW.CONTROLE <> '#EXPLOTESEP'
      AND NVL(EMP.WMSLOCALAJEST, (SELECT INTEIRO FROM TSIPAR WHERE CHAVE = 'WMSLOCALAJEST')) = Empresa.CODLOCAL_AJUSTE
),
CabecalhosPV AS (
    SELECT
        CAB.NUNOTA
    FROM TGFCAB CAB
    JOIN Parametros
      ON Parametros.CODEMP = CAB.CODEMP
    WHERE CAB.CODTIPOPER IN (1007, 1017, 1018, 1019, 1020, 1023, 1024, 1025)
      AND CAB.PENDENTE   = 'S'
      AND CAB.STATUSNOTA = 'L'
),
PedidosPendentes AS (
    SELECT
        NVL(SUM(NVL(ITE.QTDNEG, 0)), 0) AS QTD_PEDIDO_PENDENTE
    FROM TGFITE ITE
    JOIN CabecalhosPV CAB
      ON CAB.NUNOTA = ITE.NUNOTA
    JOIN Parametros
      ON Parametros.CODPROD = ITE.CODPROD
),
EstoqueComercial AS (
    SELECT
        SUM(NVL(EST.ESTOQUE, 0)) AS ESTOQUE,
        SUM(NVL(EST.RESERVADO, 0)) AS RESERVADO,
        SUM(NVL(EST.WMSBLOQUEADO, 0)) AS WMSBLOQUEADO
    FROM TGFEST EST
    JOIN Parametros
      ON Parametros.CODEMP  = EST.CODEMP
     AND Parametros.CODPROD = EST.CODPROD
    JOIN Empresa
      ON Empresa.CODEMP = EST.CODEMP
    WHERE EST.CODLOCAL = Empresa.CODLOCAL_AJUSTE
),
Calc AS (
    SELECT
        ESTOQUE,
        RESERVADO,
        WMSBLOQUEADO,

        (ESTOQUE - RESERVADO - WMSBLOQUEADO) AS DISPONIVEL_COMERCIAL,

        NVL(SaldoWmsTela.SALDO_WMS_TELA, 0) AS SALDO_WMS_TELA,
        NVL(PedidosPendentes.QTD_PEDIDO_PENDENTE, 0) AS QTD_PEDIDO_PENDENTE,

        GREATEST(
            NVL(SaldoWmsTela.SALDO_WMS_TELA, 0) - NVL(PedidosPendentes.QTD_PEDIDO_PENDENTE, 0),
            0
        ) AS WMS_APOS_PEDIDOS
    FROM EstoqueComercial
    CROSS JOIN SaldoWmsTela
    CROSS JOIN PedidosPendentes
)
SELECT
    ESTOQUE,
    RESERVADO,
    WMSBLOQUEADO,
    DISPONIVEL_COMERCIAL,
    SALDO_WMS_TELA,
    QTD_PEDIDO_PENDENTE,
    WMS_APOS_PEDIDOS,
    CASE
        WHEN DISPONIVEL_COMERCIAL <= 0 THEN 0
        ELSE LEAST(DISPONIVEL_COMERCIAL, WMS_APOS_PEDIDOS)
    END AS DISPONIVEL_REAL_FINAL
FROM Calc
"""

query_payload = {
    "requestBody": {
        "sql": query_sql
    }
}

query_response = requests.post(
    "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    json=query_payload,
    timeout=120
)

if query_response.status_code != 200:
    print(f"[ERRO] Query falhou: {query_response.text}")
    exit(1)

result = query_response.json()

if result.get("status") != "1":
    print(f"[ERRO] Query retornou erro:")
    print(f"Status: {result.get('status')}")
    print(f"Mensagem: {result.get('statusMessage')}")
    exit(1)

print("[OK] Query executada com sucesso!")

# 3. PROCESSAR RESULTADO
print("\n" + "=" * 80)
print("RESULTADO DA ANALISE")
print("=" * 80)

response_body = result.get("responseBody", {})
fields = response_body.get("fieldsMetadata", [])
rows = response_body.get("rows", [])

if len(rows) == 0:
    print("\n[INFO] Nenhum dado encontrado para este produto!")
else:
    row = rows[0]

    print(f"\nEmpresa: {CODEMP}")
    print(f"Produto: {CODPROD}")
    print("")
    print("-" * 80)

    field_names = [f["name"] for f in fields]

    for i, field_name in enumerate(field_names):
        value = row[i] if i < len(row) else 0
        print(f"{field_name:30} : {value:>15,}".replace(',', '.'))

    print("-" * 80)

    # Calculos adicionais
    estoque = row[0] if len(row) > 0 else 0
    reservado = row[1] if len(row) > 1 else 0
    wmsbloqueado = row[2] if len(row) > 2 else 0
    disponivel_comercial = row[3] if len(row) > 3 else 0
    saldo_wms = row[4] if len(row) > 4 else 0
    pedidos_pendentes = row[5] if len(row) > 5 else 0
    disponivel_final = row[7] if len(row) > 7 else 0

    print("\n[ANALISE]")
    print("")

    # Divergencia ERP vs WMS
    divergencia = estoque - saldo_wms
    if divergencia != 0:
        print(f"  Divergencia ERP vs WMS: {divergencia:+,.0f} unidades".replace(',', '.'))
        if divergencia > 0:
            print(f"    -> ERP tem {abs(divergencia):.0f} un a MAIS que WMS")
        else:
            print(f"    -> WMS tem {abs(divergencia):.0f} un a MAIS que ERP")
    else:
        print("  Divergencia ERP vs WMS: Nenhuma (sincronizados)")

    print("")

    # Bloqueios
    total_bloqueios = reservado + wmsbloqueado
    if total_bloqueios > 0:
        print(f"  Total Bloqueado: {total_bloqueios:,.0f} un ({total_bloqueios/estoque*100:.1f}% do estoque)".replace(',', '.'))
        print(f"    - Reservado: {reservado:,.0f} un".replace(',', '.'))
        print(f"    - WMS Bloqueado: {wmsbloqueado:,.0f} un".replace(',', '.'))

    print("")

    # Disponibilidade
    if disponivel_final > 0:
        print(f"  Status: DISPONIVEL PARA VENDA ({disponivel_final:,.0f} un)".replace(',', '.'))
    elif disponivel_comercial <= 0:
        print(f"  Status: BLOQUEADO TOTAL (disponivel comercial: {disponivel_comercial:,.0f})".replace(',', '.'))
    elif saldo_wms <= 0:
        print(f"  Status: SEM ESTOQUE FISICO WMS")
    else:
        print(f"  Status: BLOQUEADO POR PEDIDOS PENDENTES")

print("\n" + "=" * 80)
print("FIM DA ANALISE")
print("=" * 80)
