import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

# --- 1. Configuração e Identidade Visual ---
COR_PRIMARIA = "#10b981"  # Verde
COR_SECUNDARIA = "#1e293b" # Azul Marinho
COR_TEXTO = "#1e293b"

st.set_page_config(page_title="Frota BI | Gestão Estratégica", page_icon="🚛", layout="wide")

# CSS para garantir visibilidade e estilo profissional
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; color: {COR_TEXTO}; }}
        .stApp {{ background-color: #f8fafc; }}
        
        /* Estilização das Abas */
        .stTabs [data-baseweb="tab"] {{
            height: 50px;
            background-color: #ffffff;
            border-radius: 8px 8px 0px 0px;
            padding: 10px 20px;
            color: #64748b !important;
            font-weight: 600;
        }}
        .stTabs [aria-selected="true"] {{
            color: {COR_PRIMARIA} !important;
            border-bottom: 3px solid {COR_PRIMARIA} !important;
        }}

        /* Estilização dos Containers e Cards */
        .chart-container {{
            background-color: #ffffff;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }}
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
        st.error(f"Erro ao carregar banco: {e}")
        return pd.DataFrame()

df_base = carregar_dados_sql()

# --- 3. Sidebar com Filtros de Performance ---
with st.sidebar:
    st.markdown(f"### ⚙️ Filtros de Performance")
    st.divider()
    
    if not df_base.empty:
        # Filtro 1: Período
        meses_selecionados = st.multiselect("Selecione os Meses:", df_base['Mês'].unique(), default=df_base['Mês'].unique())
        
        # Filtro 2: Faixa de Gasto (Slider)
        gasto_min, gasto_max = float(df_base['Gasto'].min()), float(df_base['Gasto'].max())
        filtro_gasto = st.slider("Faixa de Investimento (R$):", gasto_min, gasto_max, (gasto_min, gasto_max))
        
        # Filtro 3: Eficiência (Slider)
        custo_km_max = float(df_base['Custo/KM'].max())
        filtro_eficiencia = st.slider("Limite de Custo por KM (R$):", 0.0, custo_km_max, custo_km_max)
        
        st.divider()
        if st.button("Resetar Filtros"):
            st.rerun()

    st.caption(f"Gabriel Barbosa | Analista Administrativo")

# --- 4. Lógica de Filtragem ---
if not df_base.empty:
    mask = (
        (df_base['Mês'].isin(meses_selecionados)) &
        (df_base['Gasto'] >= filtro_gasto[0]) &
        (df_base['Gasto'] <= filtro_gasto[1]) &
        (df_base['Custo/KM'] <= filtro_eficiencia)
    )
    df_filtrado = df_base[mask]

    # --- 5. Interface Principal ---
    aba1, aba2 = st.tabs(["📊 Visão Geral", "🧠 Diagnóstico de Performance"])

    # ABA 1: Visão Geral (Responde a todos os filtros)
    with aba1:
        st.markdown(f"<h2 style='color:{COR_SECUNDARIA}; margin-top:0;'>Dashboard Estratégico</h2>", unsafe_allow_html=True)
        
        if df_filtrado.empty:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Gasto Total", f"R$ {df_filtrado['Gasto'].sum():,.2f}")
            c2.metric("Média no Período", f"R$ {df_filtrado['Gasto'].mean():,.2f}")
            c3.metric("Total KM", f"{df_filtrado['KM'].sum():,}".replace(',', '.'))
            c4.metric("Eficiência Média", f"R$ {df_filtrado['Custo/KM'].mean():.3f}")

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

            st.markdown('<div class="chart-container"><b style="color:#1e293b">Dados Consolidados</b>', unsafe_allow_html=True)
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True, column_config={
                "Gasto": st.column_config.ProgressColumn("Gasto", format="R$ %.2f", min_value=0, max_value=df_base['Gasto'].max()),
                "Custo/KM": st.column_config.NumberColumn("R$/KM", format="R$ %.3f")
            })
            st.markdown('</div>', unsafe_allow_html=True)

    # ABA 2: Diagnóstico (Foca em um mês específico comparado ao todo)
    with aba2:
        st.markdown(f"<h2 style='color:{COR_SECUNDARIA}; margin-top:0;'>Análise de Desvio</h2>", unsafe_allow_html=True)
        mes_diagnostico = st.selectbox("Escolha o mês para auditoria:", df_base['Mês'].unique())
        
        media_anual = df_base['Gasto'].mean()
        dados_mes = df_base[df_base['Mês'] == mes_diagnostico].iloc[0]
        desvio = ((dados_mes['Gasto'] - media_anual) / media_anual) * 100

        diag1, diag2, diag3 = st.columns(3)
        diag1.metric(f"Gasto em {mes_diagnostico}", f"R$ {dados_mes['Gasto']:,.2f}", f"{desvio:.1f}% vs média", delta_color="inverse")
        diag2.metric("Média Global", f"R$ {media_anual:,.2f}")
        status = "⚠️ CRÍTICO" if desvio > 10 else "✅ ESTÁVEL"
        diag3.metric("Status Operacional", status)

        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        diag_chart = alt.Chart(df_base).mark_bar().encode(
            x=alt.X('Mês', title=None),
            y=alt.Y('Gasto', title=None),
            color=alt.condition(alt.datum.Mês == mes_diagnostico, alt.value(COR_PRIMARIA), alt.value('#e2e8f0'))
        ).properties(height=350)
        linha_ref = alt.Chart(pd.DataFrame({'y': [media_anual]})).mark_rule(color='#ef4444', strokeDash=[5,5]).encode(y='y')
        st.altair_chart(diag_chart + linha_ref, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Aguardando dados...")