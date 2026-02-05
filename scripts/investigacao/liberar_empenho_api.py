# -*- coding: utf-8 -*-
"""
Liberar empenhos do pedido cancelado 1183490 via API Sankhya
"""

import os
import json
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
        print(auth_response.text)
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


def executar_servico(access_token, service_name, payload):
    """Executa um servico generico da API Sankhya"""
    try:
        url = f"{BASE_URL}/gateway/v1/mge/service.sbr?serviceName={service_name}&outputType=json"
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=payload,
            timeout=60
        )
        print(f"\n[DEBUG] URL: {url}")
        print(f"[DEBUG] Status: {response.status_code}")
        print(f"[DEBUG] Response: {response.text[:500]}")
        return response.json() if response.status_code == 200 else None
    except Exception as e:
        print(f"[ERRO] {e}")
        return None


def buscar_empenhos():
    """Busca os empenhos do pedido cancelado"""
    access_token = autenticar()
    if not access_token:
        return None

    # Primeiro, buscar a estrutura da tabela
    query_estrutura = """
    SELECT COLUMN_NAME FROM ALL_TAB_COLUMNS
    WHERE TABLE_NAME = 'TGWEMPE'
    ORDER BY COLUMN_ID
    """
    print("[DEBUG] Buscando estrutura da TGWEMPE...")
    estrutura = executar_query(access_token, query_estrutura)
    if estrutura and estrutura.get("rows"):
        print("Colunas da TGWEMPE:")
        for row in estrutura["rows"]:
            print(f"  - {row[0]}")

    # Buscar chave primaria
    query_pk = """
    SELECT cols.column_name
    FROM all_constraints cons, all_cons_columns cols
    WHERE cons.constraint_type = 'P'
      AND cons.constraint_name = cols.constraint_name
      AND cons.owner = cols.owner
      AND cols.table_name = 'TGWEMPE'
    ORDER BY cols.position
    """
    print("\n[DEBUG] Buscando chave primaria...")
    pk = executar_query(access_token, query_pk)
    if pk and pk.get("rows"):
        print("Chave primaria da TGWEMPE:")
        for row in pk["rows"]:
            print(f"  - {row[0]}")

    query = f"""
    SELECT * FROM TGWEMPE
    WHERE NUNOTAPEDVEN = {PEDIDO_CANCELADO}
    """
    return executar_query(access_token, query), access_token


def tentar_remover_via_crud(access_token, empenho):
    """Tenta remover empenho via CRUDServiceProvider"""
    print(f"\n--- Tentando remover empenho do produto {empenho['CODPROD']} ---")

    # Formato padrao do Sankhya para remocao
    # Chave primaria da TGWEMPE: NUNOTA, CODPROD, CONTROLE
    payload = {
        "requestBody": {
            "dataSet": {
                "rootEntity": "TGWEMPE",
                "includePresentationFields": "N",
                "dataRow": {
                    "localFields": {
                        "NUNOTA": {"$": str(empenho['NUNOTA'])},
                        "CODPROD": {"$": str(empenho['CODPROD'])},
                        "CONTROLE": {"$": str(empenho.get('CONTROLE', ''))}
                    }
                }
            }
        }
    }

    result = executar_servico(access_token, "CRUDServiceProvider.removeRecord", payload)
    return result


def tentar_remover_via_datasetsp(access_token, empenho):
    """Tenta remover empenho via DataSetSP.removeRecord"""
    print(f"\n--- Tentando DataSetSP para produto {empenho['CODPROD']} ---")

    payload = {
        "requestBody": {
            "dataSet": {
                "rootEntity": "TGWEMPE",
                "dataRow": {
                    "primaryKey": {
                        "NUNOTA": empenho['NUNOTA'],
                        "CODPROD": empenho['CODPROD'],
                        "CONTROLE": empenho.get('CONTROLE', '')
                    }
                }
            }
        }
    }

    result = executar_servico(access_token, "DataSetSP.removeRecord", payload)
    return result


def tentar_servico_empenho(access_token):
    """Tenta usar servico especifico de empenho"""
    print("\n--- Buscando servicos de empenho disponiveis ---")
    # Nenhum servico especifico de empenho encontrado na API
    return None


