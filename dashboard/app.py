# -*- coding: utf-8 -*-
"""
MMarra Data Hub - Dashboard Web

Dashboard interativo para visualizacao de KPIs, previsoes e anomalias.

Uso:
    streamlit run dashboard/app.py
"""

import sys
from pathlib import Path

# Adicionar diretório raiz do projeto ao path
ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Configuracao da pagina
st.set_page_config(
    page_title="MMarra Data Hub",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def carregar_vendas():
    """Carrega dados de vendas."""
    vendas_path = ROOT_DIR / "src/data/raw/vendas/vendas.parquet"
    if vendas_path.exists():
        df = pd.read_parquet(vendas_path)
        df['DTNEG'] = pd.to_datetime(df['DTNEG'], errors='coerce')
        return df
    return None


@st.cache_data
def carregar_modelos_prophet():
    """Lista modelos Prophet disponíveis."""
    models_dir = ROOT_DIR / "src/agents/scientist/models/demand"
    if models_dir.exists():
        return list(models_dir.glob("*.pkl"))
    return []


def calcular_kpis(df: pd.DataFrame, dias: int = 30):
    """Calcula KPIs principais."""
    # Filtrar por período
    data_limite = df['DTNEG'].max() - timedelta(days=dias)
    df_periodo = df[df['DTNEG'] >= data_limite]

    # KPIs
    faturamento = df_periodo['VLRTOT'].sum()
    qtd_pedidos = df_periodo['NUNOTA'].nunique()
    qtd_itens = df_periodo['QTDNEG'].sum()
    ticket_medio = faturamento / qtd_pedidos if qtd_pedidos > 0 else 0
    clientes_ativos = df_periodo['CODPARC'].nunique()
    produtos_vendidos = df_periodo['CODPROD'].nunique()

    return {
        'faturamento': faturamento,
        'qtd_pedidos': qtd_pedidos,
        'qtd_itens': qtd_itens,
        'ticket_medio': ticket_medio,
        'clientes_ativos': clientes_ativos,
        'produtos_vendidos': produtos_vendidos
    }


def main():
    # Header
    st.markdown('<p class="main-header">📊 MMarra Data Hub</p>', unsafe_allow_html=True)
    st.markdown("Dashboard de Análise de Dados - Distribuidora Automotiva")

    # Sidebar
    st.sidebar.title("⚙️ Configurações")

    # Carregar dados
    df = carregar_vendas()

    if df is None:
        st.error("❌ Dados de vendas não encontrados!")
        st.info("Execute: `python scripts/extracao/extrair_vendas_completo.py`")
        return

    st.sidebar.success(f"✅ {len(df):,} registros carregados".replace(",", "."))

    # Filtro de período
    periodo = st.sidebar.selectbox(
        "Período de Análise",
        ["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Todo o período"]
    )

    dias_map = {
        "Últimos 7 dias": 7,
        "Últimos 30 dias": 30,
        "Últimos 90 dias": 90,
        "Todo o período": 9999
    }
    dias = dias_map[periodo]

    # Filtrar dados
    if dias < 9999:
        data_limite = df['DTNEG'].max() - timedelta(days=dias)
        df_filtrado = df[df['DTNEG'] >= data_limite]
    else:
        df_filtrado = df

    # ========================================
    # KPIs
    # ========================================
    st.subheader("📈 Indicadores Principais")

    kpis = calcular_kpis(df, dias)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="💰 Faturamento",
            value=f"R$ {kpis['faturamento']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

    with col2:
        st.metric(
            label="📦 Pedidos",
            value=f"{kpis['qtd_pedidos']:,}".replace(",", ".")
        )

    with col3:
        st.metric(
            label="🛒 Ticket Médio",
            value=f"R$ {kpis['ticket_medio']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

    with col4:
        st.metric(
            label="👥 Clientes Ativos",
            value=f"{kpis['clientes_ativos']:,}".replace(",", ".")
        )

    st.divider()

    # ========================================
    # Gráficos
    # ========================================
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📅 Vendas por Dia")

        # Agrupar por dia
        vendas_dia = df_filtrado.groupby(df_filtrado['DTNEG'].dt.date).agg({
            'VLRTOT': 'sum',
            'NUNOTA': 'nunique'
        }).reset_index()
        vendas_dia.columns = ['Data', 'Faturamento', 'Pedidos']

        fig_linha = px.line(
            vendas_dia,
            x='Data',
            y='Faturamento',
            title='Faturamento Diário'
        )
        fig_linha.update_layout(
            xaxis_title="Data",
            yaxis_title="Faturamento (R$)",
            showlegend=False
        )
        st.plotly_chart(fig_linha, use_container_width=True)

    with col_right:
        st.subheader("🏆 Top 10 Produtos")

        # Top produtos
        top_produtos = df_filtrado.groupby(['CODPROD', 'DESCRPROD']).agg({
            'QTDNEG': 'sum',
            'VLRTOT': 'sum'
        }).reset_index()
        top_produtos = top_produtos.nlargest(10, 'VLRTOT')
        top_produtos['DESCRICAO'] = top_produtos['DESCRPROD'].str[:30]

        fig_barra = px.bar(
            top_produtos,
            x='VLRTOT',
            y='DESCRICAO',
            orientation='h',
            title='Top 10 Produtos (Faturamento)'
        )
        fig_barra.update_layout(
            xaxis_title="Faturamento (R$)",
            yaxis_title="",
            showlegend=False,
            yaxis={'categoryorder': 'total ascending'}
        )
        st.plotly_chart(fig_barra, use_container_width=True)

    st.divider()

    # ========================================
    # Análises Avançadas
    # ========================================
    tab1, tab2, tab3 = st.tabs(["🔮 Previsões Prophet", "⚠️ Anomalias", "📊 Curva ABC"])

    with tab1:
        st.subheader("🔮 Previsões de Demanda (Prophet)")

        modelos = carregar_modelos_prophet()

        if modelos:
            st.success(f"✅ {len(modelos)} modelos treinados disponíveis")

            # Listar modelos
            modelos_info = []
            for m in modelos:
                nome = m.stem
                partes = nome.split('_')
                if len(partes) >= 3:
                    codprod = partes[2]
                    modelos_info.append({
                        'arquivo': m.name,
                        'codprod': codprod,
                        'data': '_'.join(partes[3:]) if len(partes) > 3 else ''
                    })

            df_modelos = pd.DataFrame(modelos_info)
            st.dataframe(df_modelos, use_container_width=True)

            # Selecionar modelo para visualizar
            if modelos_info:
                codprod_selecionado = st.selectbox(
                    "Selecione um produto para ver previsão:",
                    options=[m['codprod'] for m in modelos_info]
                )

                if st.button("Gerar Previsão"):
                    try:
                        from src.agents.scientist.forecasting import DemandPredictor
                        predictor = DemandPredictor()
                        resultado = predictor.forecast_product(int(codprod_selecionado), periods=30)

                        if resultado.get('success'):
                            st.json(resultado['previsao'])
                        else:
                            st.error(f"Erro: {resultado.get('error')}")
                    except Exception as e:
                        st.error(f"Erro ao gerar previsão: {e}")
        else:
            st.warning("⚠️ Nenhum modelo treinado encontrado.")
            st.info("Execute: `python scripts/treinar_multiplos_modelos.py`")

    with tab2:
        st.subheader("⚠️ Detecção de Anomalias")

        # Verificar se há relatório de anomalias
        anomalias_dir = ROOT_DIR / "output" / "reports"
        anomalias_files = list(anomalias_dir.glob("anomalias_*.csv")) if anomalias_dir.exists() else []

        if anomalias_files:
            ultimo_relatorio = max(anomalias_files, key=lambda x: x.stat().st_mtime)
            df_anomalias = pd.read_csv(ultimo_relatorio)

            st.success(f"✅ {len(df_anomalias)} anomalias detectadas")
            st.dataframe(df_anomalias, use_container_width=True)
        else:
            st.warning("⚠️ Nenhuma análise de anomalias encontrada.")
            st.info("Execute: `python scripts/detectar_anomalias.py`")

    with tab3:
        st.subheader("📊 Curva ABC de Produtos")

        # Calcular curva ABC
        produtos_abc = df_filtrado.groupby(['CODPROD', 'DESCRPROD'])['VLRTOT'].sum().reset_index()
        produtos_abc = produtos_abc.sort_values('VLRTOT', ascending=False)

        total = produtos_abc['VLRTOT'].sum()
        produtos_abc['percentual'] = produtos_abc['VLRTOT'] / total * 100
        produtos_abc['percentual_acum'] = produtos_abc['percentual'].cumsum()

        def classificar_abc(pct):
            if pct <= 80:
                return 'A'
            elif pct <= 95:
                return 'B'
            return 'C'

        produtos_abc['classe'] = produtos_abc['percentual_acum'].apply(classificar_abc)

        # Resumo por classe
        resumo_abc = produtos_abc.groupby('classe').agg({
            'CODPROD': 'count',
            'VLRTOT': 'sum',
            'percentual': 'sum'
        }).reset_index()
        resumo_abc.columns = ['Classe', 'Qtd Produtos', 'Faturamento', 'Percentual']

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Resumo por Classe**")
            st.dataframe(resumo_abc, use_container_width=True)

        with col2:
            fig_pie = px.pie(
                resumo_abc,
                values='Faturamento',
                names='Classe',
                title='Distribuição do Faturamento',
                color='Classe',
                color_discrete_map={'A': '#2ecc71', 'B': '#f1c40f', 'C': '#e74c3c'}
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # Footer
    st.divider()
    st.markdown(
        f"*Última atualização: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"Período dos dados: {df['DTNEG'].min().strftime('%Y-%m-%d')} a {df['DTNEG'].max().strftime('%Y-%m-%d')}*"
    )


if __name__ == "__main__":
    main()
