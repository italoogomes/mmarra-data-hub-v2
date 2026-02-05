# -*- coding: utf-8 -*-
"""
Gera relatorio HTML com a query V2 (com deteccao de inconsistencia)
"""

import os
import json
from datetime import datetime

# Carregar resultado
json_file = os.path.join(os.path.dirname(__file__), '..', '..', 'output', 'json', 'resultado_empenho_v2.json')

print("=" * 80)
print("GERANDO RELATORIO HTML V2")
print("=" * 80)

if not os.path.exists(json_file):
    print(f"[ERRO] Arquivo {json_file} nao encontrado!")
    print("Execute primeiro: python testar_query_v2.py")
    exit(1)

with open(json_file, 'r', encoding='utf-8') as f:
    result = json.load(f)

response_body = result.get("responseBody", {})
fields = response_body.get("fieldsMetadata", [])
rows = response_body.get("rows", [])

print(f"[OK] Carregados {len(rows)} registros")

# Preparar dados
field_names = [f["name"] for f in fields]

# Contar estatisticas
total = len(rows)
inconsistencias = 0
empenhados = 0
nao_empenhados = 0
parciais = 0

status_idx = field_names.index("STATUS_EMPENHO_ITEM") if "STATUS_EMPENHO_ITEM" in field_names else None

for row in rows:
    if status_idx is not None:
        status = str(row[status_idx] or "").lower()
        if "inconsistencia" in status:
            inconsistencias += 1
        elif "nao empenhado" in status:
            nao_empenhados += 1
        elif "parcial" in status:
            parciais += 1
        elif "total" in status:
            empenhados += 1

