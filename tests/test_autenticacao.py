#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste de Autenticação Sankhya - Ambos os Métodos
"""

import requests
import json

print("=" * 70)
print("TESTE DE AUTENTICACAO SANKHYA")
print("=" * 70)

# =============================================================================
# MÉTODO 1: OAuth 2.0 (Gateway) - USADO NO MCP
# =============================================================================
print("\n[1/2] Testando OAuth 2.0 (Gateway)...")
print("-" * 70)

CLIENT_ID = "09ef3473-cb85-41d4-b6d4-473c15d39292"
CLIENT_SECRET = "7phfkche8hWHpWYBNWbEgf4xY4mPixp0"
X_TOKEN = "dca9f07d-bf0f-426c-b537-0e5b0ff1123d"

try:
    response = requests.post(
        "https://api.sankhya.com.br/gateway/v1/authenticate",
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

    print(f"Status Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")

    if response.status_code == 200:
        data = response.json()
        if "access_token" in data:
            print("\n✅ SUCESSO! Token OAuth 2.0 obtido:")
            print(f"   Token: {data['access_token'][:50]}...")
            oauth_token = data['access_token']
        else:
            print("\n⚠️ Resposta sem access_token")
            oauth_token = None
    else:
        print(f"\n❌ FALHA! Status: {response.status_code}")
        print(f"   Erro: {response.text}")
        oauth_token = None

except Exception as e:
    print(f"\n❌ ERRO: {str(e)}")
    oauth_token = None

# =============================================================================
# MÉTODO 2: MobileLogin (Usuário/Senha) - USADO NO POSTMAN
# =============================================================================
print("\n\n[2/2] Testando MobileLogin (Usuario/Senha)...")
print("-" * 70)
print("⚠️ Este método requer usuário e senha do Sankhya")
print("   (não temos essas credenciais no código)")

usuario = input("\nDigite o usuário Sankhya (ou Enter para pular): ").strip()

if usuario:
    senha = input("Digite a senha: ").strip()

    try:
        response = requests.post(
            "https://api.sankhya.com.br/mge/service.sbr",
            params={"serviceName": "MobileLoginSP.login"},
            headers={"Content-Type": "application/json"},
            json={
                "serviceName": "MobileLoginSP.login",
                "requestBody": {
                    "NOMUSU": {"$": usuario},
                    "INTERNO": {"$": senha},
                    "KEEPCONNECTED": {"$": "S"}
                }
            },
            timeout=30
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")

        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "1":
                jsessionid = data["responseBody"]["jsessionid"]["$"]
                print(f"\n✅ SUCESSO! JSESSIONID obtido:")
                print(f"   Token: {jsessionid}")

                # Testar query com JSESSIONID
                print("\n" + "="*70)
                print("TESTANDO QUERY COM JSESSIONID")
                print("="*70)

                test_sql = "SELECT COUNT(*) AS TOTAL FROM TGFCAB WHERE CODEMP = 7"

                response_query = requests.post(
                    "https://api.sankhya.com.br/mge/service.sbr",
                    params={
                        "serviceName": "DbExplorerSP.executeQuery",
                        "outputType": "json"
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Cookie": f"JSESSIONID={jsessionid}"
                    },
                    json={
                        "serviceName": "DbExplorerSP.executeQuery",
                        "requestBody": {
                            "sql": test_sql
                        }
                    },
                    timeout=30
                )

                print(f"\nQuery Status: {response_query.status_code}")
                print(f"Query Response:\n{json.dumps(response_query.json(), indent=2, ensure_ascii=False)}")

            else:
                print(f"\n❌ FALHA! Status: {data.get('status')}")
                print(f"   Mensagem: {data.get('statusMessage')}")
        else:
            print(f"\n❌ FALHA! Status: {response.status_code}")

    except Exception as e:
        print(f"\n❌ ERRO: {str(e)}")
else:
    print("Pulando teste MobileLogin...")

# =============================================================================
# RESUMO
# =============================================================================
print("\n\n" + "="*70)
print("RESUMO")
print("="*70)

if oauth_token:
    print("✅ OAuth 2.0: FUNCIONANDO")
    print(f"   Pode usar o MCP server como está")
else:
    print("❌ OAuth 2.0: NÃO FUNCIONOU")
    print(f"   Opção 1: Verificar se credenciais OAuth ainda são válidas")
    print(f"   Opção 2: Modificar MCP para usar MobileLogin (usuário/senha)")

print("\n" + "="*70)
