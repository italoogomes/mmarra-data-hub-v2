#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 Conversor de JSON Sankhya para HTML
=======================================
Versão: 1.0
Data: 2026-01-30

DESCRIÇÃO:
    Converte o JSON retornado pela API Sankhya (query de divergências)
    para o formato HTML interativo.

USO:
    1. Execute a query no Postman e salve o resultado em 'resultado_query.json'
    2. Execute este script: python converter_json_para_html.py
    3. Abra o arquivo 'relatorio_divergencias_atualizado.html' no navegador

REQUISITOS:
    - Python 3.7+
    - Arquivo 'resultado_query.json' no mesmo diretório
"""

import json
import os
from datetime import datetime

def converter_json_sankhya_para_dados(json_path):
    """
    Converte JSON da API Sankhya para formato do relatório HTML.

    Args:
        json_path (str): Caminho do arquivo JSON

    Returns:
        list: Lista de dicionários com dados formatados
    """
    print(f"📂 Lendo arquivo: {json_path}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extrair dados do response body (estrutura Sankhya)
    if 'responseBody' in data and 'rows' in data['responseBody']:
        rows = data['responseBody']['rows']
    elif isinstance(data, list):
        rows = data
    else:
        raise ValueError("Formato JSON não reconhecido. Verifique se é o response da API Sankhya.")

    print(f"✅ {len(rows)} registros encontrados")

    # Converter para formato do HTML
    dados_formatados = []

    for row in rows:
        # Sankhya retorna em formato de array ou objeto
        if isinstance(row, dict):
            dados_formatados.append({
                'codemp': row.get('CODEMP', 7),
                'codprod': row.get('CODPROD', 0),
                'descrprod': row.get('DESCRPROD', ''),
                'referencia': row.get('REFERENCIA', ''),
                'nunota': row.get('NUNOTA', 0),
                'numnota': row.get('NUMNOTA', 0),
                'top': row.get('TOP', 0),
                'descr_top': row.get('DESCR_TOP', ''),
                'qtd_nota': row.get('QTD_NOTA', 0),
                'status_item': row.get('STATUS_ITEM', ''),
                'status_cab': row.get('STATUS_CAB', ''),
                'qtd_disponivel_tgfest': row.get('QTD_DISPONIVEL_TGFEST', 0),
                'qtd_wms': row.get('QTD_WMS', 0),
                'divergencia': row.get('DIVERGENCIA', 0),
                'data_nota': row.get('DATA_NOTA', '')
            })
        elif isinstance(row, list):
            # Se vier como array, assumir ordem da query (COM CODEMP na primeira posição)
            dados_formatados.append({
                'codemp': row[0] if len(row) > 0 else 7,
                'codprod': row[1] if len(row) > 1 else 0,
                'descrprod': row[2] if len(row) > 2 else '',
                'referencia': row[3] if len(row) > 3 else '',
                'nunota': row[4] if len(row) > 4 else 0,
                'numnota': row[5] if len(row) > 5 else 0,
                'top': row[6] if len(row) > 6 else 0,
                'descr_top': row[7] if len(row) > 7 else '',
                'qtd_nota': row[8] if len(row) > 8 else 0,
                'status_item': row[9] if len(row) > 9 else '',
                'status_cab': row[10] if len(row) > 10 else '',
                'qtd_disponivel_tgfest': row[11] if len(row) > 11 else 0,
                'qtd_wms': row[12] if len(row) > 12 else 0,
                'divergencia': row[13] if len(row) > 13 else 0,
                'data_nota': row[14] if len(row) > 14 else ''
            })

    return dados_formatados


def atualizar_html(dados, html_template='relatorio_divergencias.html',
                   html_output='relatorio_divergencias_atualizado.html'):
    """
    Atualiza o HTML com os dados reais da query.

    Args:
        dados (list): Lista de dicionários com dados
        html_template (str): Arquivo HTML template
        html_output (str): Arquivo HTML de saída
    """
    print(f"📝 Lendo template HTML: {html_template}")

    with open(html_template, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Converter dados para JavaScript
    dados_js = json.dumps(dados, ensure_ascii=False, indent=12)

    # Substituir o array de dados de exemplo
    # Procurar por "let tableData = [" até "];"
    import re

    pattern = r'let tableData = \[[\s\S]*?\];'
    replacement = f'let tableData = {dados_js};'

    html_atualizado = re.sub(pattern, replacement, html_content)

    # Atualizar título do footer
    html_atualizado = html_atualizado.replace(
        'Versão 2.0 | Query corrigida (sem duplicatas)',
        f'Versão 2.0 | Atualizado em {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'
    )

    # Salvar HTML atualizado
    with open(html_output, 'w', encoding='utf-8') as f:
        f.write(html_atualizado)

    print(f"✅ HTML atualizado salvo em: {html_output}")
    print(f"📊 Total de registros: {len(dados)}")

    # Estatísticas
    produtos_unicos = len(set(d['codprod'] for d in dados))
    notas_unicas = len(set(d['nunota'] for d in dados))
    divergencia_total = sum(d['divergencia'] for d in dados)
    maior_divergencia = max(d['divergencia'] for d in dados) if dados else 0

    print(f"\n📈 Estatísticas:")
    print(f"   - Produtos únicos: {produtos_unicos}")
    print(f"   - Notas únicas: {notas_unicas}")
    print(f"   - Divergência total: {divergencia_total:,} unidades")
    print(f"   - Maior divergência: {maior_divergencia:,} unidades")


def main():
    """Função principal."""
    print("="*60)
    print("📊 CONVERSOR JSON → HTML - Divergências de Estoque")
    print("="*60)
    print()

    # Verificar se arquivo JSON existe
    json_file = 'resultado_query.json'

    if not os.path.exists(json_file):
        print(f"❌ Erro: Arquivo '{json_file}' não encontrado!")
        print()
        print("📝 INSTRUÇÕES:")
        print("   1. Execute a query no Postman (curl_divergencias_corrigida.txt)")
        print("   2. Salve o resultado completo em 'resultado_query.json'")
        print("   3. Execute este script novamente")
        print()
        return

    try:
        # Converter JSON para dados formatados
        dados = converter_json_sankhya_para_dados(json_file)

        # Atualizar HTML
        atualizar_html(dados)

        print()
        print("="*60)
        print("✅ CONVERSÃO CONCLUÍDA COM SUCESSO!")
        print("="*60)
        print()
        print("🌐 Abra o arquivo 'relatorio_divergencias_atualizado.html' no navegador")
        print()

    except Exception as e:
        print(f"❌ Erro durante conversão: {str(e)}")
        print()
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
