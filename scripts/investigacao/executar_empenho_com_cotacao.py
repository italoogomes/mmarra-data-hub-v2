# -*- coding: utf-8 -*-
"""
Executa query de Gestão de Empenho com Cotação
Inclui campos de cotação: Responsável, Código e Status
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
print("RELATORIO DE GESTAO DE EMPENHO COM COTACAO")
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

# 2. CARREGAR QUERY
print("\n[2] Carregando query de empenho com cotacao...")
query_file = "query_empenho_com_cotacao_sem_parametros.sql"

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
print("\n[3] Executando query...")
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

print(f"Total de registros: {len(rows)}")

if len(rows) == 0:
    print("\n[INFO] Nenhum registro encontrado!")
else:
    print(f"\n[INFO] Encontrados {len(rows)} registros!")

    # Salvar JSON
    output_json = "resultado_empenho_com_cotacao.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"[OK] Resultado salvo em: {output_json}")

    # Mostrar primeiros 5 registros
    print("\n[PREVIEW] Primeiros 5 registros:")
    print("-" * 80)

    field_names = [f["name"] for f in fields]

    # Header (primeiras 8 colunas)
    header = " | ".join([f"{name[:12]:12}" for name in field_names[:8]])
    print(header)
    print("-" * 80)

    # Linhas
    for i, row in enumerate(rows[:5]):
        values = " | ".join([f"{str(val)[:12]:12}" for val in row[:8]])
        print(values)

    # Verificar se há dados de cotação
    print("\n" + "=" * 80)
    print("ANALISE DE DADOS DE COTACAO")
    print("=" * 80)

    # Encontrar índices das colunas de cotação
    cod_cotacao_idx = None
    nome_resp_idx = None
    status_cotacao_idx = None

    for i, field in enumerate(fields):
        if field["name"] == "COD_COTACAO":
            cod_cotacao_idx = i
        elif field["name"] == "NOME_RESP_COTACAO":
            nome_resp_idx = i
        elif field["name"] == "STATUS_COTACAO":
            status_cotacao_idx = i

    if cod_cotacao_idx is not None:
        cotacoes_preenchidas = sum(1 for row in rows if row[cod_cotacao_idx] is not None)
        print(f"\nRegistros com cotacao: {cotacoes_preenchidas} de {len(rows)}")

        if cotacoes_preenchidas > 0:
            print("\n[SAMPLE] Exemplos de registros com cotacao:")
            print("-" * 80)
            print(f"{'Num_Unico':<12} | {'Cod_Prod':<10} | {'Cod_Cotacao':<12} | {'Status':<15} | {'Responsavel':<20}")
            print("-" * 80)

            count = 0
            for row in rows:
                if row[cod_cotacao_idx] is not None and count < 10:
                    nunota = row[7] if len(row) > 7 else ""  # Num_Unico geralmente está no índice 7
                    codprod = row[16] if len(row) > 16 else ""  # Cod_Prod
                    cod_cot = row[cod_cotacao_idx] if cod_cotacao_idx < len(row) else ""
                    status = row[status_cotacao_idx] if status_cotacao_idx is not None and status_cotacao_idx < len(row) else ""
                    resp = str(row[nome_resp_idx])[:20] if nome_resp_idx is not None and nome_resp_idx < len(row) and row[nome_resp_idx] else ""

                    print(f"{str(nunota):<12} | {str(codprod):<10} | {str(cod_cot):<12} | {str(status):<15} | {resp:<20}")
                    count += 1
    else:
        print("\n[AVISO] Colunas de cotacao nao encontradas no resultado!")

print("\n" + "=" * 80)
print("CONCLUIDO!")
print("=" * 80)
print(f"\nProximo passo:")
print(f"  python gerar_html_empenho.py")
print(f"\nOu use o JSON '{output_json}' para criar seu proprio relatorio")
