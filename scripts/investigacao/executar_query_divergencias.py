"""
Executa a query V3 de divergencias diretamente via API Sankhya
Sem dependencia do servidor MCP
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
print("EXECUTANDO QUERY V3 DE DIVERGENCIAS")
print("=" * 80)

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

# 2. CARREGAR QUERY V3
print("\n[2] Carregando query V3 de divergencias...")
query_file = "query_divergencias_v3_definitiva.sql"

if not os.path.exists(query_file):
    print(f"[ERRO] Arquivo {query_file} nao encontrado!")
    exit(1)

with open(query_file, 'r', encoding='utf-8') as f:
    query_sql = f.read()

# Remover comentarios SQL para enviar apenas a query
lines = []
for line in query_sql.split('\n'):
    line = line.strip()
    if line and not line.startswith('--'):
        lines.append(line)

query_clean = ' '.join(lines)
print(f"[OK] Query carregada ({len(query_clean)} caracteres)")

# 3. EXECUTAR QUERY
print("\n[3] Executando query V3...")
print("(pode demorar alguns segundos...)")

query_payload = {
    "requestBody": {
        "sql": query_clean
    }
}

query_response = requests.post(
    "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    json=query_payload,
    timeout=120  # Query pode demorar
)

print(f"Status: {query_response.status_code}")

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

# 4. PROCESSAR RESULTADO
print("\n[4] Processando resultado...")

response_body = result.get("responseBody", {})
fields = response_body.get("fieldsMetadata", [])
rows = response_body.get("rows", [])

print(f"Total de registros: {len(rows)}")

if len(rows) == 0:
    print("\n[INFO] Nenhuma divergencia encontrada!")
else:
    print(f"\n[INFO] Encontradas {len(rows)} divergencias!")

    # Salvar JSON
    output_json = "resultado_divergencias_v3.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[OK] Resultado salvo em: {output_json}")

    # Mostrar primeiros 5 registros
    print("\n[PREVIEW] Primeiras 5 divergencias:")
    print("-" * 80)

    field_names = [f["name"] for f in fields]

    # Header
    header = " | ".join([f"{name[:15]:15}" for name in field_names[:8]])
    print(header)
    print("-" * 80)

    # Linhas
    for i, row in enumerate(rows[:5]):
        values = " | ".join([f"{str(val)[:15]:15}" for val in row[:8]])
        print(values)

print("\n" + "=" * 80)
print("CONCLUIDO!")
print("=" * 80)
print(f"\nProximo passo:")
print(f"  python gerar_relatorio.py")
print(f"\nOu copie o conteudo de '{output_json}' e cole no script gerar_relatorio.py")
