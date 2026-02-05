# -*- coding: utf-8 -*-
"""
Transferir empenhos do pedido cancelado 1183490 para o pedido novo 1192177
Usando o mesmo padrao de UPDATE que funciona nos outros scripts
"""

import os
import requests
from dotenv import load_dotenv

# Caminho do .env na raiz do projeto
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
env_path = os.path.join(project_root, 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

BASE_URL = "https://api.sankhya.com.br"

PEDIDO_CANCELADO = 1183490
PEDIDO_NOVO = 1192177


def autenticar():
    """Autentica e retorna o access_token"""
    auth_response = requests.post(
        f"{BASE_URL}/authenticate",
        headers={"Content-Type": "application/x-www-form-urlencoded", "X-Token": X_TOKEN},
        data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"},
        timeout=30
    )
    if auth_response.status_code != 200:
        print(f"[ERRO] Autenticacao falhou: {auth_response.status_code}")
        return None
    return auth_response.json()["access_token"]


def executar_query(access_token, query_sql):
    """Executa uma query SELECT"""
    query_payload = {"requestBody": {"sql": query_sql}}
    try:
        query_response = requests.post(
            f"{BASE_URL}/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=query_payload,
            timeout=60
        )
        if query_response.status_code != 200:
            return None
        result = query_response.json()
        if result.get("status") != "1":
            print(f"[ERRO] {result.get('statusMessage')}")
            return None
        return result.get("responseBody", {})
    except Exception as e:
        print(f"[ERRO] {e}")
        return None


def save_record(access_token, entity, fields):
    """
    Executa saveRecord no MESMO PADRAO dos scripts que funcionam.
    """
    local_fields = {}
    for key, value in fields.items():
        if value is None:
            local_fields[key] = {}
        else:
            local_fields[key] = {"$": str(value)}

    payload = {
        "requestBody": {
            "dataSet": {
                "rootEntity": entity,
                "includePresentationFields": "N",
                "dataRow": {
                    "localFields": local_fields
                }
            }
        }
    }

    url = f"{BASE_URL}/gateway/v1/mge/service.sbr?serviceName=CRUDServiceProvider.saveRecord&outputType=json"

    try:
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"[ERRO] {e}")
        return None


def buscar_empenhos(access_token, pedido):
    """Busca os empenhos de um pedido"""
    query = f"""
    SELECT
        NUNOTA,
        CODPROD,
        CONTROLE,
        NUNOTAPEDVEN,
        QTDEMPENHO,
        PENDENTE
    FROM TGWEMPE
    WHERE NUNOTAPEDVEN = {pedido}
    ORDER BY CODPROD
    """
    return executar_query(access_token, query)