def tentar_mgeservico_remover(access_token, empenho):
    """Tenta remover via MGECoreServiceSP ou servico similar"""
    print(f"\n--- Tentando MGE Remove para produto {empenho['CODPROD']} ---")

    # Formato XML-like que Sankhya usa internamente
    payload = {
        "requestBody": {
            "entity": {
                "$": "TGWEMPE"
            },
            "criteria": {
                "expression": {
                    "$": f"NUNOTA = {empenho['NUNOTA']} AND CODPROD = {empenho['CODPROD']} AND NUNOTAPEDVEN = {PEDIDO_CANCELADO}"
                }
            }
        }
    }

    result = executar_servico(access_token, "MGECoreServiceSP.deleteRecords", payload)
    if not result or result.get("status") != "1":
        # Tentar outro formato
        payload2 = {
            "requestBody": {
                "dataSet": {
                    "rootEntity": "TGWEMPE",
                    "criteria": {
                        "expression": {
                            "$": f"this.NUNOTA = {empenho['NUNOTA']} AND this.CODPROD = {empenho['CODPROD']}"
                        }
                    }
                }
            }
        }
        result = executar_servico(access_token, "CRUDServiceProvider.removeRecordByPK", payload2)
    return result


def tentar_saverecord_zerar(access_token, empenho):
    """Tenta zerar a quantidade do empenho via SaveRecord"""
    print(f"\n--- Tentando ZERAR empenho do produto {empenho['CODPROD']} ---")

    # Em vez de deletar, tentar atualizar para QTDEMPENHO = 0
    payload = {
        "requestBody": {
            "dataSet": {
                "rootEntity": "TGWEMPE",
                "includePresentationFields": "N",
                "dataRow": {
                    "localFields": {
                        "NUNOTA": {"$": str(empenho['NUNOTA'])},
                        "CODPROD": {"$": str(empenho['CODPROD'])},
                        "CONTROLE": {"$": str(empenho.get('CONTROLE', ''))},
                        "NUNOTAPEDVEN": {"$": str(empenho['NUNOTAPEDVEN'])},
                        "QTDEMPENHO": {"$": "0"}
                    }
                }
            }
        }
    }

    result = executar_servico(access_token, "CRUDServiceProvider.saveRecord", payload)
    return result


def tentar_desvincular_pedido(access_token, empenho):
    """Tenta desvincular empenho do pedido (setar NUNOTAPEDVEN = NULL)"""
    print(f"\n--- Tentando DESVINCULAR empenho do produto {empenho['CODPROD']} ---")

    # Tentar setar NUNOTAPEDVEN para null
    payload = {
        "requestBody": {
            "dataSet": {
                "rootEntity": "TGWEMPE",
                "includePresentationFields": "N",
                "dataRow": {
                    "localFields": {
                        "NUNOTA": {"$": str(empenho['NUNOTA'])},
                        "CODPROD": {"$": str(empenho['CODPROD'])},
                        "CONTROLE": {"$": str(empenho.get('CONTROLE', ''))},
                        "NUNOTAPEDVEN": {}  # Tentar setar como null
                    }
                }
            }
        }
    }

    result = executar_servico(access_token, "CRUDServiceProvider.saveRecord", payload)
    return result


def tentar_action_button(access_token, empenho):
    """Tenta usar ActionButtonSP para acionar botao de cancelar empenho"""
    print(f"\n--- Tentando ActionButtonSP para produto {empenho['CODPROD']} ---")

    # Formato para chamar acao de botao
    payload = {
        "requestBody": {
            "acao": {
                "nome": "cancelarEmpenho"
            },
            "parametros": {
                "NUNOTA": str(empenho['NUNOTA']),
                "CODPROD": str(empenho['CODPROD']),
                "NUNOTAPEDVEN": str(empenho['NUNOTAPEDVEN'])
            }
        }
    }

    result = executar_servico(access_token, "ActionButtonSP.executeJava", payload)
    return result


def tentar_removerecord_formato_v2(access_token, empenho):
    """Tenta removeRecord com formato alternativo (pk explicita)"""
    print(f"\n--- Tentando removeRecord formato V2 para produto {empenho['CODPROD']} ---")

    # Formato com pk explicita - chave primaria: NUNOTA, CODPROD, CONTROLE, NUNOTAPEDVEN
    controle = empenho.get('CONTROLE') or ''

    payload = {
        "requestBody": {
            "dataSet": {
                "rootEntity": "TGWEMPE",
                "includePresentationFields": "N",
                "dataRow": {
                    "key": {
                        "NUNOTA": str(empenho['NUNOTA']),
                        "CODPROD": str(empenho['CODPROD']),
                        "CONTROLE": controle,
                        "NUNOTAPEDVEN": str(empenho['NUNOTAPEDVEN'])
                    }
                }
            }
        }
    }

    result = executar_servico(access_token, "CRUDServiceProvider.removeRecord", payload)
    return result


