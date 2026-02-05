# -*- coding: utf-8 -*-
"""
Liberar empenhos do pedido cancelado 1183490 via SESSAO WEB do Sankhya
Baseado no script de integracao BEPO que funciona!

Usa MobileLoginSP.login + DatasetSP para operacoes
"""

import os
import requests
from dotenv import load_dotenv

# Caminho do .env na raiz do projeto
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
env_path = os.path.join(project_root, 'mcp_sankhya', '.env')
load_dotenv(env_path)

# Credenciais API (para consultas)
CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

# Credenciais sessao web (para operacoes)
SANKHYA_USER = os.getenv('SANKHYA_USER', 'SUP')
SANKHYA_PASS = os.getenv('SANKHYA_PASS', '')
SANKHYA_WEB_URL = os.getenv('SANKHYA_WEB_URL', 'https://mmarra.sankhyacloud.com.br')

BASE_URL = "https://api.sankhya.com.br"
PEDIDO_CANCELADO = 1183490


def autenticar_api():
    """Autentica na API Gateway e retorna o access_token"""
    auth_response = requests.post(
        f"{BASE_URL}/authenticate",
        headers={"Content-Type": "application/x-www-form-urlencoded", "X-Token": X_TOKEN},
        data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"},
        timeout=30
    )
    if auth_response.status_code != 200:
        print(f"[ERRO] Autenticacao API falhou: {auth_response.status_code}")
        return None
    return auth_response.json()["access_token"]


def executar_query(access_token, query_sql):
    """Executa uma query SELECT via API"""
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


def criar_sessao_web():
    """
    Cria sessao web no Sankhya (igual ao script BEPO).
    Retorna a sessao autenticada.
    """
    if not SANKHYA_PASS:
        raise Exception("SANKHYA_PASS nao configurado no .env")

    session = requests.Session()

    # Login para obter sessao
    login_url = f"{SANKHYA_WEB_URL}/mge/service.sbr?serviceName=MobileLoginSP.login&outputType=json"
    login_payload = {
        "serviceName": "MobileLoginSP.login",
        "requestBody": {
            "NOMUSU": {"$": SANKHYA_USER},
            "INTERNO": {"$": SANKHYA_PASS},
            "KEEPCONNECTED": {"$": "S"}
        }
    }

    print(f"[DEBUG] Login URL: {login_url}")
    print(f"[DEBUG] Usuario: {SANKHYA_USER}")

    login_response = session.post(login_url, json=login_payload)
    login_result = login_response.json()

    print(f"[DEBUG] Login status: {login_result.get('status')}")
    print(f"[DEBUG] Login msg: {login_result.get('statusMessage', 'OK')[:100]}")

    if login_result.get('status') != '1':
        raise Exception(f"Erro no login web: {login_result.get('statusMessage')}")

    return session


def fechar_sessao_web(session):
    """Fecha a sessao web"""
    try:
        logout_url = f"{SANKHYA_WEB_URL}/mge/service.sbr?serviceName=MobileLoginSP.logout&outputType=json"
        session.post(logout_url)
    except:
        pass


