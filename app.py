import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

# --- 1. Configuração da Página e Identidade Visual ---
COR_PRIMARIA = "#10b981"  # Verde
COR_SECUNDARIA = "#1e293b" # Azul Marinho
COR_TEXTO = "#1e293b"      # Forçando texto escuro

st.set_page_config(page_title="Frota BI | Pro", page_icon="🚛", layout="wide")

# CSS para garantir que TUDO seja visível (Abas, Títulos e Métricas)
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; color: {COR_TEXTO}; }}
        .stApp {{ background-color: #f8fafc; }}
        
        /* --- CORREÇÃO DAS ABAS (Títulos Invisíveis) --- */
        .stTabs [data-baseweb="tab-list"] {{ gap: 24px; }}
        
        /* Estilo da Aba Inativa */
        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            background-color: #ffffff;
            border-radius: 8px 8px 0px 0px;
            padding: 10px 20px;
            color: #64748b !important; /* Cinza para abas não selecionadas */
            font-weight: 600;
        }}
        
        /* Estilo da Aba Ativa (Selecionada) */
        .stTabs [aria-selected="true"] {{
            background-color: #ffffff !important;
            color: {COR_PRIMARIA} !important; /* Verde para a aba ativa */
            border-bottom: 3px solid {COR_PRIMARIA} !important;
        }}

        /* Estilização dos Containers */
        .chart-container {{
            background-color: #ffffff;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
            color: {COR_TEXTO};
        }}

        /* Estilização das Métricas (Cards) */
        div[data-testid="stMetric"] {{
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
        }}
        [data-testid="stMetricLabel"] p {{ color: #64748b !important; font-weight: 600 !important; }}
        [data-testid="stMetricValue"] div {{ color: {COR_SECUNDARIA} !important; font-weight: 800 !important; }}

        #MainMenu, footer, header {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. Funções de Dados ---
@st.cache_data
def carregar_dados_sql():
    try:
        conn = sqlite3.connect('manutencao.db')
        df = pd.read_sql("SELECT mes, gasto_real, km_rodado FROM custos_frota", conn)
        conn.close()
        ordem = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        df['mes'] = pd.Categorical(df['mes'], categories=ordem, ordered=True)
        df = df.sort_values('mes').rename(columns={'mes': 'Mês', 'gasto_real': 'Gasto', 'km_rodado': 'KM'})
        df['Custo/KM'] = df['Gasto'] / df['KM']
        return df
    except Exception as e:
        st.error(f"Erro: {e}")
        return pd.DataFrame()

df_base = carregar_dados_sql()

# --- 3. Sidebar ---
with st.sidebar:
    st.markdown("### 🔍 Central de Controle")
    st.divider()
    if not df_base.empty:
        meses_selecionados = st.multiselect("Filtrar Período:", df_base['Mês'].unique(), default=df_base['Mês'].unique())
    st.caption("Gabriel Barbosa | Analista Administrativo")

# --- 4. Interface com ABAS ---
if not df_base.empty:
    df_filtrado = df_base[df_base['Mês'].isin(meses_selecionados)]
    
    aba1, aba2 = st.tabs(["📊 Visão Geral da Frota", "🧠 Diagnóstico de Performance"])

    # --- ABA 1: VISÃO GERAL ---
    with aba1:
        st.markdown(f"<h2 style='color:{COR_SECUNDARIA}; margin-top:0;'>Painel de Custos e Rodagem</h2>", unsafe_allow_html=True)
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Gasto Total", f"R$ {df_filtrado['Gasto'].sum():,.2f}")
        c2.metric("Média Mensal", f"R$ {df_filtrado['Gasto'].mean():,.2f}")
        c3.metric("KM Rodados", f"{df_filtrado['KM'].sum():,}".replace(',', '.'))
        c4.metric("Custo/KM Médio", f"R$ {df_filtrado['Custo/KM'].mean():.3f}")

        col_esq, col_dir = st.columns(2)
        with col_esq:
            st.markdown('<div class="chart-container"><b style="color:#1e293b">Evolução de Custos (R$)</b>', unsafe_allow_html=True)
            chart_area = alt.Chart(df_filtrado).mark_area(line={'color':COR_PRIMARIA}, color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color=COR_PRIMARIA, offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0), interpolate='monotone').encode(x=alt.X('Mês', title=None), y=alt.Y('Gasto', title=None, axis=alt.Axis(format=',.0f', grid=True, labelPadding=10))).properties(height=300)
            st.altair_chart(chart_area, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col_dir:
            st.markdown('<div class="chart-container"><b style="color:#1e293b">Volume de Quilometragem</b>', unsafe_allow_html=True)
            chart_bar = alt.Chart(df_filtrado).mark_bar(color=COR_PRIMARIA, cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=35).encode(x=alt.X('Mês', title=None), y=alt.Y('KM', title=None, axis=alt.Axis(format=',.0f', grid=True, labelPadding=10))).properties(height=300)
            st.altair_chart(chart_bar, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="chart-container"><b style="color:#1e293b">Tabela de Detalhamento</b>', unsafe_allow_html=True)
        st.dataframe(df_filtrado, use_container_width=True, hide_index=True, column_config={"Gasto": st.column_config.ProgressColumn("Gasto Real", format="R$ %.2f", min_value=0, max_value=df_base['Gasto'].max())})
        st.markdown('</div>', unsafe_allow_html=True)

    # --- ABA 2: DIAGNÓSTICO ---
    with aba2:
        st.markdown(f"<h2 style='color:{COR_SECUNDARIA}; margin-top:0;'>Análise Comparativa de Desvios</h2>", unsafe_allow_html=True)
        
        mes_diagnostico = st.selectbox("Escolha o mês para análise profunda:", df_base['Mês'].unique())
        
        media_anual = df_base['Gasto'].mean()
        dados_mes = df_base[df_base['Mês'] == mes_diagnostico].iloc[0]
        desvio = ((dados_mes['Gasto'] - media_anual) / media_anual) * 100

        c_diag1, c_diag2, c_diag3 = st.columns(3)
        c_diag1.metric(f"Gasto em {mes_diagnostico}", f"R$ {dados_mes['Gasto']:,.2f}", f"{desvio:.1f}% vs média", delta_color="inverse")
        c_diag2.metric("Média de Referência", f"R$ {media_anual:,.2f}")
        status = "⚠️ ACIMA DA MÉDIA" if desvio > 0 else "✅ DENTRO DA META"
        c_diag3.metric("Status Operacional", status)

        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        diag_chart = alt.Chart(df_base).mark_bar().encode(x=alt.X('Mês', title=None), y=alt.Y('Gasto', title=None), color=alt.condition(alt.datum.Mês == mes_diagnostico, alt.value(COR_PRIMARIA), alt.value('#e2e8f0')), tooltip=['Mês', 'Gasto']).properties(height=350)
        linha_media = alt.Chart(pd.DataFrame({'y': [media_anual]})).mark_rule(color='#ef4444', strokeDash=[5,5]).encode(y='y')
        st.altair_chart(diag_chart + linha_media, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if desvio > 10:
            st.error(f"O mês de {mes_diagnostico} está com custos elevados. Verifique as manutenções corretivas.")
        else:
            st.success(f"O desempenho de {mes_diagnostico} está saudável perante a média anual.")
else:
    st.info("Carregando banco de dados...")