def listar_servicos_disponiveis(access_token):
    """Lista servicos que contenham WMS ou EMPE no nome"""
    print("\n--- Listando servicos disponiveis relacionados a WMS/Empenho ---")

    # Tentar descobrir servicos via reflexao (pode nao funcionar)
    servicos_testar = [
        "WMSP.cancelarEmpenho",
        "WMSP.liberarEmpenho",
        "WMSEmpenhoSP.cancelar",
        "WMSEmpenhoSP.liberar",
        "WMSEmpenhoSP.remover",
        "WMSEmpenhoSP.desvincular",
        "EmpenhoSP.cancelar",
        "EmpenhoSP.liberar",
        "EmpenhoSP.remover",
        "CACSP.liberarEmpenho",
        "CACSP.removerEmpenho",
        "ServEmpenhoSP.cancelar",
        "ServEmpenhoSP.excluir",
    ]

    for servico in servicos_testar:
        payload = {"requestBody": {}}
        try:
            url = f"{BASE_URL}/gateway/v1/mge/service.sbr?serviceName={servico}&outputType=json"
            response = requests.post(
                url,
                headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
                json=payload,
                timeout=10
            )
            result = response.json()
            if "Nenhum provedor foi encontrado" not in result.get("statusMessage", ""):
                print(f"  [EXISTE!] {servico}: {result.get('statusMessage', '')[:50]}")
        except:
            pass


def main():
    print("=" * 80)
    print("LIBERAR EMPENHOS DO PEDIDO CANCELADO 1183490")
    print("=" * 80)

    # 1. Buscar empenhos atuais
    print("\n[1] Buscando empenhos do pedido cancelado...")
    result, access_token = buscar_empenhos()

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
    print(f"\n{'CODPROD':>10} | {'QTDEMP':>8} | {'COMPRA':>10} | {'CONTROLE':>10}")
    print("-" * 50)
    for emp in empenhos:
        print(f"{emp['CODPROD']:>10} | {emp['QTDEMPENHO']:>8} | {emp['NUNOTA']:>10} | {emp.get('CONTROLE', 'N/A'):>10}")

    # 2. Tentar metodos diferentes
    print("\n" + "=" * 80)
    print("[2] TENTANDO LIBERAR VIA API...")
    print("=" * 80)

    # Metodo 1: MGE Delete
    print("\n--- METODO 1: MGECoreServiceSP.deleteRecords ---")
    tentar_mgeservico_remover(access_token, empenhos[0])

    # Metodo 2: CRUD Remove
    print("\n--- METODO 2: CRUDServiceProvider.removeRecord ---")
    tentar_remover_via_crud(access_token, empenhos[0])

    # Metodo 3: Zerar quantidade (alternativa)
    print("\n--- METODO 3: CRUDServiceProvider.saveRecord (zerar qtd) ---")
    tentar_saverecord_zerar(access_token, empenhos[0])

    # Metodo 4: Desvincular pedido
    print("\n--- METODO 4: Desvincular (NUNOTAPEDVEN = NULL) ---")
    tentar_desvincular_pedido(access_token, empenhos[0])

    # Metodo 5: Action Button
    print("\n--- METODO 5: ActionButtonSP ---")
    tentar_action_button(access_token, empenhos[0])

    # Metodo 6: removeRecord formato V2
    print("\n--- METODO 6: removeRecord com PK explicita ---")
    tentar_removerecord_formato_v2(access_token, empenhos[0])

    # Metodo 7: Listar servicos disponiveis
    print("\n--- METODO 7: Buscar servicos WMS/Empenho ---")
    listar_servicos_disponiveis(access_token)

    # 3. Verificar se algum foi removido
    print("\n" + "=" * 80)
    print("[3] VERIFICANDO SE ALGUM FOI REMOVIDO...")
    print("=" * 80)

    result2, _ = buscar_empenhos()
    if result2 and result2.get("rows"):
        print(f"\nAinda existem {len(result2['rows'])} empenhos (nenhum foi removido)")
    else:
        print("\n[OK] Empenhos removidos com sucesso!")


if __name__ == "__main__":
    main()
