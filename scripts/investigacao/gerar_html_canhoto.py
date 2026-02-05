# -*- coding: utf-8 -*-
"""
Gera relatorio HTML de Recebimento de Canhotos com Status WMS
"""

import os
import json
import pandas as pd
from datetime import datetime

# Carregar dados
json_file = os.path.join(os.path.dirname(__file__), '..', '..', 'output', 'canhoto', 'recebimento_canhoto.json')

print("=" * 80)
print("GERANDO RELATORIO HTML - RECEBIMENTO DE CANHOTOS")
print("=" * 80)

if not os.path.exists(json_file):
    print(f"[ERRO] Arquivo {json_file} nao encontrado!")
    print("Execute primeiro: python extrair_canhoto.py")
    exit(1)

with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

fields = data.get("fieldsMetadata", [])
rows = data.get("rows", [])

print(f"[OK] Carregados {len(rows)} registros")

# Converter para DataFrame
field_names = [f["name"] for f in fields]
df = pd.DataFrame(rows, columns=field_names)

# Estatisticas
total = len(df)
empresas = df['Cod_Empresa'].nunique() if 'Cod_Empresa' in df.columns else 0

# Por empresa
por_empresa = df.groupby(['Cod_Empresa', 'Nome_Fantasia_Empresa']).size().reset_index(name='Qtd')

# Por status WMS
if 'Status_WMS' in df.columns:
    por_status = df.groupby('Status_WMS').size().reset_index(name='Qtd')
else:
    por_status = pd.DataFrame()

