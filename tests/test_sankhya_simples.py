"""
Teste simples de autenticação e query no Sankhya
Sem dependências do MCP - apenas requests
"""

import os
import json
import requests
from dotenv import load_dotenv

# Carregar credenciais do .env
env_path = os.path.join(os.path.dirname(__file__), 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

print("=" * 80)
print("TESTE SIMPLES - SANKHYA API")
print("=" * 80)

# 1. AUTENTICAÇÃO
print("\n[1] Testando autenticacao OAuth 2.0...")
print(f"URL: https://api.sankhya.com.br/authenticate")

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

print(f"Status: {auth_response.status_code}")

if auth_response.status_code == 200:
    auth_data = auth_response.json()
    access_token = auth_data.get("access_token")
    print("[OK] Autenticacao OK!")
    print(f"Token obtido: {access_token[:50]}...")
else:
    print("[ERRO] Autenticacao FALHOU!")
    print(f"Resposta: {auth_response.text}")
    exit(1)

# 2. EXECUTAR QUERY SIMPLES
print("\n[2] Testando execucao de query...")
print(f"URL: https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json")

# Query simples: contar produtos
query_sql = """
SELECT COUNT(*) AS TOTAL_PRODUTOS
FROM TGFPRO
WHERE ROWNUM <= 1
"""

query_payload = {
    "requestBody": {
        "sql": query_sql
    }
}

print(f"Query: {query_sql.strip()[:100]}...")
print(f"Payload: {json.dumps(query_payload, indent=2)}")

query_response = requests.post(
    "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    json=query_payload,
    timeout=30
)

print(f"Status: {query_response.status_code}")
print(f"Content-Type: {query_response.headers.get('Content-Type')}")
print(f"Resposta texto (primeiros 500 chars): {query_response.text[:500]}")

if query_response.status_code == 200:
    try:
        result = query_response.json()

        if result.get("status") == "1":
            print("[OK] Query executada com SUCESSO!")
            print("\nResultado:")
            print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
        else:
            print("[ERRO] Query FALHOU!")
            print(f"Status: {result.get('status')}")
            print(f"Mensagem: {result.get('statusMessage')}")
            print("\nResposta completa:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
    except json.JSONDecodeError:
        print("[ERRO] Resposta nao eh JSON valido!")
        print(f"Resposta completa: {query_response.text}")
else:
    print("[ERRO] Requisicao FALHOU!")
    print(f"Resposta: {query_response.text}")

print("\n" + "=" * 80)
print("FIM DO TESTE")
print("=" * 80)