# Gerar HTML
html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestao de Empenho com Cotacao V2</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background: #f5f5f5; }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{ font-size: 1.8em; margin-bottom: 10px; }}

        .stats {{
            display: flex;
            justify-content: center;
            gap: 20px;
            padding: 20px;
            flex-wrap: wrap;
        }}
        .stat-card {{
            background: white;
            padding: 15px 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            min-width: 150px;
        }}
        .stat-card.warning {{ border-left: 4px solid #FFB347; }}
        .stat-card.danger {{ border-left: 4px solid #F8D7DA; }}
        .stat-card.success {{ border-left: 4px solid #D1E7DD; }}
        .stat-card.partial {{ border-left: 4px solid #FFF3CD; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #333; }}
        .stat-label {{ color: #666; font-size: 0.9em; }}

        .controls {{
            padding: 15px 20px;
            background: white;
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
            border-bottom: 1px solid #ddd;
        }}
        .controls input {{
            padding: 10px 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 1em;
            flex: 1;
            min-width: 200px;
        }}
        .controls button {{
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }}
        .controls button:hover {{ background: #5a6fd6; }}

        .table-container {{
            overflow-x: auto;
            padding: 20px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            font-size: 0.85em;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 12px 8px;
            text-align: left;
            position: sticky;
            top: 0;
            cursor: pointer;
        }}
        th:hover {{ background: #5a6fd6; }}
        td {{
            padding: 10px 8px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{ background: #f8f9fa; }}

        /* Cores por status */
        .inconsistencia {{ background-color: #FFB347 !important; font-weight: bold; }}
        .nao-empenhado {{ background-color: #F8D7DA !important; }}
        .empenhado-parcial {{ background-color: #FFF3CD !important; }}
        .empenhado-total {{ background-color: #D1E7DD !important; }}
        .concluido {{ background-color: #CFE2D6 !important; }}

        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}

        @media print {{
            .controls {{ display: none; }}
            .header {{ padding: 10px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Gestao de Empenho com Cotacao V2</h1>
        <p>Com Deteccao de Inconsistencia</p>
        <p>Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
    </div>

    <div class="stats">
        <div class="stat-card">
            <div class="stat-number">{total:,}</div>
            <div class="stat-label">Total de Registros</div>
        </div>
        <div class="stat-card warning">
            <div class="stat-number">{inconsistencias:,}</div>
            <div class="stat-label">Inconsistencias</div>
        </div>
        <div class="stat-card danger">
            <div class="stat-number">{nao_empenhados:,}</div>
            <div class="stat-label">Nao Empenhados</div>
        </div>
        <div class="stat-card partial">
            <div class="stat-number">{parciais:,}</div>
            <div class="stat-label">Parciais</div>
        </div>
        <div class="stat-card success">
            <div class="stat-number">{empenhados:,}</div>
            <div class="stat-label">Empenhados Total</div>
        </div>
    </div>

    <div class="controls">
        <input type="text" id="search" placeholder="Buscar (pedido, produto, cliente...)">
        <button onclick="exportCSV()">Exportar CSV</button>
        <button onclick="window.print()">Imprimir</button>
    </div>

    <div class="table-container">
        <table id="dataTable">
            <thead>
                <tr>
"""

# Cabecalho
for name in field_names:
    if name not in ['BKCOLOR', 'FGCOLOR']:
        html += f'                    <th onclick="sortTable(this)">{name}</th>\n'

html += """                </tr>
            </thead>
            <tbody>
"""

# Linhas
bkcolor_idx = field_names.index("BKCOLOR") if "BKCOLOR" in field_names else None
status_empenho_idx = field_names.index("STATUS_EMPENHO_ITEM") if "STATUS_EMPENHO_ITEM" in field_names else None

for row in rows:
    # Determinar classe CSS
    css_class = ""
    if status_empenho_idx is not None:
        status = str(row[status_empenho_idx] or "").lower()
        if "inconsistencia" in status:
            css_class = "inconsistencia"
        elif "nao empenhado" in status:
            css_class = "nao-empenhado"
        elif "parcial" in status:
            css_class = "empenhado-parcial"
        elif "total" in status:
            css_class = "empenhado-total"

    html += f'                <tr class="{css_class}">\n'
    for i, val in enumerate(row):
        if field_names[i] not in ['BKCOLOR', 'FGCOLOR']:
            display_val = str(val) if val is not None else ""
            # Truncar valores muito longos
            if len(display_val) > 50:
                display_val = display_val[:47] + "..."
            html += f'                    <td>{display_val}</td>\n'
    html += '                </tr>\n'

html += """            </tbody>
        </table>
    </div>

    <div class="footer">
        MMarra Data Hub v0.6.0 | Gestao de Empenho com Cotacao V2 | {total} registros<br>
        Gerado automaticamente via API Sankhya | OAuth 2.0
    </div>

    <script>
        // Busca
        document.getElementById('search').addEventListener('input', function() {{
            const filter = this.value.toLowerCase();
            const rows = document.querySelectorAll('#dataTable tbody tr');
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            }});
        }});

        // Ordenacao
        function sortTable(th) {{
            const table = th.closest('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const idx = Array.from(th.parentNode.children).indexOf(th);
            const asc = th.dataset.sort !== 'asc';

            rows.sort((a, b) => {{
                const aVal = a.children[idx].textContent;
                const bVal = b.children[idx].textContent;
                return asc ? aVal.localeCompare(bVal, 'pt-BR', {{numeric: true}}) : bVal.localeCompare(aVal, 'pt-BR', {{numeric: true}});
            }});

            th.dataset.sort = asc ? 'asc' : 'desc';
            rows.forEach(row => tbody.appendChild(row));
        }}

        // Exportar CSV
        function exportCSV() {{
            const table = document.getElementById('dataTable');
            const rows = table.querySelectorAll('tr');
            let csv = [];

            rows.forEach(row => {{
                const cols = row.querySelectorAll('th, td');
                const rowData = Array.from(cols).map(col => '"' + col.textContent.replace(/"/g, '""') + '"');
                csv.push(rowData.join(','));
            }});

            const blob = new Blob([csv.join('\\n')], {{ type: 'text/csv;charset=utf-8;' }});
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'empenho_cotacao_v2.csv';
            link.click();
        }}
    </script>
</body>
</html>
""".format(total=total)

# Salvar
output_file = os.path.join(os.path.dirname(__file__), '..', '..', 'output', 'html', 'relatorio_empenho_cotacao_v2.html')
os.makedirs(os.path.dirname(output_file), exist_ok=True)

with open(output_file, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n[OK] Relatorio salvo em: {output_file}")
print(f"\nEstatisticas:")
print(f"  - Total: {total}")
print(f"  - Inconsistencias: {inconsistencias}")
print(f"  - Nao empenhados: {nao_empenhados}")
print(f"  - Parciais: {parciais}")
print(f"  - Empenhados total: {empenhados}")
