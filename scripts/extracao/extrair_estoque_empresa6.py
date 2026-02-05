# -*- coding: utf-8 -*-
"""
Extrai estoque da empresa 6
"""

import os
import sys
import json
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Adicionar src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Carregar credenciais
env_path = os.path.join(os.path.dirname(__file__), '..', 'mcp_sankhya', '.env')
load_dotenv(env_path)

CLIENT_ID = os.getenv('SANKHYA_CLIENT_ID')
CLIENT_SECRET = os.getenv('SANKHYA_CLIENT_SECRET')
X_TOKEN = os.getenv('SANKHYA_X_TOKEN')
AZURE_STORAGE_ACCOUNT = os.getenv('AZURE_STORAGE_ACCOUNT')
AZURE_STORAGE_KEY = os.getenv('AZURE_STORAGE_KEY')
AZURE_CONTAINER = os.getenv('AZURE_CONTAINER', 'datahub')

CODEMP = 6  # Empresa a extrair

print("=" * 80)
print(f"EXTRACAO DE ESTOQUE - EMPRESA {CODEMP}")
print("=" * 80)

# 1. Autenticar
print("\n[1] Autenticando no Sankhya...")
auth_response = requests.post(
    "https://api.sankhya.com.br/authenticate",
    headers={"Content-Type": "application/x-www-form-urlencoded", "X-Token": X_TOKEN},
    data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"},
    timeout=30
)

if auth_response.status_code != 200:
    print(f"[ERRO] Autenticacao falhou: {auth_response.text}")
    sys.exit(1)

access_token = auth_response.json()["access_token"]
print("[OK] Autenticado!")

# 2. Query de estoque
query = f"""
SELECT
    e.CODEMP,
    e.CODPROD,
    p.DESCRPROD,
    p.REFERENCIA,
    e.CODLOCAL,
    l.DESCRLOCAL,
    e.CONTROLE,
    NVL(e.ESTOQUE, 0) AS ESTOQUE,
    NVL(e.RESERVADO, 0) AS RESERVADO,
    NVL(e.ESTOQUE, 0) - NVL(e.RESERVADO, 0) AS DISPONIVEL,
    p.ATIVO,
    p.CODGRUPOPROD,
    g.DESCRGRUPOPROD
FROM TGFEST e
LEFT JOIN TGFPRO p ON p.CODPROD = e.CODPROD
LEFT JOIN TGFLOC l ON l.CODLOCAL = e.CODLOCAL
LEFT JOIN TGFGRU g ON g.CODGRUPOPROD = p.CODGRUPOPROD
WHERE e.CODEMP = {CODEMP}
  AND NVL(e.ESTOQUE, 0) > 0
ORDER BY e.CODPROD, e.CODLOCAL
"""

print(f"\n[2] Executando query para empresa {CODEMP}...")
print("(pode demorar alguns segundos...)")

query_payload = {"requestBody": {"sql": query}}
query_response = requests.post(
    "https://api.sankhya.com.br/gateway/v1/mge/service.sbr?serviceName=DbExplorerSP.executeQuery&outputType=json",
    headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
    json=query_payload,
    timeout=120
)

if query_response.status_code != 200:
    print(f"[ERRO] Query falhou: {query_response.text}")
    sys.exit(1)

result = query_response.json()

if result.get("status") != "1":
    print(f"[ERRO] {result.get('statusMessage')}")
    sys.exit(1)

print("[OK] Query executada!")

# 3. Processar resultado
response_body = result.get("responseBody", {})
fields = response_body.get("fieldsMetadata", [])
rows = response_body.get("rows", [])

print(f"\n[3] Processando {len(rows)} registros...")

if len(rows) == 0:
    print("[INFO] Nenhum registro encontrado para a empresa 6!")
    sys.exit(0)

# Converter para DataFrame
field_names = [f["name"] for f in fields]
df = pd.DataFrame(rows, columns=field_names)

# Estatisticas
print(f"\n[INFO] Estatisticas:")
print(f"  - Total de registros: {len(df)}")
print(f"  - Produtos unicos: {df['CODPROD'].nunique()}")
print(f"  - Locais unicos: {df['CODLOCAL'].nunique()}")
print(f"  - Estoque total: {df['ESTOQUE'].sum():,.0f}")
print(f"  - Reservado total: {df['RESERVADO'].sum():,.0f}")
print(f"  - Disponivel total: {df['DISPONIVEL'].sum():,.0f}")

# 4. Salvar localmente
output_dir = os.path.join(os.path.dirname(__file__), '..', 'output', 'estoque')
os.makedirs(output_dir, exist_ok=True)

parquet_file = os.path.join(output_dir, f'estoque_empresa{CODEMP}.parquet')
csv_file = os.path.join(output_dir, f'estoque_empresa{CODEMP}.csv')

df.to_parquet(parquet_file, index=False)
df.to_csv(csv_file, index=False, encoding='utf-8-sig')

print(f"\n[4] Arquivos salvos localmente:")
print(f"  - Parquet: {parquet_file}")
print(f"  - CSV: {csv_file}")

# 5. Upload para Azure (se configurado)
if AZURE_STORAGE_ACCOUNT and AZURE_STORAGE_KEY:
    print(f"\n[5] Enviando para Azure Data Lake...")

    try:
        from azure.storage.filedatalake import DataLakeServiceClient

        service_client = DataLakeServiceClient(
            account_url=f"https://{AZURE_STORAGE_ACCOUNT}.dfs.core.windows.net",
            credential=AZURE_STORAGE_KEY
        )

        file_system_client = service_client.get_file_system_client(AZURE_CONTAINER)

        # Caminho no Data Lake
        blob_path = f"raw/estoque/empresa{CODEMP}/estoque_empresa{CODEMP}.parquet"

        # Upload
        file_client = file_system_client.get_file_client(blob_path)

        with open(parquet_file, "rb") as f:
            file_client.upload_data(f, overwrite=True)

        print(f"[OK] Enviado para: {AZURE_CONTAINER}/{blob_path}")

    except ImportError:
        print("[AVISO] azure-storage-file-datalake nao instalado. Pulando upload.")
    except Exception as e:
        print(f"[ERRO] Falha no upload: {e}")
else:
    print("\n[5] Azure nao configurado. Pulando upload.")

# Preview
print("\n" + "=" * 80)
print("PREVIEW DOS DADOS (primeiros 10 registros)")
print("=" * 80)
print(df.head(10).to_string(index=False))

print("\n" + "=" * 80)
print("CONCLUIDO!")
print("=" * 80)
