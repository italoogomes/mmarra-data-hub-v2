# -*- coding: utf-8 -*-
"""
Tentar liberar empenhos usando o mesmo padrao de UPDATE que funciona
Baseado em: corrigir-medidas.py e limpa-complemento.py
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
    Baseado em corrigir-medidas.py e limpa-complemento.py
    """
    # Construir localFields no formato exato
    local_fields = {}
    for key, value in fields.items():
        if value is None:
            local_fields[key] = {}  # Campo null
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

    print(f"\n[DEBUG] URL: {url}")
    print(f"[DEBUG] Entity: {entity}")
    print(f"[DEBUG] Fields: {fields}")

    try:
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        print(f"[DEBUG] Status: {response.status_code}")
        print(f"[DEBUG] Response: {response.text[:500]}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"[ERRO] {e}")
        return None


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
    """
    return executar_query(access_token, query)


def main():
    print("=" * 80)
    print("LIBERAR EMPENHOS - METODO UPDATE (igual scripts que funcionam)")
    print("=" * 80)

    access_token = autenticar()
    if not access_token:
        return

    print("[OK] Autenticado!")

    # 1. Buscar empenhos
    print("\n[1] Buscando empenhos do pedido cancelado...")
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

    # 2. Tentar metodos diferentes
    print("\n" + "=" * 80)
    print("[2] TENTANDO LIBERAR VIA UPDATE...")
    print("=" * 80)

    # Pegar primeiro empenho para teste
    emp = empenhos[0]
    controle = emp.get('CONTROLE') or ''

    # METODO A: Zerar QTDEMPENHO (igual ao padrao dos seus scripts)
    print("\n--- METODO A: Zerar QTDEMPENHO ---")
    result_a = save_record(access_token, "TGWEMPE", {
        "NUNOTA": emp['NUNOTA'],
        "CODPROD": emp['CODPROD'],
        "CONTROLE": controle,
        "NUNOTAPEDVEN": emp['NUNOTAPEDVEN'],
        "QTDEMPENHO": "0"
    })
    if result_a and result_a.get("status") == "1":
        print("[SUCESSO!] Metodo A funcionou!")
    else:
        print(f"[FALHOU] {result_a.get('statusMessage') if result_a else 'Sem resposta'}")

    # METODO B: Setar PENDENTE = 'N'
    print("\n--- METODO B: Setar PENDENTE = N ---")
    result_b = save_record(access_token, "TGWEMPE", {
        "NUNOTA": emp['NUNOTA'],
        "CODPROD": emp['CODPROD'],
        "CONTROLE": controle,
        "NUNOTAPEDVEN": emp['NUNOTAPEDVEN'],
        "PENDENTE": "N"
    })
    if result_b and result_b.get("status") == "1":
        print("[SUCESSO!] Metodo B funcionou!")
    else:
        print(f"[FALHOU] {result_b.get('statusMessage') if result_b else 'Sem resposta'}")

    # METODO C: Usar NUNOTAPEDVEN = 0 (em vez de null)
    print("\n--- METODO C: Setar NUNOTAPEDVEN = 0 ---")
    result_c = save_record(access_token, "TGWEMPE", {
        "NUNOTA": emp['NUNOTA'],
        "CODPROD": emp['CODPROD'],
        "CONTROLE": controle,
        "NUNOTAPEDVEN": "0"
    })
    if result_c and result_c.get("status") == "1":
        print("[SUCESSO!] Metodo C funcionou!")
    else:
        print(f"[FALHOU] {result_c.get('statusMessage') if result_c else 'Sem resposta'}")

    # 3. Verificar se algo mudou
    print("\n" + "=" * 80)
    print("[3] VERIFICANDO SE ALGO MUDOU...")
    print("=" * 80)

    result2 = buscar_empenhos(access_token)
    if result2 and result2.get("rows"):
        print(f"\nAinda existem {len(result2['rows'])} empenhos")

        # Mostrar se algo mudou
        for row in result2["rows"][:3]:
            emp2 = dict(zip(field_names, row))
            print(f"  CODPROD {emp2['CODPROD']}: QTDEMP={emp2['QTDEMPENHO']}, PENDENTE={emp2.get('PENDENTE')}")
    else:
        print("\n[OK] Empenhos removidos/zerados com sucesso!")

    print("\n" + "=" * 80)
    print("CONCLUSAO")
    print("=" * 80)
    print("""
Se NENHUM metodo funcionou, a tabela TGWEMPE provavelmente tem:
- Triggers que impedem modificacao direta
- Constraints de integridade referencial
- Regras de negocio no servidor Sankhya

Neste caso, a unica opcao e:
1. Via TELA do Sankhya (Central de Empenho)
2. Via SQL DIRETO no banco (ja criamos: scripts/sql/liberar_empenho_1183490.sql)
""")


if __name__ == "__main__":
    main()
