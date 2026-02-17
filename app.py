import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

# --- 0. CONFIGURAÇÃO ESSENCIAL DO ALTAIR ---
# Força o tema claro para evitar o fundo preto automático do Streamlit Cloud
alt.themes.enable("default")

# --- 1. Configuração e Identidade Visual ---
COR_PRIMARIA = "#10b981"   
COR_SECUNDARIA = "#334155" 
COR_TEXTO_SUAVE = "#64748b" 
COR_FUNDO_PAGINA = "#eef2f6" 
COR_CARD = "#ffffff"       

st.set_page_config(page_title="Frota BI | Gestão Estratégica", page_icon="🚛", layout="wide")

st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; color: {COR_SECUNDARIA}; }}
        .stApp {{ background-color: {COR_FUNDO_PAGINA}; }}
        .stTabs [data-baseweb="tab"] {{ height: 45px; color: {COR_TEXTO_SUAVE} !important; font-weight: 500; }}
        .stTabs [aria-selected="true"] {{ color: {COR_PRIMARIA} !important; border-bottom: 3px solid {COR_PRIMARIA} !important; font-weight: 700; }}
        .chart-container {{ background-color: {COR_CARD}; padding: 24px; border-radius: 16px; border: 1px solid #e2e8f0; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.03); margin-bottom: 24px; }}
        div[data-testid="stMetric"] {{ background-color: {COR_CARD} !important; border: 1px solid #e2e8f0; padding: 1.5rem; border-radius: 16px; text-align: left; }}
        [data-testid="stMetricLabel"] p {{ color: {COR_TEXTO_SUAVE} !important; font-size: 0.95rem !important; font-weight: 600 !important; }}
        [data-testid="stMetricValue"] div {{ color: {COR_SECUNDARIA} !important; font-size: 1.8rem !important; font-weight: 700 !important; }}
        .alert-success {{ background-color: #dcfce7; padding: 1rem; border-radius: 12px; border-left: 6px solid #22c55e; color: #1e293b !important; margin-bottom: 1rem; font-weight: 600; }}
        .alert-error {{ background-color: #fee2e2; padding: 1rem; border-radius: 12px; border-left: 6px solid #ef4444; color: #1e293b !important; margin-bottom: 1rem; font-weight: 600; }}
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
        mapa_meses = {'Jan':'Janeiro','Fev':'Fevereiro','Mar':'Março','Abr':'Abril','Mai':'Maio','Jun':'Junho','Jul':'Julho','Ago':'Agosto','Set':'Setembro','Out':'Outubro','Nov':'Novembro','Dez':'Dezembro'}
        if df['mes'].iloc[0] in mapa_meses: df['mes'] = df['mes'].map(mapa_meses)
        ordem = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
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
    st.markdown("### ⚙️ Parâmetros")
    if not df_base.empty:
        meses_selecionados = st.multiselect("Período:", df_base['Mês'].unique(), default=df_base['Mês'].unique())
        gasto_range = (float(df_base['Gasto'].min()), float(df_base['Gasto'].max()))
        filtro_gasto = st.slider("Investimento (R$):", gasto_range[0], gasto_range[1], gasto_range)
        filtro_eficiencia = st.slider("Eficiência (R$/KM):", 0.0, float(df_base['Custo/KM'].max()), float(df_base['Custo/KM'].max()))

# --- 4. Interface ---
if not df_base.empty:
    df_filtrado = df_base[(df_base['Mês'].isin(meses_selecionados)) & (df_base['Gasto'].between(filtro_gasto[0], filtro_gasto[1])) & (df_base['Custo/KM'] <= filtro_eficiencia)]
    
    aba1, aba2 = st.tabs(["📊 Dashboards", "🧠 Diagnóstico"])
    axis_config = alt.Axis(labelColor=COR_TEXTO_SUAVE, titleColor=COR_TEXTO_SUAVE, gridDash=[2,2], domain=False, ticks=False)

    with aba1:
        st.markdown(f"<h2 style='color:{COR_SECUNDARIA};'>Visão Consolidada</h2>", unsafe_allow_html=True)
        if not df_filtrado.empty:
            mes_foco = st.selectbox("Destaque Mensal:", df_filtrado['Mês'].unique())
            dados_foco = df_filtrado[df_filtrado['Mês'] == mes_foco].iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(f"Custos em {mes_foco}", f"R$ {dados_foco['Gasto']:,.2f}")
            c2.metric(f"KM em {mes_foco}", f"{dados_foco['KM']:,.0f}".replace(',', '.'))
            c3.metric(f"Eficiência em {mes_foco}", f"R$ {dados_foco['Custo/KM']:.3f}")
            c4.metric("Total Acumulado", f"R$ {df_filtrado['Gasto'].sum():,.2f}")

            col_esq, col_dir = st.columns(2)
            with col_esq:
                st.markdown('<div class="chart-container"><b>EVOLUÇÃO DOS CUSTOS (R$)</b>', unsafe_allow_html=True)
                area = alt.Chart(df_filtrado).mark_area(line={'color':COR_PRIMARIA}, color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color=COR_PRIMARIA, offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0), interpolate='monotone').encode(x=alt.X('Mês', title=None, axis=alt.Axis(labelAngle=-45)), y=alt.Y('Gasto', title=None, axis=axis_config))
                st.altair_chart(area.properties(height=300).configure_view(strokeOpacity=0), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_dir:
                st.markdown('<div class="chart-container"><b>VOLUME DE RODAGEM</b>', unsafe_allow_html=True)
                bar = alt.Chart(df_filtrado).mark_bar(color=COR_PRIMARIA, cornerRadiusTopLeft=6, size=35).encode(x=alt.X('Mês', title=None, axis=alt.Axis(labelAngle=-45)), y=alt.Y('KM', title=None, axis=axis_config))
                st.altair_chart(bar.properties(height=300).configure_view(strokeOpacity=0), use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="chart-container"><b>DETALHAMENTO</b>', unsafe_allow_html=True)
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with aba2:
        st.markdown(f"<h2 style='color:{COR_SECUNDARIA};'>Análise de Meta</h2>", unsafe_allow_html=True)
        mes_diag = st.selectbox("Auditar Período:", df_base['Mês'].unique())
        media_anual = df_base['Gasto'].mean()
        dados_mes = df_base[df_base['Mês'] == mes_diag].iloc[0]
        desvio = ((dados_mes['Gasto'] - media_anual) / media_anual) * 100

        diag1, diag2, diag3 = st.columns(3)
        diag1.metric(f"Gasto: {mes_diag}", f"R$ {dados_mes['Gasto']:,.2f}", f"{desvio:.1f}% vs meta", delta_color="inverse")
        diag2.metric("Meta (Média Anual)", f"R$ {media_anual:,.2f}")
        diag3.metric("Status", "⚠️ ACIMA" if desvio > 0 else "✅ SOB CONTROLE")

        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        diag_chart = alt.Chart(df_base).mark_bar().encode(x=alt.X('Mês', title=None, axis=alt.Axis(labelAngle=-45)), y=alt.Y('Gasto', title=None, axis=axis_config), color=alt.condition(alt.datum.Mês == mes_diag, alt.value(COR_PRIMARIA), alt.value('#e2e8f0')))
        linha_ref = alt.Chart(pd.DataFrame({'y': [media_anual]})).mark_rule(color='#ef4444', strokeDash=[4,4], size=2).encode(y='y')
        
        # AQUI ESTÁ A CORREÇÃO: configure_view() aplicada ao resultado da soma
        st.altair_chart((diag_chart + linha_ref).properties(height=350).configure_view(strokeOpacity=0), use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if desvio > 10:
            st.markdown(f'<div class="alert-error">🚨 O mês de <b>{mes_diag}</b> superou a meta em {desvio:.1f}%.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert-success">✅ <b>Excelente!</b> {mes_diag} operou dentro da meta.</div>', unsafe_allow_html=True)