# -*- coding: utf-8 -*-
"""
Gerador de Relatorio de Pedidos de Compra Pendentes

Gera relatorio HTML profissional com graficos interativos usando Plotly.js.
Inclui filtros por empresa, fornecedor e periodo.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from datetime import datetime
from src.utils.sankhya_client import SankhyaClient
import json


def gerar_relatorio_pedidos_pendentes():
    """Gera relatorio HTML de pedidos de compra pendentes com graficos interativos."""

    client = SankhyaClient()

    # Query simplificada usando ITE.PENDENTE diretamente (mais performatico)
    query = """
    SELECT
        CAB.NUNOTA,
        CAB.NUMNOTA AS NRO_PEDIDO,
        CAB.CODEMP,
        EMP.NOMEFANTASIA AS EMPRESA,
        CAB.CODPARC,
        PAR.NOMEPARC AS FORNECEDOR,
        CAB.DTNEG,
        CAB.STATUSNOTA,
        TOP.DESCROPER AS TIPO_OPERACAO,
        ITE.SEQUENCIA,
        ITE.CODPROD,
        PRO.DESCRPROD,
        PRO.REFERENCIA,
        ITE.QTDNEG AS QTD_PEDIDO,
        NVL(ITE.QTDENTREGUE, 0) AS QTD_ENTREGUE,
        (ITE.QTDNEG - NVL(ITE.QTDENTREGUE, 0)) AS QTD_PENDENTE,
        ITE.VLRUNIT,
        (ITE.QTDNEG - NVL(ITE.QTDENTREGUE, 0)) * ITE.VLRUNIT AS VALOR_PENDENTE
    FROM TGFCAB CAB
    JOIN TGFITE ITE ON ITE.NUNOTA = CAB.NUNOTA
    LEFT JOIN TGFPAR PAR ON PAR.CODPARC = CAB.CODPARC
    LEFT JOIN TGFPRO PRO ON PRO.CODPROD = ITE.CODPROD
    LEFT JOIN TSIEMP EMP ON EMP.CODEMP = CAB.CODEMP
    LEFT JOIN (
        SELECT CODTIPOPER, DESCROPER,
               ROW_NUMBER() OVER (PARTITION BY CODTIPOPER ORDER BY DHALTER DESC) AS RN
        FROM TGFTOP
    ) TOP ON TOP.CODTIPOPER = CAB.CODTIPOPER AND TOP.RN = 1
    WHERE CAB.TIPMOV = 'O'
      AND ITE.PENDENTE = 'S'
      AND (ITE.QTDNEG - NVL(ITE.QTDENTREGUE, 0)) > 0
    ORDER BY CAB.DTNEG DESC
    """

    print("Buscando dados do Sankhya...")
    result = client.executar_query(query)
    rows = result.get('rows', [])
    fields = result.get('fieldsMetadata', [])
    columns = [f.get('name') for f in fields]

    df = pd.DataFrame(rows, columns=columns)
    print(f"Total de itens pendentes: {len(df)}")

    # Converter tipos
    numeric_cols = ['QTD_PEDIDO', 'QTD_ENTREGUE', 'QTD_PENDENTE', 'VLRUNIT', 'VALOR_PENDENTE', 'CODEMP']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    df['DTNEG_DT'] = pd.to_datetime(df['DTNEG'], format='%d%m%Y %H:%M:%S', errors='coerce')
    df['DATA_PEDIDO'] = df['DTNEG_DT'].dt.strftime('%d/%m/%Y')
    df['MES'] = df['DTNEG_DT'].dt.to_period('M').astype(str)

    # Nome da empresa
    df['EMPRESA'] = df['EMPRESA'].fillna('Empresa ' + df['CODEMP'].astype(int).astype(str))

    # Metricas gerais
    total_valor = df['VALOR_PENDENTE'].sum()
    total_pedidos = df['NUNOTA'].nunique()
    total_fornecedores = df['FORNECEDOR'].nunique()
    total_itens = len(df)
    total_produtos = df['CODPROD'].nunique()
    qtd_empresas = df['CODEMP'].nunique()

    # Dados para filtros (listas unicas)
    empresas = sorted(df['EMPRESA'].dropna().unique().tolist())
    fornecedores = sorted(df['FORNECEDOR'].dropna().unique().tolist())[:50]  # Top 50

    # Por empresa
    por_empresa = df.groupby(['CODEMP', 'EMPRESA']).agg({
        'NUNOTA': 'nunique',
        'VALOR_PENDENTE': 'sum',
        'CODPROD': 'nunique'
    }).reset_index().sort_values('VALOR_PENDENTE', ascending=False)

    # Por tipo de operacao
    por_tipo = df.groupby('TIPO_OPERACAO').agg({
        'NUNOTA': 'nunique',
        'VALOR_PENDENTE': 'sum'
    }).reset_index().sort_values('VALOR_PENDENTE', ascending=False)

    # Por fornecedor
    por_fornecedor = df.groupby('FORNECEDOR').agg({
        'NUNOTA': 'nunique',
        'VALOR_PENDENTE': 'sum',
        'CODPROD': 'nunique'
    }).reset_index().sort_values('VALOR_PENDENTE', ascending=False)

    # Por mes
    por_mes = df.groupby('MES').agg({
        'VALOR_PENDENTE': 'sum',
        'NUNOTA': 'nunique'
    }).reset_index().sort_values('MES')

    # Pedidos mais antigos
    antigos = df.sort_values('DTNEG_DT').drop_duplicates('NUNOTA')[
        ['NUNOTA', 'NRO_PEDIDO', 'FORNECEDOR', 'DTNEG_DT', 'DATA_PEDIDO', 'EMPRESA']
    ].head(20)
    # Valor total por pedido
    valor_por_pedido = df.groupby('NUNOTA')['VALOR_PENDENTE'].sum()
    antigos['VALOR_PEDIDO'] = antigos['NUNOTA'].map(valor_por_pedido)

    # Preparar dados para JSON (graficos interativos)
    dados_completos = df.to_dict('records')
    for item in dados_completos:
        if pd.isna(item.get('DTNEG_DT')):
            item['DTNEG_DT'] = None
        else:
            item['DTNEG_DT'] = item['DTNEG_DT'].isoformat()

    # Gerar HTML com Plotly.js
    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pedidos de Compra Pendentes - MMarra</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        :root {{
            --primary: #1565c0;
            --primary-dark: #0d47a1;
            --secondary: #ff6f00;
            --success: #2e7d32;
            --danger: #c62828;
            --warning: #f9a825;
            --light: #f8f9fa;
            --dark: #212529;
            --gray: #6c757d;
            --border: #dee2e6;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}

        /* Header */
        .header {{
            background: white;
            border-radius: 16px;
            padding: 24px 32px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.15);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 20px;
        }}

        .header-left h1 {{
            font-size: 26px;
            color: var(--dark);
            margin-bottom: 6px;
        }}

        .header-left .subtitle {{
            color: var(--gray);
            font-size: 13px;
        }}

        .header-right {{
            text-align: right;
        }}

        .header-right .total {{
            font-size: 32px;
            font-weight: 700;
            color: var(--primary);
        }}

        .header-right .total-label {{
            color: var(--gray);
            font-size: 13px;
        }}

        /* Filtros */
        .filters {{
            background: white;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            align-items: flex-end;
        }}

        .filter-group {{
            flex: 1;
            min-width: 200px;
        }}

        .filter-group label {{
            display: block;
            font-size: 12px;
            font-weight: 600;
            color: var(--gray);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }}

        .filter-group select,
        .filter-group input {{
            width: 100%;
            padding: 10px 14px;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.2s;
        }}

        .filter-group select:focus,
        .filter-group input:focus {{
            outline: none;
            border-color: var(--primary);
        }}

        .btn {{
            padding: 10px 24px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .btn-primary {{
            background: var(--primary);
            color: white;
        }}

        .btn-primary:hover {{
            background: var(--primary-dark);
        }}

        .btn-secondary {{
            background: var(--light);
            color: var(--dark);
        }}

        .btn-secondary:hover {{
            background: var(--border);
        }}

        /* Cards */
        .cards {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 16px;
            margin-bottom: 20px;
        }}

        .card {{
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        }}

        .card .icon {{
            width: 44px;
            height: 44px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 10px;
            font-size: 22px;
        }}

        .card .icon.blue {{ background: #e3f2fd; }}
        .card .icon.orange {{ background: #fff3e0; }}
        .card .icon.green {{ background: #e8f5e9; }}
        .card .icon.purple {{ background: #f3e5f5; }}
        .card .icon.red {{ background: #ffebee; }}

        .card .value {{
            font-size: 26px;
            font-weight: 700;
            color: var(--dark);
        }}

        .card .label {{
            color: var(--gray);
            font-size: 12px;
            margin-top: 4px;
        }}

        /* Graficos */
        .row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }}

        .section {{
            background: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        }}

        .section h2 {{
            font-size: 16px;
            color: var(--dark);
            margin-bottom: 16px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--light);
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .section h2::before {{
            content: '';
            width: 4px;
            height: 18px;
            background: var(--primary);
            border-radius: 2px;
        }}

        .chart-container {{
            height: 320px;
        }}

        /* Tabelas */
        .table-container {{
            max-height: 500px;
            overflow-y: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th, td {{
            padding: 12px 10px;
            text-align: left;
            border-bottom: 1px solid var(--border);
            font-size: 13px;
        }}

        th {{
            background: var(--light);
            color: var(--dark);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            position: sticky;
            top: 0;
            cursor: pointer;
        }}

        th:hover {{
            background: #e9ecef;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .valor {{
            text-align: right;
            font-family: 'Consolas', 'Monaco', monospace;
            font-weight: 600;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
        }}

        .badge-danger {{ background: #ffebee; color: var(--danger); }}
        .badge-warning {{ background: #fff8e1; color: #f57c00; }}
        .badge-success {{ background: #e8f5e9; color: var(--success); }}
        .badge-info {{ background: #e3f2fd; color: var(--primary); }}

        .search-box {{
            margin-bottom: 12px;
        }}

        .search-box input {{
            width: 100%;
            padding: 10px 14px;
            border: 2px solid var(--border);
            border-radius: 8px;
            font-size: 14px;
        }}

        .search-box input:focus {{
            outline: none;
            border-color: var(--primary);
        }}

        /* Alert */
        .alert {{
            background: linear-gradient(135deg, #ff6b6b, #ee5a5a);
            color: white;
            padding: 16px 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .alert-icon {{ font-size: 22px; }}

        /* Footer */
        .footer {{
            text-align: center;
            color: white;
            padding: 24px;
            font-size: 12px;
            opacity: 0.8;
        }}

        /* Responsive */
        @media (max-width: 1200px) {{
            .cards {{ grid-template-columns: repeat(3, 1fr); }}
            .row {{ grid-template-columns: 1fr; }}
        }}

        @media (max-width: 768px) {{
            .cards {{ grid-template-columns: repeat(2, 1fr); }}
            .header {{ flex-direction: column; text-align: center; }}
            .filters {{ flex-direction: column; }}
        }}

        /* Loading */
        .loading {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 9999;
            justify-content: center;
            align-items: center;
        }}

        .loading.active {{
            display: flex;
        }}

        .spinner {{
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        /* Info sobre filtros ativos */
        .filter-info {{
            background: var(--light);
            padding: 10px 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 13px;
            display: none;
        }}

        .filter-info.active {{
            display: block;
        }}

        .filter-tag {{
            display: inline-block;
            background: var(--primary);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            margin-right: 8px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="loading" id="loading">
        <div class="spinner"></div>
    </div>

    <div class="container">
        <div class="header">
            <div class="header-left">
                <h1>Pedidos de Compra Pendentes</h1>
                <div class="subtitle">Relatorio gerado em {datetime.now().strftime('%d/%m/%Y as %H:%M')} | Dados em tempo real do Sankhya</div>
            </div>
            <div class="header-right">
                <div class="total" id="totalValor">R$ {total_valor:,.2f}</div>
                <div class="total-label">Valor Total Pendente</div>
            </div>
        </div>

        <div class="filters">
            <div class="filter-group">
                <label>Empresa</label>
                <select id="filterEmpresa" onchange="aplicarFiltros()">
                    <option value="">Todas as Empresas</option>
                    {"".join([f'<option value="{e}">{e}</option>' for e in empresas])}
                </select>
            </div>
            <div class="filter-group">
                <label>Fornecedor</label>
                <select id="filterFornecedor" onchange="aplicarFiltros()">
                    <option value="">Todos os Fornecedores</option>
                    {"".join([f'<option value="{f}">{f[:40]}</option>' for f in fornecedores])}
                </select>
            </div>
            <div class="filter-group">
                <label>Periodo De</label>
                <input type="date" id="filterDataDe" onchange="aplicarFiltros()">
            </div>
            <div class="filter-group">
                <label>Periodo Ate</label>
                <input type="date" id="filterDataAte" onchange="aplicarFiltros()">
            </div>
            <div>
                <button class="btn btn-secondary" onclick="limparFiltros()">Limpar Filtros</button>
            </div>
        </div>

        <div class="filter-info" id="filterInfo">
            <strong>Filtros ativos:</strong> <span id="filterTags"></span>
        </div>

        <div class="cards">
            <div class="card">
                <div class="icon blue">📋</div>
                <div class="value" id="cardPedidos">{total_pedidos:,}</div>
                <div class="label">Pedidos</div>
            </div>
            <div class="card">
                <div class="icon orange">🏭</div>
                <div class="value" id="cardFornecedores">{total_fornecedores}</div>
                <div class="label">Fornecedores</div>
            </div>
            <div class="card">
                <div class="icon green">📦</div>
                <div class="value" id="cardItens">{total_itens:,}</div>
                <div class="label">Itens</div>
            </div>
            <div class="card">
                <div class="icon purple">🏷️</div>
                <div class="value" id="cardProdutos">{total_produtos:,}</div>
                <div class="label">Produtos</div>
            </div>
            <div class="card">
                <div class="icon red">🏢</div>
                <div class="value" id="cardEmpresas">{qtd_empresas}</div>
                <div class="label">Empresas</div>
            </div>
        </div>

        <div class="row">
            <div class="section">
                <h2>Valor Pendente por Empresa</h2>
                <div class="chart-container" id="chartEmpresa"></div>
            </div>
            <div class="section">
                <h2>Distribuicao por Tipo de Operacao</h2>
                <div class="chart-container" id="chartTipo"></div>
            </div>
        </div>

        <div class="row">
            <div class="section">
                <h2>Top 10 Fornecedores</h2>
                <div class="chart-container" id="chartFornecedor"></div>
            </div>
            <div class="section">
                <h2>Evolucao Mensal</h2>
                <div class="chart-container" id="chartMes"></div>
            </div>
        </div>

        <div class="section" style="margin-bottom: 20px;">
            <h2>Detalhamento por Empresa</h2>
            <div class="table-container">
                <table id="tabelaEmpresas">
                    <thead>
                        <tr>
                            <th onclick="ordenarTabela('tabelaEmpresas', 0)">Empresa</th>
                            <th onclick="ordenarTabela('tabelaEmpresas', 1)">Pedidos</th>
                            <th onclick="ordenarTabela('tabelaEmpresas', 2)">Produtos</th>
                            <th onclick="ordenarTabela('tabelaEmpresas', 3)" class="valor">Valor Pendente</th>
                            <th onclick="ordenarTabela('tabelaEmpresas', 4)" class="valor">% do Total</th>
                        </tr>
                    </thead>
                    <tbody id="bodyEmpresas">
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section" style="margin-bottom: 20px;">
            <h2>Top 20 Fornecedores com Pendencias</h2>
            <div class="search-box">
                <input type="text" id="searchFornecedor" placeholder="Buscar fornecedor..." onkeyup="filtrarTabelaFornecedores()">
            </div>
            <div class="table-container">
                <table id="tabelaFornecedores">
                    <thead>
                        <tr>
                            <th onclick="ordenarTabela('tabelaFornecedores', 0)">Fornecedor</th>
                            <th onclick="ordenarTabela('tabelaFornecedores', 1)">Pedidos</th>
                            <th onclick="ordenarTabela('tabelaFornecedores', 2)">Produtos</th>
                            <th onclick="ordenarTabela('tabelaFornecedores', 3)" class="valor">Valor Pendente</th>
                            <th onclick="ordenarTabela('tabelaFornecedores', 4)" class="valor">% do Total</th>
                        </tr>
                    </thead>
                    <tbody id="bodyFornecedores">
                    </tbody>
                </table>
            </div>
        </div>

        <div class="alert" id="alertAntigos">
            <span class="alert-icon">⚠️</span>
            <div id="alertTexto">
                <strong>Atencao:</strong> Verificando pedidos antigos...
            </div>
        </div>

        <div class="section">
            <h2>Pedidos Mais Antigos</h2>
            <div class="table-container">
                <table id="tabelaAntigos">
                    <thead>
                        <tr>
                            <th>Nro Unico</th>
                            <th>Nro Pedido</th>
                            <th>Empresa</th>
                            <th>Fornecedor</th>
                            <th>Data</th>
                            <th class="valor">Valor Pendente</th>
                        </tr>
                    </thead>
                    <tbody id="bodyAntigos">
                    </tbody>
                </table>
            </div>
        </div>

        <div class="footer">
            <strong>MMarra Data Hub</strong> - Relatorio interativo gerado automaticamente<br>
            {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} | Plotly.js para graficos interativos
        </div>
    </div>

    <script>
        // Dados completos
        const dadosOriginais = {json.dumps(dados_completos, ensure_ascii=False, default=str)};
        let dadosFiltrados = [...dadosOriginais];

        // Cores do tema
        const cores = ['#1565c0', '#ff6f00', '#2e7d32', '#c62828', '#7b1fa2', '#00796b', '#c2185b', '#303f9f', '#455a64', '#5d4037'];

        // Formatacao de moeda
        function formatarMoeda(valor) {{
            return 'R$ ' + valor.toLocaleString('pt-BR', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
        }}

        function formatarNumero(valor) {{
            return valor.toLocaleString('pt-BR');
        }}

        // Aplicar filtros
        function aplicarFiltros() {{
            const empresa = document.getElementById('filterEmpresa').value;
            const fornecedor = document.getElementById('filterFornecedor').value;
            const dataDe = document.getElementById('filterDataDe').value;
            const dataAte = document.getElementById('filterDataAte').value;

            dadosFiltrados = dadosOriginais.filter(item => {{
                if (empresa && item.EMPRESA !== empresa) return false;
                if (fornecedor && item.FORNECEDOR !== fornecedor) return false;
                if (dataDe && item.DTNEG_DT) {{
                    const itemData = new Date(item.DTNEG_DT);
                    if (itemData < new Date(dataDe)) return false;
                }}
                if (dataAte && item.DTNEG_DT) {{
                    const itemData = new Date(item.DTNEG_DT);
                    if (itemData > new Date(dataAte + 'T23:59:59')) return false;
                }}
                return true;
            }});

            // Mostrar info de filtros
            const filterInfo = document.getElementById('filterInfo');
            const filterTags = document.getElementById('filterTags');
            let tags = [];
            if (empresa) tags.push(`<span class="filter-tag">Empresa: ${{empresa}}</span>`);
            if (fornecedor) tags.push(`<span class="filter-tag">Fornecedor: ${{fornecedor.substring(0,30)}}</span>`);
            if (dataDe) tags.push(`<span class="filter-tag">De: ${{dataDe}}</span>`);
            if (dataAte) tags.push(`<span class="filter-tag">Ate: ${{dataAte}}</span>`);

            if (tags.length > 0) {{
                filterInfo.classList.add('active');
                filterTags.innerHTML = tags.join('');
            }} else {{
                filterInfo.classList.remove('active');
            }}

            atualizarDashboard();
        }}

        function limparFiltros() {{
            document.getElementById('filterEmpresa').value = '';
            document.getElementById('filterFornecedor').value = '';
            document.getElementById('filterDataDe').value = '';
            document.getElementById('filterDataAte').value = '';
            dadosFiltrados = [...dadosOriginais];
            document.getElementById('filterInfo').classList.remove('active');
            atualizarDashboard();
        }}

        // Atualizar dashboard
        function atualizarDashboard() {{
            // Calcular metricas
            const totalValor = dadosFiltrados.reduce((sum, item) => sum + (parseFloat(item.VALOR_PENDENTE) || 0), 0);
            const pedidos = [...new Set(dadosFiltrados.map(item => item.NUNOTA))];
            const fornecedores = [...new Set(dadosFiltrados.map(item => item.FORNECEDOR))];
            const produtos = [...new Set(dadosFiltrados.map(item => item.CODPROD))];
            const empresas = [...new Set(dadosFiltrados.map(item => item.EMPRESA))];

            // Atualizar cards
            document.getElementById('totalValor').textContent = formatarMoeda(totalValor);
            document.getElementById('cardPedidos').textContent = formatarNumero(pedidos.length);
            document.getElementById('cardFornecedores').textContent = formatarNumero(fornecedores.length);
            document.getElementById('cardItens').textContent = formatarNumero(dadosFiltrados.length);
            document.getElementById('cardProdutos').textContent = formatarNumero(produtos.length);
            document.getElementById('cardEmpresas').textContent = formatarNumero(empresas.length);

            // Atualizar graficos
            atualizarGraficos(totalValor);

            // Atualizar tabelas
            atualizarTabelas(totalValor);

            // Atualizar alerta
            atualizarAlerta();
        }}

        function atualizarGraficos(totalValor) {{
            // Por empresa
            const porEmpresa = {{}};
            dadosFiltrados.forEach(item => {{
                const key = item.EMPRESA || 'N/A';
                if (!porEmpresa[key]) porEmpresa[key] = 0;
                porEmpresa[key] += parseFloat(item.VALOR_PENDENTE) || 0;
            }});
            const empresasOrdenadas = Object.entries(porEmpresa).sort((a, b) => b[1] - a[1]);

            Plotly.react('chartEmpresa', [{{
                x: empresasOrdenadas.map(e => e[0]),
                y: empresasOrdenadas.map(e => e[1]),
                type: 'bar',
                marker: {{ color: cores, cornerradius: 4 }},
                hovertemplate: '<b>%{{x}}</b><br>Valor: R$ %{{y:,.2f}}<extra></extra>'
            }}], {{
                margin: {{ t: 20, b: 80, l: 80, r: 20 }},
                yaxis: {{ tickformat: ',.0f', tickprefix: 'R$ ' }},
                xaxis: {{ tickangle: -30 }},
                hoverlabel: {{ bgcolor: '#fff', font: {{ size: 12 }} }}
            }}, {{ responsive: true, displayModeBar: true }});

            // Por tipo
            const porTipo = {{}};
            dadosFiltrados.forEach(item => {{
                const key = (item.TIPO_OPERACAO || 'N/A').substring(0, 25);
                if (!porTipo[key]) porTipo[key] = 0;
                porTipo[key] += parseFloat(item.VALOR_PENDENTE) || 0;
            }});
            const tiposOrdenados = Object.entries(porTipo).sort((a, b) => b[1] - a[1]).slice(0, 8);

            Plotly.react('chartTipo', [{{
                labels: tiposOrdenados.map(t => t[0]),
                values: tiposOrdenados.map(t => t[1]),
                type: 'pie',
                hole: 0.5,
                marker: {{ colors: cores }},
                textinfo: 'percent',
                hovertemplate: '<b>%{{label}}</b><br>Valor: R$ %{{value:,.2f}}<br>%{{percent}}<extra></extra>'
            }}], {{
                margin: {{ t: 20, b: 20, l: 20, r: 20 }},
                showlegend: true,
                legend: {{ x: 1, y: 0.5, font: {{ size: 10 }} }}
            }}, {{ responsive: true, displayModeBar: false }});

            // Por fornecedor (top 10)
            const porFornecedor = {{}};
            dadosFiltrados.forEach(item => {{
                const key = (item.FORNECEDOR || 'N/A').substring(0, 25);
                if (!porFornecedor[key]) porFornecedor[key] = 0;
                porFornecedor[key] += parseFloat(item.VALOR_PENDENTE) || 0;
            }});
            const fornecedoresOrdenados = Object.entries(porFornecedor).sort((a, b) => b[1] - a[1]).slice(0, 10).reverse();

            Plotly.react('chartFornecedor', [{{
                y: fornecedoresOrdenados.map(f => f[0]),
                x: fornecedoresOrdenados.map(f => f[1]),
                type: 'bar',
                orientation: 'h',
                marker: {{ color: '#1565c0', cornerradius: 4 }},
                hovertemplate: '<b>%{{y}}</b><br>Valor: R$ %{{x:,.2f}}<extra></extra>'
            }}], {{
                margin: {{ t: 20, b: 40, l: 150, r: 20 }},
                xaxis: {{ tickformat: ',.0f', tickprefix: 'R$ ' }}
            }}, {{ responsive: true, displayModeBar: true }});

            // Por mes
            const porMes = {{}};
            dadosFiltrados.forEach(item => {{
                if (item.MES) {{
                    if (!porMes[item.MES]) porMes[item.MES] = 0;
                    porMes[item.MES] += parseFloat(item.VALOR_PENDENTE) || 0;
                }}
            }});
            const mesesOrdenados = Object.entries(porMes).sort((a, b) => a[0].localeCompare(b[0])).slice(-12);

            Plotly.react('chartMes', [{{
                x: mesesOrdenados.map(m => m[0]),
                y: mesesOrdenados.map(m => m[1]),
                type: 'scatter',
                mode: 'lines+markers',
                fill: 'tozeroy',
                line: {{ color: '#1565c0', width: 3, shape: 'spline' }},
                marker: {{ size: 8, color: '#1565c0' }},
                hovertemplate: '<b>%{{x}}</b><br>Valor: R$ %{{y:,.2f}}<extra></extra>'
            }}], {{
                margin: {{ t: 20, b: 40, l: 80, r: 20 }},
                yaxis: {{ tickformat: ',.0f', tickprefix: 'R$ ' }}
            }}, {{ responsive: true, displayModeBar: true }});
        }}

        function atualizarTabelas(totalValor) {{
            // Tabela empresas
            const porEmpresa = {{}};
            dadosFiltrados.forEach(item => {{
                const key = item.EMPRESA || 'N/A';
                if (!porEmpresa[key]) porEmpresa[key] = {{ valor: 0, pedidos: new Set(), produtos: new Set() }};
                porEmpresa[key].valor += parseFloat(item.VALOR_PENDENTE) || 0;
                porEmpresa[key].pedidos.add(item.NUNOTA);
                porEmpresa[key].produtos.add(item.CODPROD);
            }});

            let htmlEmpresas = '';
            Object.entries(porEmpresa)
                .sort((a, b) => b[1].valor - a[1].valor)
                .forEach(([empresa, dados]) => {{
                    const pct = totalValor > 0 ? (dados.valor / totalValor * 100) : 0;
                    const badgeClass = pct > 30 ? 'badge-danger' : pct > 15 ? 'badge-warning' : 'badge-info';
                    htmlEmpresas += `
                        <tr>
                            <td><strong>${{empresa}}</strong></td>
                            <td>${{dados.pedidos.size}}</td>
                            <td>${{dados.produtos.size}}</td>
                            <td class="valor">${{formatarMoeda(dados.valor)}}</td>
                            <td class="valor"><span class="badge ${{badgeClass}}">${{pct.toFixed(1)}}%</span></td>
                        </tr>
                    `;
                }});
            document.getElementById('bodyEmpresas').innerHTML = htmlEmpresas;

            // Tabela fornecedores
            const porFornecedor = {{}};
            dadosFiltrados.forEach(item => {{
                const key = item.FORNECEDOR || 'N/A';
                if (!porFornecedor[key]) porFornecedor[key] = {{ valor: 0, pedidos: new Set(), produtos: new Set() }};
                porFornecedor[key].valor += parseFloat(item.VALOR_PENDENTE) || 0;
                porFornecedor[key].pedidos.add(item.NUNOTA);
                porFornecedor[key].produtos.add(item.CODPROD);
            }});

            let htmlFornecedores = '';
            Object.entries(porFornecedor)
                .sort((a, b) => b[1].valor - a[1].valor)
                .slice(0, 20)
                .forEach(([fornecedor, dados]) => {{
                    const pct = totalValor > 0 ? (dados.valor / totalValor * 100) : 0;
                    const badgeClass = pct > 10 ? 'badge-danger' : pct > 5 ? 'badge-warning' : 'badge-info';
                    htmlFornecedores += `
                        <tr data-fornecedor="${{fornecedor.toLowerCase()}}">
                            <td>${{fornecedor.substring(0, 50)}}</td>
                            <td>${{dados.pedidos.size}}</td>
                            <td>${{dados.produtos.size}}</td>
                            <td class="valor">${{formatarMoeda(dados.valor)}}</td>
                            <td class="valor"><span class="badge ${{badgeClass}}">${{pct.toFixed(1)}}%</span></td>
                        </tr>
                    `;
                }});
            document.getElementById('bodyFornecedores').innerHTML = htmlFornecedores;

            // Tabela antigos
            const pedidosAgrupados = {{}};
            dadosFiltrados.forEach(item => {{
                if (!pedidosAgrupados[item.NUNOTA]) {{
                    pedidosAgrupados[item.NUNOTA] = {{
                        ...item,
                        VALOR_TOTAL: 0
                    }};
                }}
                pedidosAgrupados[item.NUNOTA].VALOR_TOTAL += parseFloat(item.VALOR_PENDENTE) || 0;
            }});

            const antigosOrdenados = Object.values(pedidosAgrupados)
                .filter(p => p.DTNEG_DT)
                .sort((a, b) => new Date(a.DTNEG_DT) - new Date(b.DTNEG_DT))
                .slice(0, 20);

            let htmlAntigos = '';
            antigosOrdenados.forEach(pedido => {{
                const data = pedido.DATA_PEDIDO || 'N/A';
                htmlAntigos += `
                    <tr>
                        <td>${{pedido.NUNOTA}}</td>
                        <td>${{pedido.NRO_PEDIDO || '-'}}</td>
                        <td>${{pedido.EMPRESA || 'N/A'}}</td>
                        <td>${{(pedido.FORNECEDOR || 'N/A').substring(0, 40)}}</td>
                        <td>${{data}}</td>
                        <td class="valor">${{formatarMoeda(pedido.VALOR_TOTAL)}}</td>
                    </tr>
                `;
            }});
            document.getElementById('bodyAntigos').innerHTML = htmlAntigos;
        }}

        function atualizarAlerta() {{
            const pedidosComData = dadosFiltrados.filter(p => p.DTNEG_DT);
            if (pedidosComData.length === 0) return;

            const maisAntigo = pedidosComData.reduce((oldest, p) =>
                new Date(p.DTNEG_DT) < new Date(oldest.DTNEG_DT) ? p : oldest
            );

            const diasAntigo = Math.floor((new Date() - new Date(maisAntigo.DTNEG_DT)) / (1000 * 60 * 60 * 24));
            const dataFormatada = maisAntigo.DATA_PEDIDO || 'N/A';

            document.getElementById('alertTexto').innerHTML = `
                <strong>Atencao:</strong> Existem pedidos pendentes desde ${{dataFormatada}} (${{diasAntigo}} dias).
                Verifique os pedidos mais antigos abaixo.
            `;
        }}

        // Filtrar tabela de fornecedores
        function filtrarTabelaFornecedores() {{
            const busca = document.getElementById('searchFornecedor').value.toLowerCase();
            const linhas = document.querySelectorAll('#bodyFornecedores tr');
            linhas.forEach(linha => {{
                const fornecedor = linha.getAttribute('data-fornecedor') || '';
                linha.style.display = fornecedor.includes(busca) ? '' : 'none';
            }});
        }}

        // Ordenar tabela
        let ordemAtual = {{}};
        function ordenarTabela(tabelaId, coluna) {{
            const tabela = document.getElementById(tabelaId);
            const tbody = tabela.querySelector('tbody');
            const linhas = Array.from(tbody.querySelectorAll('tr'));

            // Alternar ordem
            const chave = tabelaId + '_' + coluna;
            ordemAtual[chave] = !ordemAtual[chave];
            const ordem = ordemAtual[chave] ? 1 : -1;

            linhas.sort((a, b) => {{
                let valorA = a.cells[coluna].textContent.trim();
                let valorB = b.cells[coluna].textContent.trim();

                // Tentar converter para numero
                const numA = parseFloat(valorA.replace(/[R$%\s.]/g, '').replace(',', '.'));
                const numB = parseFloat(valorB.replace(/[R$%\s.]/g, '').replace(',', '.'));

                if (!isNaN(numA) && !isNaN(numB)) {{
                    return (numA - numB) * ordem;
                }}

                return valorA.localeCompare(valorB) * ordem;
            }});

            linhas.forEach(linha => tbody.appendChild(linha));
        }}

        // Click nos graficos para filtrar
        document.getElementById('chartEmpresa').on('plotly_click', function(data) {{
            const empresa = data.points[0].x;
            document.getElementById('filterEmpresa').value = empresa;
            aplicarFiltros();
        }});

        document.getElementById('chartFornecedor').on('plotly_click', function(data) {{
            const fornecedor = data.points[0].y;
            const selectFornecedor = document.getElementById('filterFornecedor');
            for (let option of selectFornecedor.options) {{
                if (option.text.startsWith(fornecedor)) {{
                    selectFornecedor.value = option.value;
                    break;
                }}
            }}
            aplicarFiltros();
        }});

        // Inicializar
        document.addEventListener('DOMContentLoaded', function() {{
            atualizarDashboard();
        }});
    </script>
</body>
</html>
"""

    # Salvar
    output_dir = Path(__file__).parent.parent.parent / "src" / "data" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f'pedidos_compra_pendentes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html'

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\nRelatorio salvo em: {output_file}")
    print(f"Tamanho: {output_file.stat().st_size / 1024:.1f} KB")
    print(f"\nCaracteristicas do relatorio:")
    print(f"  - Graficos interativos com Plotly.js (zoom, hover, click)")
    print(f"  - Filtros por empresa, fornecedor e periodo")
    print(f"  - Tabelas com ordenacao (clique no cabecalho)")
    print(f"  - Busca de fornecedores")
    print(f"  - Click nos graficos filtra os dados")

    return output_file


if __name__ == "__main__":
    gerar_relatorio_pedidos_pendentes()