# Gerar HTML
html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recebimento de Canhotos - MMarra</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #f0f2f5; }}

        .header {{
            background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
            color: white;
            padding: 25px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}
        .header h1 {{ font-size: 2em; margin-bottom: 5px; }}
        .header p {{ opacity: 0.9; }}

        .stats {{
            display: flex;
            justify-content: center;
            gap: 15px;
            padding: 25px;
            flex-wrap: wrap;
        }}
        .stat-card {{
            background: white;
            padding: 15px 25px;
            border-radius: 12px;
            box-shadow: 0 2px 15px rgba(0,0,0,0.08);
            text-align: center;
            min-width: 140px;
        }}
        .stat-card.total {{ border-top: 4px solid #2c5282; }}
        .stat-card.armazenado {{ border-top: 4px solid #22c55e; }}
        .stat-card.conferido {{ border-top: 4px solid #3b82f6; }}
        .stat-card.pendente {{ border-top: 4px solid #f59e0b; }}
        .stat-card.sem-wms {{ border-top: 4px solid #ef4444; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #1e3a5f; }}
        .stat-label {{ color: #666; font-size: 0.85em; margin-top: 5px; }}

        .controls {{
            padding: 20px 25px;
            background: white;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
            margin: 0 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .controls input, .controls select {{
            padding: 12px 18px;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            font-size: 1em;
            transition: border-color 0.2s;
        }}
        .controls input {{ flex: 1; min-width: 200px; }}
        .controls input:focus, .controls select:focus {{
            outline: none;
            border-color: #2c5282;
        }}
        .controls button {{
            padding: 12px 25px;
            background: #2c5282;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 500;
            transition: background 0.2s;
        }}
        .controls button:hover {{ background: #1e3a5f; }}

        .table-container {{
            overflow-x: auto;
            padding: 20px;
            margin-top: 10px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            font-size: 0.85em;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 15px rgba(0,0,0,0.08);
        }}
        th {{
            background: #1e3a5f;
            color: white;
            padding: 14px 10px;
            text-align: left;
            position: sticky;
            top: 0;
            cursor: pointer;
            font-weight: 500;
        }}
        th:hover {{ background: #2c5282; }}
        td {{
            padding: 12px 10px;
            border-bottom: 1px solid #e2e8f0;
        }}
        tr:hover {{ background: #f7fafc; }}

        /* Badges de status */
        .status-badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
        }}
        .status-armazenado {{ background: #dcfce7; color: #166534; }}
        .status-conferido {{ background: #dbeafe; color: #1e40af; }}
        .status-em-conferencia {{ background: #e0f2fe; color: #0369a1; }}
        .status-em-recebimento {{ background: #fef3c7; color: #92400e; }}
        .status-pendente {{ background: #ffedd5; color: #c2410c; }}
        .status-sem-wms {{ background: #fee2e2; color: #991b1b; }}

        .empresa-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 500;
        }}
        .empresa-1 {{ background: #dbeafe; color: #1e40af; }}
        .empresa-4 {{ background: #dcfce7; color: #166534; }}
        .empresa-7 {{ background: #fef3c7; color: #92400e; }}

        .footer {{
            text-align: center;
            padding: 25px;
            color: #666;
            font-size: 0.9em;
        }}

        @media print {{
            .controls {{ display: none; }}
            .header {{ padding: 15px; }}
            table {{ font-size: 0.75em; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Recebimento de Canhotos</h1>
        <p>Com Status WMS (Entrada / Conferencia / Armazenagem)</p>
        <p>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    </div>

    <div class="stats">
        <div class="stat-card total">
            <div class="stat-number">{total}</div>
            <div class="stat-label">Total Canhotos</div>
        </div>
"""

# Adicionar cards por status WMS
if not por_status.empty:
    status_colors = {
        'Armazenado': 'armazenado',
        'Conferido': 'conferido',
        'Em Conferencia': 'conferido',
        'Em Recebimento': 'pendente',
        'Pendente': 'pendente',
        'Sem WMS': 'sem-wms'
    }
    for _, row in por_status.iterrows():
        status = row['Status_WMS']
        qtd = int(row['Qtd'])
        css_class = status_colors.get(status, 'total')
        html += f"""        <div class="stat-card {css_class}">
            <div class="stat-number">{qtd}</div>
            <div class="stat-label">{status}</div>
        </div>
"""

html += """    </div>

    <div class="controls">
        <input type="text" id="search" placeholder="Buscar (nota, cliente, vendedor...)">
        <select id="filterStatus" onchange="filterTable()">
            <option value="">Todos Status WMS</option>
            <option value="Armazenado">Armazenado</option>
            <option value="Conferido">Conferido</option>
            <option value="Em Recebimento">Em Recebimento</option>
            <option value="Pendente">Pendente</option>
            <option value="Sem WMS">Sem WMS</option>
        </select>
        <select id="filterEmpresa" onchange="filterTable()">
            <option value="">Todas Empresas</option>
"""

for _, row in por_empresa.iterrows():
    html += f'            <option value="{int(row["Cod_Empresa"])}">{row["Nome_Fantasia_Empresa"]}</option>\n'

html += """        </select>
        <button onclick="exportCSV()">Exportar CSV</button>
        <button onclick="window.print()">Imprimir</button>
    </div>

    <div class="table-container">
        <table id="dataTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">Seq</th>
                    <th onclick="sortTable(1)">NF</th>
                    <th onclick="sortTable(2)">Data Receb.</th>
                    <th onclick="sortTable(3)">Empresa</th>
                    <th onclick="sortTable(4)">Cliente</th>
                    <th onclick="sortTable(5)">Vendedor</th>
                    <th onclick="sortTable(6)">Valor</th>
                    <th onclick="sortTable(7)">Status WMS</th>
                    <th onclick="sortTable(8)">Conf. Final</th>
                    <th onclick="sortTable(9)">Usuario</th>
                </tr>
            </thead>
            <tbody>
"""

# Linhas da tabela
for _, row in df.iterrows():
    seq = row.get('Seq_Recebimento_Canhoto', '')
    nf = row.get('Nro_Nota_Fiscal', '')
    dt_rec = str(row.get('Data_Recebimento', ''))[:10] if row.get('Data_Recebimento') else ''
    emp = int(row.get('Cod_Empresa', 0)) if pd.notna(row.get('Cod_Empresa')) else 0
    emp_nome = str(row.get('Nome_Fantasia_Empresa', ''))[:20] if row.get('Nome_Fantasia_Empresa') else ''
    cliente = str(row.get('Nome_Parceiro', ''))[:35] if row.get('Nome_Parceiro') else ''
    vendedor = row.get('Vendedor', '') or ''
    valor = row.get('Valor_Nota', 0) or 0
    status_wms = row.get('Status_WMS', 'Sem WMS') or 'Sem WMS'
    conf_final = row.get('Conferencia_Final', '') or ''
    usuario = row.get('Nome_Usuario', '') or ''

    # CSS classes
    emp_class = f"empresa-{emp}" if emp in [1, 4, 7] else ""

    status_class_map = {
        'Armazenado': 'status-armazenado',
        'Conferido': 'status-conferido',
        'Em Conferencia': 'status-em-conferencia',
        'Em Recebimento': 'status-em-recebimento',
        'Pendente': 'status-pendente',
        'Sem WMS': 'status-sem-wms'
    }
    status_class = status_class_map.get(status_wms, 'status-sem-wms')

    html += f"""                <tr data-empresa="{emp}" data-status="{status_wms}">
                    <td>{seq}</td>
                    <td><strong>{nf}</strong></td>
                    <td>{dt_rec}</td>
                    <td><span class="empresa-badge {emp_class}">{emp_nome}</span></td>
                    <td>{cliente}</td>
                    <td>{vendedor}</td>
                    <td style="text-align:right">R$ {valor:,.2f}</td>
                    <td><span class="status-badge {status_class}">{status_wms}</span></td>
                    <td style="text-align:center">{conf_final}</td>
                    <td>{usuario}</td>
                </tr>
"""

html += """            </tbody>
        </table>
    </div>

    <div class="footer">
        MMarra Data Hub v0.7.0 | Recebimento de Canhotos com Status WMS | """ + str(total) + """ registros<br>
        Tabelas: AD_RECEBCANH + TGWREC | Gerado via API Sankhya
    </div>

    <script>
        document.getElementById('search').addEventListener('input', filterTable);

        function filterTable() {
            const searchFilter = document.getElementById('search').value.toLowerCase();
            const statusFilter = document.getElementById('filterStatus').value;
            const empresaFilter = document.getElementById('filterEmpresa').value;
            const rows = document.querySelectorAll('#dataTable tbody tr');

            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                const status = row.dataset.status;
                const empresa = row.dataset.empresa;

                const matchSearch = text.includes(searchFilter);
                const matchStatus = !statusFilter || status === statusFilter;
                const matchEmpresa = !empresaFilter || empresa === empresaFilter;

                row.style.display = (matchSearch && matchStatus && matchEmpresa) ? '' : 'none';
            });
        }

        let sortDirection = {};
        function sortTable(colIndex) {
            const table = document.getElementById('dataTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            sortDirection[colIndex] = !sortDirection[colIndex];
            const asc = sortDirection[colIndex];

            rows.sort((a, b) => {
                let aVal = a.cells[colIndex].textContent.trim();
                let bVal = b.cells[colIndex].textContent.trim();

                const aNum = parseFloat(aVal.replace(/[R$,.]/g, ''));
                const bNum = parseFloat(bVal.replace(/[R$,.]/g, ''));

                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return asc ? aNum - bNum : bNum - aNum;
                }

                return asc ? aVal.localeCompare(bVal, 'pt-BR') : bVal.localeCompare(aVal, 'pt-BR');
            });

            rows.forEach(row => tbody.appendChild(row));
        }

        function exportCSV() {
            const table = document.getElementById('dataTable');
            const rows = table.querySelectorAll('tr');
            let csv = [];

            rows.forEach(row => {
                if (row.style.display !== 'none') {
                    const cols = row.querySelectorAll('th, td');
                    const rowData = Array.from(cols).map(col => '"' + col.textContent.replace(/"/g, '""').trim() + '"');
                    csv.push(rowData.join(','));
                }
            });

            const blob = new Blob([csv.join('\\n')], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'recebimento_canhotos.csv';
            link.click();
        }
    </script>
</body>
</html>
"""

# Salvar
output_file = os.path.join(os.path.dirname(__file__), '..', '..', 'output', 'html', 'relatorio_recebimento_canhoto.html')
os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n[OK] Relatorio salvo em: {output_file}")
print(f"\nEstatisticas:")
print(f"  - Total: {total}")
print(f"  - Empresas: {empresas}")
if not por_status.empty:
    print(f"\n  Status WMS:")
    for _, row in por_status.iterrows():
        print(f"    - {row['Status_WMS']}: {int(row['Qtd'])}")

print("\n" + "=" * 80)
print("CONCLUIDO!")
print("=" * 80)
