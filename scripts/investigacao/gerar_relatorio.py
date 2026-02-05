#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 Gerador Rápido de Relatório HTML
====================================
Lê o JSON colado e gera HTML instantaneamente
"""

import json
import re
from datetime import datetime

print("="*70)
print("📊 GERADOR DE RELATÓRIO HTML - Divergências de Estoque")
print("="*70)
print()
print("📋 INSTRUÇÕES:")
print("   1. Cole o JSON completo do Postman aqui (pode ser grande)")
print("   2. Após colar, pressione Enter")
print("   3. Digite 'FIM' e pressione Enter novamente")
print()
print("="*70)
print("👇 Cole o JSON abaixo:")
print()

# Ler todas as linhas até encontrar 'FIM'
linhas = []
while True:
    try:
        linha = input()
        if linha.strip().upper() == 'FIM':
            break
        linhas.append(linha)
    except EOFError:
        break

json_text = '\n'.join(linhas)

if not json_text.strip():
    print("❌ Nenhum dado foi colado!")
    exit(1)

print()
print("⏳ Processando JSON...")

try:
    data = json.loads(json_text)

    # Extrair rows
    if 'responseBody' in data and 'rows' in data['responseBody']:
        rows = data['responseBody']['rows']
    elif isinstance(data, list):
        rows = data
    else:
        print("❌ Formato JSON não reconhecido")
        exit(1)

    print(f"✅ {len(rows)} registros encontrados")

    # Verificar se tem CODEMP (primeira coluna)
    # Se a query antiga foi usada, não terá CODEMP
    primeiro_row = rows[0] if rows else []
    tem_codemp = len(primeiro_row) == 15  # 15 campos com CODEMP, 14 sem

    if not tem_codemp:
        print("⚠️  ATENÇÃO: JSON parece ser da query antiga (sem CODEMP)")
        print("   Adicionando CODEMP=7 automaticamente...")

    # Converter dados
    dados = []
    for row in rows:
        if tem_codemp:
            # Ordem: CODEMP, CODPROD, DESCRPROD, REFERENCIA, NUNOTA, NUMNOTA, TOP, DESCR_TOP,
            #        QTD_NOTA, STATUS_ITEM, STATUS_CAB, QTD_DISPONIVEL_TGFEST, QTD_WMS,
            #        DIVERGENCIA, DATA_NOTA
            dados.append({
                'codemp': row[0],
                'codprod': row[1],
                'descrprod': row[2],
                'referencia': row[3],
                'nunota': row[4],
                'numnota': row[5],
                'top': row[6],
                'descr_top': row[7],
                'qtd_nota': row[8],
                'status_item': row[9],
                'status_cab': row[10],
                'qtd_disponivel_tgfest': row[11],
                'qtd_wms': row[12],
                'divergencia': row[13],
                'data_nota': row[14]
            })
        else:
            # Query antiga sem CODEMP
            # Ordem: CODPROD, DESCRPROD, REFERENCIA, NUNOTA, NUMNOTA, TOP, DESCR_TOP,
            #        QTD_NOTA, STATUS_ITEM, STATUS_CAB, QTD_DISPONIVEL_TGFEST, QTD_WMS,
            #        DIVERGENCIA, DATA_NOTA
            dados.append({
                'codemp': 7,  # Padrão
                'codprod': row[0],
                'descrprod': row[1],
                'referencia': row[2],
                'nunota': row[3],
                'numnota': row[4],
                'top': row[5],
                'descr_top': row[6],
                'qtd_nota': row[7],
                'status_item': row[8],
                'status_cab': row[9],
                'qtd_disponivel_tgfest': row[10],
                'qtd_wms': row[11],
                'divergencia': row[12],
                'data_nota': row[13]
            })

    # Estatísticas
    produtos_unicos = len(set(d['codprod'] for d in dados))
    notas_unicas = len(set(d['nunota'] for d in dados))
    divergencia_total = sum(d['divergencia'] for d in dados)
    maior_divergencia = max(d['divergencia'] for d in dados) if dados else 0

    print()
    print("📊 ESTATÍSTICAS:")
    print(f"   • Total de registros: {len(dados)}")
    print(f"   • Produtos únicos: {produtos_unicos}")
    print(f"   • Notas únicas: {notas_unicas}")
    print(f"   • Divergência total: {divergencia_total:,} unidades")
    print(f"   • Maior divergência: {maior_divergencia:,} unidades")
    print()

    # Ler template HTML
    print("📄 Gerando HTML...")
    with open('relatorio_divergencias.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # Substituir dados
    dados_js = json.dumps(dados, ensure_ascii=False, indent=12)
    html = re.sub(r'let tableData = \[[\s\S]*?\];', f'let tableData = {dados_js};', html)

    # Atualizar footer
    html = html.replace(
        'Versão 2.0 | Query corrigida (sem duplicatas)',
        f'Versão 2.0 | Gerado em {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}'
    )

    # Salvar
    output_file = 'relatorio_divergencias_completo.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Relatório gerado: {output_file}")
    print()
    print("="*70)
    print("🎉 SUCESSO!")
    print("="*70)
    print()
    print(f"🌐 Abra o arquivo: {output_file}")
    print()
    print("OU digite no terminal:")
    print(f"   start {output_file}")
    print()

except json.JSONDecodeError as e:
    print(f"❌ Erro ao decodificar JSON: {e}")
    print("   Verifique se colou o JSON completo e válido")
except Exception as e:
    print(f"❌ Erro: {e}")
    import traceback
    traceback.print_exc()