def deletar_empenho_via_sessao(session, empenho):
    """
    Tenta deletar empenho via sessao web usando DatasetSP.remove
    """
    print(f"\n--- Deletando empenho CODPROD {empenho['CODPROD']} ---")

    controle = empenho.get('CONTROLE') or ''

    # Metodo 1: DatasetSP.remove
    remove_url = f"{SANKHYA_WEB_URL}/mge/service.sbr?serviceName=DatasetSP.remove&outputType=json"

    # Formato baseado no padrao do Sankhya
    remove_payload = {
        "serviceName": "DatasetSP.remove",
        "requestBody": {
            "entityName": "TGWEMPE",
            "criteria": {
                "expression": {
                    "$": f"NUNOTA = {empenho['NUNOTA']} AND CODPROD = {empenho['CODPROD']} AND NUNOTAPEDVEN = {empenho['NUNOTAPEDVEN']}"
                }
            }
        }
    }

    print(f"[DEBUG] URL: {remove_url}")
    print(f"[DEBUG] Criteria: NUNOTA={empenho['NUNOTA']}, CODPROD={empenho['CODPROD']}, NUNOTAPEDVEN={empenho['NUNOTAPEDVEN']}")

    response = session.post(remove_url, json=remove_payload)
    result = response.json()

    print(f"[DEBUG] Status: {result.get('status')}")
    print(f"[DEBUG] Mensagem: {result.get('statusMessage', 'OK')[:200]}")

    if result.get('status') == '1':
        return True, "DatasetSP.remove"

    # Metodo 2: CRUDServiceProvider.removeRecord via sessao web
    crud_url = f"{SANKHYA_WEB_URL}/mge/service.sbr?serviceName=CRUDServiceProvider.removeRecord&outputType=json"

    crud_payload = {
        "serviceName": "CRUDServiceProvider.removeRecord",
        "requestBody": {
            "dataSet": {
                "rootEntity": "TGWEMPE",
                "includePresentationFields": "N",
                "dataRow": {
                    "localFields": {
                        "NUNOTA": {"$": str(empenho['NUNOTA'])},
                        "CODPROD": {"$": str(empenho['CODPROD'])},
                        "CONTROLE": {"$": controle},
                        "NUNOTAPEDVEN": {"$": str(empenho['NUNOTAPEDVEN'])}
                    }
                }
            }
        }
    }

    print(f"\n[DEBUG] Tentando CRUDServiceProvider via sessao...")
    response2 = session.post(crud_url, json=crud_payload)
    result2 = response2.json()

    print(f"[DEBUG] Status: {result2.get('status')}")
    print(f"[DEBUG] Mensagem: {result2.get('statusMessage', 'OK')[:200]}")

    if result2.get('status') == '1':
        return True, "CRUDServiceProvider.removeRecord (sessao)"

    # Metodo 3: MGECoreServiceSP.deleteRecords via sessao web
    mge_url = f"{SANKHYA_WEB_URL}/mge/service.sbr?serviceName=MGECoreServiceSP.deleteRecords&outputType=json"

    mge_payload = {
        "serviceName": "MGECoreServiceSP.deleteRecords",
        "requestBody": {
            "entity": {"$": "TGWEMPE"},
            "criteria": {
                "expression": {
                    "$": f"NUNOTA = {empenho['NUNOTA']} AND CODPROD = {empenho['CODPROD']} AND NUNOTAPEDVEN = {empenho['NUNOTAPEDVEN']}"
                }
            }
        }
    }

    print(f"\n[DEBUG] Tentando MGECoreServiceSP via sessao...")
    response3 = session.post(mge_url, json=mge_payload)
    result3 = response3.json()

    print(f"[DEBUG] Status: {result3.get('status')}")
    print(f"[DEBUG] Mensagem: {result3.get('statusMessage', 'OK')[:200]}")

    if result3.get('status') == '1':
        return True, "MGECoreServiceSP.deleteRecords (sessao)"

    # Metodo 4: Tentar via DbExplorerSP.executeStatement (DELETE direto)
    # CUIDADO: Pode nao ter permissao
    delete_url = f"{SANKHYA_WEB_URL}/mge/service.sbr?serviceName=DbExplorerSP.executeStatement&outputType=json"

    delete_sql = f"""
    DELETE FROM TGWEMPE
    WHERE NUNOTA = {empenho['NUNOTA']}
      AND CODPROD = {empenho['CODPROD']}
      AND NUNOTAPEDVEN = {empenho['NUNOTAPEDVEN']}
    """

    delete_payload = {
        "serviceName": "DbExplorerSP.executeStatement",
        "requestBody": {
            "sql": delete_sql.strip()
        }
    }

    print(f"\n[DEBUG] Tentando DELETE direto via DbExplorerSP.executeStatement...")
    response4 = session.post(delete_url, json=delete_payload)
    result4 = response4.json()

    print(f"[DEBUG] Status: {result4.get('status')}")
    print(f"[DEBUG] Mensagem: {result4.get('statusMessage', 'OK')[:200]}")

    if result4.get('status') == '1':
        return True, "DbExplorerSP.executeStatement (DELETE SQL)"

    return False, None


def buscar_empenhos(access_token):
    """Busca os empenhos do pedido cancelado"""
    query = f"""
    SELECT
        NUNOTA,
        CODPROD,
        CONTROLE,
        NUNOTAPEDVEN,
        QTDEMPENHO,
        PENDENTE
    FROM TGWEMPE
    WHERE NUNOTAPEDVEN = {PEDIDO_CANCELADO}
    ORDER BY CODPROD
    """
    return executar_query(access_token, query)


