import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

# --- 0. CONFIGURAÇÃO GLOBAL ---
alt.themes.enable("default") 

# --- 1. IDENTIDADE VISUAL & CORES ---
COR_PRIMARIA = "#10b981"   
COR_SECUNDARIA = "#1e293b" # Azul Marinho
COR_TEXTO_SUAVE = "#64748b" 
COR_FUNDO_PAGINA = "#eef2f6" 
COR_CARD = "#ffffff"       

st.set_page_config(page_title="Frota BI | Gestão Estratégica", page_icon="🚛", layout="wide")

# CSS Avançado: Transforma o container nativo do Streamlit em um Card Customizado
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {{ 
            font-family: 'Inter', sans-serif; 
            color: {COR_SECUNDARIA} !important; 
        }}
        
        .stApp {{ background-color: {COR_FUNDO_PAGINA}; }}
        
        /* Abas */
        .stTabs [data-baseweb="tab"] {{ height: 45px; color: {COR_TEXTO_SUAVE} !important; font-weight: 500; }}
        .stTabs [aria-selected="true"] {{ color: {COR_PRIMARIA} !important; border-bottom: 3px solid {COR_PRIMARIA} !important; font-weight: 700; }}

        /* ESTILIZAÇÃO DOS CARDS (Containers nativos) */
        [data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: {COR_CARD} !important;
            border: 1px solid #e2e8f0 !important;
            border-radius: 16px !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.03) !important;
            padding: 24px !important;
            margin-bottom: 24px !important;
        }}
        
        /* Métricas */
        div[data-testid="stMetric"] {{ background-color: {COR_CARD} !important; border: 1px solid #e2e8f0; padding: 1.5rem; border-radius: 16px; text-align: left; }}
        [data-testid="stMetricLabel"] p {{ color: {COR_TEXTO_SUAVE} !important; font-size: 0.95rem !important; font-weight: 600 !important; }}
        [data-testid="stMetricValue"] div {{ color: {COR_SECUNDARIA} !important; font-size: 1.8rem !important; font-weight: 700 !important; }}

        /* Alertas Customizados (Escrita Preta) */
        .alert-box {{ padding: 1rem; border-radius: 12px; margin-bottom: 1rem; font-weight: 500; color: #000000 !important; border-left: 6px solid; }}
        .alert-success {{ background-color: #dcfce7; border-left-color: #22c55e; }}
        .alert-warning {{ background-color: #fef3c7; border-left-color: #f59e0b; }}
        .alert-error {{ background-color: #fee2e2; border-left-color: #ef4444; }}

        #MainMenu, footer, header {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÕES DE DADOS (Tratamento Robusto) ---
@st.cache_data
def carregar_dados():
    try:
        conn = sqlite3.connect('manutencao.db')
        df = pd.read_sql("SELECT mes, gasto_real, km_rodado FROM custos_frota", conn)
        conn.close()
        
        mapa = {'Jan':'Janeiro','Fev':'Fevereiro','Mar':'Março','Abr':'Abril','Mai':'Maio','Jun':'Junho','Jul':'Julho','Ago':'Agosto','Set':'Setembro','Out':'Outubro','Nov':'Novembro','Dez':'Dezembro'}
        
        # Garante a conversão de todos os meses, não apenas o primeiro
        df['mes'] = df['mes'].replace(mapa)
        
        ordem = ['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
        df['mes'] = pd.Categorical(df['mes'], categories=ordem, ordered=True)
        df = df.sort_values('mes').rename(columns={'mes': 'Mês', 'gasto_real': 'Gasto', 'km_rodado': 'KM'})
        df['Custo/KM'] = df['Gasto'] / df['KM']
        return df
    except Exception as e:
        st.error(f"Erro nos dados: {e}")
        return pd.DataFrame()

df_base = carregar_dados()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.markdown(f"### <span style='color:white'>⚙️ Parâmetros</span>", unsafe_allow_html=True)
    if not df_base.empty:
        meses_sel = st.multiselect("Filtrar Período:", df_base['Mês'].unique(), default=df_base['Mês'].unique())
        g_min, g_max = float(df_base['Gasto'].min()), float(df_base['Gasto'].max())
        filtro_gasto = st.slider("Investimento (R$):", g_min, g_max, (g_min, g_max))
        filtro_ef = st.slider("Custo Máximo por KM:", 0.0, float(df_base['Custo/KM'].max()), float(df_base['Custo/KM'].max()))
    st.caption("Gabriel Barbosa | Analista Administrativo")

# --- 4. INTERFACE ---
if not df_base.empty:
    mask = (df_base['Mês'].isin(meses_sel)) & (df_base['Gasto'].between(filtro_gasto[0], filtro_gasto[1])) & (df_base['Custo/KM'] <= filtro_ef)
    df_filtrado = df_base[mask]
    
    aba1, aba2 = st.tabs(["📊 Dashboards Operacionais", "🧠 Diagnóstico Estratégico"])
    axis_config = alt.Axis(labelColor=COR_TEXTO_SUAVE, titleColor=COR_TEXTO_SUAVE, gridDash=[2,2], domain=False, ticks=False, labelAngle=-45)

    with aba1:
        st.markdown(f"<h2 style='color:{COR_SECUNDARIA}; font-weight:700;'>Visão Consolidada</h2>", unsafe_allow_html=True)
        if not df_filtrado.empty:
            mes_foco = st.selectbox("Destaque Mensal:", df_filtrado['Mês'].unique())
            df_foco = df_filtrado[df_filtrado['Mês'] == mes_foco].iloc[0]
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(f"Custos em {mes_foco}", f"R$ {df_foco['Gasto']:,.2f}")
            c2.metric(f"KM em {mes_foco}", f"{df_foco['KM']:,.0f}".replace(',', '.'))
            c3.metric(f"Eficiência em {mes_foco}", f"R$ {df_foco['Custo/KM']:.3f}")
            c4.metric("Total Acumulado", f"R$ {df_filtrado['Gasto'].sum():,.2f}")

            col_esq, col_dir = st.columns(2)
            with col_esq:
                with st.container(border=True): # O Título agora fica preso aqui dentro
                    st.markdown(f'<b style="color:{COR_SECUNDARIA};">EVOLUÇÃO DOS CUSTOS TOTAIS</b>', unsafe_allow_html=True)
                    area = alt.Chart(df_filtrado).mark_area(line={'color':COR_PRIMARIA, 'strokeWidth':3}, color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color=COR_PRIMARIA, offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0), interpolate='monotone').encode(x=alt.X('Mês', title=None, axis=axis_config), y=alt.Y('Gasto', title=None, axis=axis_config))
                    st.altair_chart(area.properties(height=300).configure_view(strokeOpacity=0), use_container_width=True)
            
            with col_dir:
                with st.container(border=True):
                    st.markdown(f'<b style="color:{COR_SECUNDARIA};">VOLUME DE RODAGEM MENSAL</b>', unsafe_allow_html=True)
                    bar = alt.Chart(df_filtrado).mark_bar(color=COR_PRIMARIA, cornerRadiusTopLeft=6, size=35).encode(x=alt.X('Mês', title=None, axis=axis_config), y=alt.Y('KM', title=None, axis=axis_config))
                    st.altair_chart(bar.properties(height=300).configure_view(strokeOpacity=0), use_container_width=True)

            with st.container(border=True):
                st.markdown(f'<b style="color:{COR_SECUNDARIA};">DETALHAMENTO TÉCNICO DOS REGISTROS</b>', unsafe_allow_html=True)
                st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

    with aba2:
        st.markdown(f"<h2 style='color:{COR_SECUNDARIA}; font-weight:700;'>Análise de Meta vs Realizado</h2>", unsafe_allow_html=True)
        mes_diag = st.selectbox("Auditar Período:", df_base['Mês'].unique(), key="diag_box")
        media_anual = df_base['Gasto'].mean()
        dados_mes = df_base[df_base['Mês'] == mes_diag].iloc[0]
        desvio = ((dados_mes['Gasto'] - media_anual) / media_anual) * 100

        diag1, diag2, diag3 = st.columns(3)
        diag1.metric(f"Investimento: {mes_diag}", f"R$ {dados_mes['Gasto']:,.2f}", f"{desvio:.1f}% vs meta", delta_color="inverse")
        diag2.metric("Meta de Controle (Média)", f"R$ {media_anual:,.2f}")
        status = "⚠️ ACIMA" if desvio > 0 else "✅ SOB CONTROLE"
        diag3.metric("Status Operacional", status)

        with st.container(border=True): # RESOLVE O TÍTULO FORA DO ENQUADRAMENTO
            st.markdown(f"<b style='color:{COR_SECUNDARIA};'>COMPARATIVO MENSAL VS META</b>", unsafe_allow_html=True)
            diag_c = alt.Chart(df_base).mark_bar().encode(x=alt.X('Mês', title=None, axis=axis_config), y=alt.Y('Gasto', title=None, axis=axis_config), color=alt.condition(alt.datum.Mês == mes_diag, alt.value(COR_PRIMARIA), alt.value('#e2e8f0')))
            linha = alt.Chart(pd.DataFrame({'y': [media_anual]})).mark_rule(color='#ef4444', strokeDash=[4,4], size=2).encode(y='y')
            # A configuração de view deve ser no gráfico final (unificado)
            st.altair_chart((diag_c + linha).properties(height=350).configure_view(strokeOpacity=0), use_container_width=True)
        
        # Lógica de Diagnóstico Corrigida (3 Níveis)
        if desvio > 10:
            st.markdown(f'<div class="alert-box alert-error">🚨 <b>ALERTA CRÍTICO:</b> {mes_diag} superou a meta em {desvio:.1f}%. Verifique manutenções.</div>', unsafe_allow_html=True)
        elif desvio > 0:
            st.markdown(f'<div class="alert-box alert-warning">⚠️ <b>ATENÇÃO:</b> {mes_diag} operou {desvio:.1f}% acima da meta. Custo fora do planejado.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert-box alert-success">✅ <b>DENTRO DA META:</b> {mes_diag} operou com economia de {abs(desvio):.1f}%. Excelente!</div>', unsafe_allow_html=True)
else:
    st.info("Conectando aos dados...")