"""
Executa query V4 - Relatorio Consolidado por Produto
Retorna 1 linha por produto com analise completa
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
print("RELATORIO CONSOLIDADO POR PRODUTO - V4")
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

# 2. CARREGAR QUERY V4
print("\n[2] Carregando query V4...")
query_file = "query_relatorio_consolidado_v4_simplificado.sql"

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
print("\n[3] Executando query V4...")
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
    timeout=120
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

print(f"Total de produtos com divergencia: {len(rows)}")

if len(rows) == 0:
    print("\n[INFO] Nenhum produto com divergencia encontrado!")
else:
    print(f"\n[INFO] Encontrados {len(rows)} produtos com divergencia!")

    # Salvar JSON
    output_json = "resultado_consolidado_v4.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[OK] Resultado salvo em: {output_json}")

    # Mostrar primeiros 5 produtos
    print("\n[PREVIEW] Top 5 produtos com maior divergencia:")
    print("-" * 80)

    field_names = [f["name"] for f in fields]

    # Header
    header = " | ".join([f"{name[:12]:12}" for name in field_names[:8]])
    print(header)
    print("-" * 80)

    # Linhas
    for i, row in enumerate(rows[:5]):
        values = " | ".join([f"{str(val)[:12]:12}" for val in row[:8]])
        print(values)

    # Estatisticas
    print("\n" + "=" * 80)
    print("ESTATISTICAS")
    print("=" * 80)

    total_estoque = sum(row[4] for row in rows)  # ESTOQUE
    total_wms = sum(row[8] for row in rows)      # SALDO_WMS_TELA
    total_div = sum(abs(row[10]) for row in rows)  # DIVERGENCIA_ERP_WMS (indice 10 na versao simplificada)

    print(f"\nTotal Estoque (TGFEST): {total_estoque:,.0f} unidades".replace(',', '.'))
    print(f"Total WMS Disponivel:   {total_wms:,.0f} unidades".replace(',', '.'))
    print(f"Total Divergencia:      {total_div:,.0f} unidades".replace(',', '.'))

    # Produtos com maior divergencia
    print("\n[TOP 10] Produtos com maior divergencia absoluta:")
    print("-" * 80)
    print(f"{'CODPROD':<10} | {'DESCRICAO':<30} | {'ESTOQUE':>10} | {'WMS':>10} | {'DIVERGENCIA':>12}")
    print("-" * 80)

    for i, row in enumerate(rows[:10]):
        codprod = row[1]
        descr = str(row[2])[:30]
        estoque = row[4]
        wms = row[8]
        div = row[10]  # DIVERGENCIA_ERP_WMS

        print(f"{codprod:<10} | {descr:<30} | {estoque:>10.0f} | {wms:>10.0f} | {div:>+12.0f}")

print("\n" + "=" * 80)
print("CONCLUIDO!")
print("=" * 80)
print(f"\nProximo passo:")
print(f"  python gerar_html_consolidado.py")
print(f"\nOu use o JSON '{output_json}' para criar seu proprio relatorio")