def main():
    print("=" * 80)
    print("LIBERAR EMPENHOS VIA SESSAO WEB (metodo BEPO)")
    print("=" * 80)

    # Verificar credenciais
    if not SANKHYA_PASS:
        print("\n[ERRO] SANKHYA_PASS nao configurado no .env!")
        print("       Adicione: SANKHYA_PASS=sua_senha")
        return

    # 1. Autenticar na API (para consultas)
    print("\n[1] Autenticando na API...")
    access_token = autenticar_api()
    if not access_token:
        return
    print("[OK] API autenticada!")

    # 2. Buscar empenhos
    print(f"\n[2] Buscando empenhos do pedido {PEDIDO_CANCELADO}...")
    result = buscar_empenhos(access_token)

    if not result or not result.get("rows"):
        print("Nenhum empenho encontrado!")
        return

    empenhos = []
    fields = result.get("fieldsMetadata", [])
    field_names = [f["name"] for f in fields]

    for row in result["rows"]:
        emp = dict(zip(field_names, row))
        empenhos.append(emp)

    print(f"\n[OK] {len(empenhos)} empenhos encontrados:")
    print(f"\n{'NUNOTA':>10} | {'CODPROD':>10} | {'CONTROLE':>10} | {'QTDEMP':>8}")
    print("-" * 50)
    for emp in empenhos:
        controle = emp.get('CONTROLE') or 'NULL'
        print(f"{emp['NUNOTA']:>10} | {emp['CODPROD']:>10} | {str(controle):>10} | {emp['QTDEMPENHO']:>8}")

    # 3. Criar sessao web
    print("\n[3] Criando sessao web no Sankhya...")
    try:
        session = criar_sessao_web()
        print("[OK] Sessao web criada!")
    except Exception as e:
        print(f"[ERRO] {e}")
        return

    # 4. Tentar deletar o primeiro empenho como teste
    print("\n" + "=" * 80)
    print("[4] TESTANDO DELECAO COM 1 EMPENHO...")
    print("=" * 80)

    emp = empenhos[0]
    sucesso, metodo = deletar_empenho_via_sessao(session, emp)

    if sucesso:
        print("\n" + "=" * 80)
        print(f"[SUCESSO!] Metodo que funcionou: {metodo}")
        print("=" * 80)

        # Verificar se foi deletado
        print("\n[5] Verificando se foi deletado...")
        result2 = buscar_empenhos(access_token)
        if result2 and result2.get("rows"):
            qtd = len(result2["rows"])
            print(f"    Empenhos restantes: {qtd} (era {len(empenhos)})")
            if qtd < len(empenhos):
                print("\n    [CONFIRMADO] Empenho foi deletado!")
                print(f"\n    Para deletar TODOS os {qtd} restantes, rode:")
                print(f"    python scripts/investigacao/liberar_empenho_sessao_web.py --all")
        else:
            print("    Todos os empenhos foram deletados!")
    else:
        print("\n[FALHOU] Nenhum metodo funcionou via sessao web")
        print("""
A unica opcao restante e SQL DIRETO:

DELETE FROM TGWEMPE WHERE NUNOTAPEDVEN = 1183490;
COMMIT;

Execute isso na sua sessao do banco.
""")

    # 5. Fechar sessao
    fechar_sessao_web(session)
    print("\n[OK] Sessao web fechada")


def deletar_todos():
    """Deleta todos os empenhos"""
    print("=" * 80)
    print("DELETAR TODOS OS EMPENHOS")
    print("=" * 80)

    if not SANKHYA_PASS:
        print("[ERRO] SANKHYA_PASS nao configurado!")
        return

    access_token = autenticar_api()
    if not access_token:
        return

    result = buscar_empenhos(access_token)
    if not result or not result.get("rows"):
        print("Nenhum empenho para deletar!")
        return

    fields = result.get("fieldsMetadata", [])
    field_names = [f["name"] for f in fields]

    session = criar_sessao_web()

    sucesso = 0
    falha = 0

    for row in result["rows"]:
        emp = dict(zip(field_names, row))
        ok, metodo = deletar_empenho_via_sessao(session, emp)
        if ok:
            print(f"  [OK] CODPROD {emp['CODPROD']} deletado via {metodo}")
            sucesso += 1
        else:
            print(f"  [X] CODPROD {emp['CODPROD']} falhou")
            falha += 1

    fechar_sessao_web(session)

    print("\n" + "=" * 80)
    print(f"RESULTADO: {sucesso} deletados, {falha} falharam")
    print("=" * 80)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        deletar_todos()
    else:
        main()