def main():
    print("=" * 80)
    print("TRANSFERIR EMPENHOS DO PEDIDO 1183490 PARA 1192177")
    print("=" * 80)

    access_token = autenticar()
    if not access_token:
        return

    print("[OK] Autenticado!")

    # 1. Buscar empenhos do pedido cancelado
    print(f"\n[1] Buscando empenhos do pedido CANCELADO ({PEDIDO_CANCELADO})...")
    result = buscar_empenhos(access_token, PEDIDO_CANCELADO)

    if not result or not result.get("rows"):
        print("Nenhum empenho encontrado no pedido cancelado!")
        return

    empenhos = []
    fields = result.get("fieldsMetadata", [])
    field_names = [f["name"] for f in fields]

    for row in result["rows"]:
        emp = dict(zip(field_names, row))
        empenhos.append(emp)

    print(f"\n[OK] {len(empenhos)} empenhos para transferir:")
    print(f"\n{'NUNOTA':>10} | {'CODPROD':>10} | {'CONTROLE':>10} | {'QTDEMP':>8}")
    print("-" * 50)
    for emp in empenhos:
        controle = emp.get('CONTROLE') or 'NULL'
        print(f"{emp['NUNOTA']:>10} | {emp['CODPROD']:>10} | {str(controle):>10} | {emp['QTDEMPENHO']:>8}")

    # 2. Buscar empenhos do pedido novo (para comparar)
    print(f"\n[2] Empenhos atuais do pedido NOVO ({PEDIDO_NOVO})...")
    result_novo = buscar_empenhos(access_token, PEDIDO_NOVO)
    if result_novo and result_novo.get("rows"):
        print(f"    {len(result_novo['rows'])} empenhos ja existentes")
    else:
        print("    Nenhum empenho ainda")

    # 3. Transferir empenhos (testar com 1 primeiro)
    print("\n" + "=" * 80)
    print("[3] TRANSFERINDO EMPENHOS...")
    print("=" * 80)

    # Testar com o primeiro
    emp = empenhos[0]
    controle = emp.get('CONTROLE') or ''

    print(f"\n--- Testando com CODPROD {emp['CODPROD']} ---")
    print(f"    De: NUNOTAPEDVEN = {PEDIDO_CANCELADO}")
    print(f"    Para: NUNOTAPEDVEN = {PEDIDO_NOVO}")

    # Tentar transferir
    result_transfer = save_record(access_token, "TGWEMPE", {
        "NUNOTA": emp['NUNOTA'],
        "CODPROD": emp['CODPROD'],
        "CONTROLE": controle,
        "NUNOTAPEDVEN": PEDIDO_NOVO  # <<< MUDA PARA O PEDIDO NOVO!
    })

    if result_transfer:
        print(f"\n[DEBUG] Status: {result_transfer.get('status')}")
        print(f"[DEBUG] Mensagem: {result_transfer.get('statusMessage', 'OK')}")

        if result_transfer.get("status") == "1":
            print("\n" + "=" * 80)
            print("[SUCESSO!] TRANSFERENCIA FUNCIONOU!")
            print("=" * 80)

            # Verificar se realmente transferiu
            print("\n[4] VERIFICANDO RESULTADO...")

            # Checar pedido cancelado
            result_check = buscar_empenhos(access_token, PEDIDO_CANCELADO)
            if result_check and result_check.get("rows"):
                qtd_cancelado = len(result_check["rows"])
                print(f"    Pedido {PEDIDO_CANCELADO}: {qtd_cancelado} empenhos restantes")
            else:
                print(f"    Pedido {PEDIDO_CANCELADO}: 0 empenhos (todos transferidos!)")

            # Checar pedido novo
            result_check2 = buscar_empenhos(access_token, PEDIDO_NOVO)
            if result_check2 and result_check2.get("rows"):
                qtd_novo = len(result_check2["rows"])
                print(f"    Pedido {PEDIDO_NOVO}: {qtd_novo} empenhos")

            # Perguntar se quer transferir o resto
            print("\n" + "=" * 80)
            print("PROXIMO PASSO")
            print("=" * 80)
            print(f"""
O teste funcionou! Para transferir TODOS os {len(empenhos)} empenhos:

1. Rode novamente com --all:
   python scripts/investigacao/transferir_empenho.py --all

2. OU via SQL (mais rapido):
   UPDATE TGWEMPE
   SET NUNOTAPEDVEN = {PEDIDO_NOVO}
   WHERE NUNOTAPEDVEN = {PEDIDO_CANCELADO};
   COMMIT;
""")
        else:
            print(f"\n[FALHOU] {result_transfer.get('statusMessage')}")
            print("""
A API nao permitiu a transferencia. Opcoes:
1. Tentar via SQL direto na sessao
2. Tentar via tela Central de Empenho no Sankhya
""")
    else:
        print("\n[ERRO] Sem resposta da API")


def transferir_todos():
    """Transfere todos os empenhos"""
    print("=" * 80)
    print("TRANSFERIR TODOS OS EMPENHOS")
    print("=" * 80)

    access_token = autenticar()
    if not access_token:
        return

    result = buscar_empenhos(access_token, PEDIDO_CANCELADO)
    if not result or not result.get("rows"):
        print("Nenhum empenho para transferir!")
        return

    fields = result.get("fieldsMetadata", [])
    field_names = [f["name"] for f in fields]

    sucesso = 0
    falha = 0

    for row in result["rows"]:
        emp = dict(zip(field_names, row))
        controle = emp.get('CONTROLE') or ''

        result_transfer = save_record(access_token, "TGWEMPE", {
            "NUNOTA": emp['NUNOTA'],
            "CODPROD": emp['CODPROD'],
            "CONTROLE": controle,
            "NUNOTAPEDVEN": PEDIDO_NOVO
        })

        if result_transfer and result_transfer.get("status") == "1":
            print(f"  [OK] CODPROD {emp['CODPROD']} transferido")
            sucesso += 1
        else:
            print(f"  [X] CODPROD {emp['CODPROD']} falhou")
            falha += 1

    print("\n" + "=" * 80)
    print(f"RESULTADO: {sucesso} transferidos, {falha} falharam")
    print("=" * 80)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        transferir_todos()
    else:
        main()
