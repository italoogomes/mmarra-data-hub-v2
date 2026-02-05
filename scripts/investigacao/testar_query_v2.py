# -*- coding: utf-8 -*-
"""
Testa a query V2 com deteccao de inconsistencia
"""

import os
import json
import requests
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), '..', '..', 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')

print("=" * 80)
print("TESTE DA QUERY V2 - COM DETECCAO DE INCONSISTENCIA")
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

# 2. CARREGAR QUERY V2
print("\n[2] Carregando query V2...")
query_file = os.path.join(os.path.dirname(__file__), '..', '..', 'queries', 'query_empenho_com_cotacao_v2.sql')

if not os.path.exists(query_file):
    print(f"[ERRO] Arquivo {query_file} nao encontrado!")
    exit(1)

with open(query_file, 'r', encoding='utf-8') as f:
    query_sql = f.read()

# Remover comentarios SQL
lines = []
for line in query_sql.split('\n'):
    line = line.strip()
    if line and not line.startswith('--'):
        lines.append(line)

query_clean = ' '.join(lines)
print(f"[OK] Query carregada ({len(query_clean)} caracteres)")

# 3. EXECUTAR QUERY
print("\n[3] Executando query V2...")
print("(pode demorar 30-60 segundos...)")

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
    timeout=180
)

print(f"Status HTTP: {query_response.status_code}")

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
    print("\n[INFO] Nenhum registro encontrado!")
else:
    print(f"\n[INFO] Encontrados {len(rows)} registros!")

    field_names = [f["name"] for f in fields]
    print(f"\nColunas: {', '.join(field_names)}")

    # Buscar indice das colunas relevantes
    status_empenho_idx = None
    cod_cotacao_idx = None
    nunota_idx = None
    codprod_idx = None

    for i, f in enumerate(fields):
        if f["name"] == "STATUS_EMPENHO_ITEM":
            status_empenho_idx = i
        elif f["name"] == "COD_COTACAO":
            cod_cotacao_idx = i
        elif f["name"] == "NUM_UNICO":
            nunota_idx = i
        elif f["name"] == "COD_PROD":
            codprod_idx = i

    # Contar inconsistencias
    inconsistencias = []
    com_cotacao = 0

    for row in rows:
        if status_empenho_idx and row[status_empenho_idx] and 'inconsistencia' in str(row[status_empenho_idx]).lower():
            inconsistencias.append(row)
        if cod_cotacao_idx and row[cod_cotacao_idx]:
            com_cotacao += 1

    print(f"\nRegistros com cotacao: {com_cotacao}")
    print(f"Registros com INCONSISTENCIA: {len(inconsistencias)}")

    if inconsistencias:
        print("\n" + "=" * 80)
        print("REGISTROS COM INCONSISTENCIA DETECTADA:")
        print("=" * 80)
        for row in inconsistencias[:10]:
            nunota = row[nunota_idx] if nunota_idx else "?"
            codprod = row[codprod_idx] if codprod_idx else "?"
            cotacao = row[cod_cotacao_idx] if cod_cotacao_idx else "?"
            print(f"  Pedido {nunota}, Produto {codprod}, Cotacao {cotacao}")

    # Verificar pedido 1191930 especificamente
    print("\n" + "=" * 80)
    print("VERIFICANDO PEDIDO 1191930:")
    print("=" * 80)

    for row in rows:
        if nunota_idx and str(row[nunota_idx]) == "1191930":
            print(f"\nProduto: {row[codprod_idx] if codprod_idx else '?'}")
            print(f"  Cotacao: {row[cod_cotacao_idx] if cod_cotacao_idx else '?'}")
            print(f"  Status Empenho: {row[status_empenho_idx] if status_empenho_idx else '?'}")
            for i, f in enumerate(fields):
                if 'STATUS' in f["name"] or 'COTACAO' in f["name"] or 'INCONSIST' in f["name"].upper():
                    print(f"  {f['name']}: {row[i]}")

    # Salvar resultado
    output_file = os.path.join(os.path.dirname(__file__), '..', '..', 'output', 'json', 'resultado_empenho_v2.json')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Resultado salvo em: {output_file}")

print("\n" + "=" * 80)
print("CONCLUIDO!")
print("=" * 80)
