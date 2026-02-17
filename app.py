import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

# --- 0. CONFIGURAÇÃO ESSENCIAL DO ALTAIR ---
# Isso força os gráficos a serem CLAROS, resolvendo o fundo preto.
alt.themes.enable("default")

# --- 1. Configuração e Identidade Visual (Paleta Suavizada Premium) ---
COR_PRIMARIA = "#10b981"   # Verde Esmeralda
COR_SECUNDARIA = "#334155" # Slate Gray (Texto Forte)
COR_TEXTO_SUAVE = "#64748b" # Cinza Azulado (Texto Secundário/Eixos)
COR_FUNDO_PAGINA = "#eef2f6" # Cinza Off-White (Mais encorpado que o anterior)
COR_CARD = "#ffffff"       # Branco Puro

st.set_page_config(page_title="Frota BI | Gestão Estratégica", page_icon="🚛", layout="wide")

# CSS Repaginado para equilíbrio visual
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {{ 
            font-family: 'Inter', sans-serif; 
            color: {COR_SECUNDARIA}; 
        }}
        
        /* Fundo da Página Off-White (Mais suave aos olhos) */
        .stApp {{ 
            background-color: {COR_FUNDO_PAGINA}; 
        }}

        /* Abas Modernas */
        .stTabs [data-baseweb="tab"] {{
            height: 45px;
            background-color: transparent;
            padding: 10px 25px;
            color: {COR_TEXTO_SUAVE} !important;
            font-weight: 500;
            border: none;
        }}
        .stTabs [aria-selected="true"] {{
            color: {COR_PRIMARIA} !important;
            border-bottom: 3px solid {COR_PRIMARIA} !important;
            font-weight: 700;
            background-color: transparent !important;
        }}

        /* Cards Elevados (Fundo Branco no Fundo Cinza) */
        .chart-container {{
            background-color: {COR_CARD};
            padding: 24px;
            border-radius: 16px;
            border: 1px solid #e2e8f0;
            /* Sombra mais difusa para efeito premium */
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.03), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
            margin-bottom: 24px;
        }}

        /* Métricas Minimalistas */
        div[data-testid="stMetric"] {{
            background-color: {COR_CARD} !important;
            border: 1px solid #e2e8f0;
            padding: 1.5rem;
            border-radius: 16px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02);
            text-align: left;
        }}
        [data-testid="stMetricLabel"] p {{ color: {COR_TEXTO_SUAVE} !important; font-size: 0.95rem !important; font-weight: 600 !important; }}
        [data-testid="stMetricValue"] div {{ color: {COR_SECUNDARIA} !important; font-size: 1.8rem !important; font-weight: 700 !important; }}

        /* Alertas com escrita preta */
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
        
        mapa_meses = {
            'Jan': 'Janeiro', 'Fev': 'Fevereiro', 'Mar': 'Março', 'Abr': 'Abril',
            'Mai': 'Maio', 'Jun': 'Junho', 'Jul': 'Julho', 'Ago': 'Agosto',
            'Set': 'Setembro', 'Out': 'Outubro', 'Nov': 'Novembro', 'Dez': 'Dezembro'
        }
        
        if df['mes'].iloc[0] in mapa_meses:
            df['mes'] = df['mes'].map(mapa_meses)
            
        ordem_completa = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                         'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        
        df['mes'] = pd.Categorical(df['mes'], categories=ordem_completa, ordered=True)
        df = df.sort_values('mes').rename(columns={'mes': 'Mês', 'gasto_real': 'Gasto', 'km_rodado': 'KM'})
        df['Custo/KM'] = df['Gasto'] / df['KM']
        return df
    except Exception as e:
        st.error(f"Erro: {e}")
        return pd.DataFrame()

df_base = carregar_dados_sql()

# --- 3. Sidebar Repaginada ---
with st.sidebar:
    st.markdown(f"### ⚙️ Parâmetros de Filtro")
    st.divider()
    if not df_base.empty:
        meses_selecionados = st.multiselect("Gráficos por Período:", df_base['Mês'].unique(), default=df_base['Mês'].unique())
        gasto_min, gasto_max = float(df_base['Gasto'].min()), float(df_base['Gasto'].max())
        filtro_gasto = st.slider("Investimento (R$):", gasto_min, gasto_max, (gasto_min, gasto_max))
        custo_km_max = float(df_base['Custo/KM'].max())
        filtro_eficiencia = st.slider("Eficiência Máxima (R$/KM):", 0.0, custo_km_max, custo_km_max)
    st.caption(f"Gabriel Barbosa | ADS")

# --- 4. Interface Principal ---
if not df_base.empty:
    mask = (df_base['Mês'].isin(meses_selecionados)) & (df_base['Gasto'].between(filtro_gasto[0], filtro_gasto[1])) & (df_base['Custo/KM'] <= filtro_eficiencia)
    df_filtrado = df_base[mask]

    aba1, aba2 = st.tabs(["📊 Dashboards Operacionais", "🧠 Diagnóstico Estratégico"])

    # Configuração comum para eixos dos gráficos (Cinza suave)
    axis_config = alt.Axis(labelColor=COR_TEXTO_SUAVE, titleColor=COR_TEXTO_SUAVE, gridColor='#e2e8f0', domainColor='#e2e8f0', tickColor='#e2e8f0')

    with aba1:
        st.markdown(f"<h2 style='color:{COR_SECUNDARIA}; margin-top:0; font-weight:700;'>Visão Consolidada</h2>", unsafe_allow_html=True)
        
        if df_filtrado.empty:
            st.warning("Ajuste os filtros para visualizar os dados.")
        else:
            mes_foco = st.selectbox("Destaque Mensal:", df_filtrado['Mês'].unique(), key="foco_geral")
            dados_foco = df_filtrado[df_filtrado['Mês'] == mes_foco].iloc[0]
            
            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(f"Custos em {mes_foco}", f"R$ {dados_foco['Gasto']:,.2f}")
            c2.metric(f"KM em {mes_foco}", f"{dados_foco['KM']:,.0f}".replace(',', '.'))
            c3.metric(f"Eficiência em {mes_foco}", f"R$ {dados_foco['Custo/KM']:.3f}")
            c4.metric("Gasto Total Acumulado", f"R$ {df_filtrado['Gasto'].sum():,.2f}")

            col_esq, col_dir = st.columns(2)
            with col_esq:
                st.markdown(f'<div class="chart-container"><b style="color:{COR_SECUNDARIA}; font-size:14px;">EVOLUÇÃO DOS CUSTOS TOTAIS</b>', unsafe_allow_html=True)
                chart_area = alt.Chart(df_filtrado).mark_area(
                    line={'color':COR_PRIMARIA, 'strokeWidth':3},
                    color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color=COR_PRIMARIA, offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0),
                    interpolate='monotone'
                ).encode(
                    x=alt.X('Mês', title=None, axis=axis_config),
                    y=alt.Y('Gasto', title=None, axis=alt.Axis(format=',.0f', grid=True, gridDash=[2,2], labelPadding=10, domain=False, ticks=False, labelColor=COR_TEXTO_SUAVE, gridColor='#e2e8f0'))
                ).configure_view(strokeOpacity=0).properties(height=300)
                st.altair_chart(chart_area, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_dir:
                st.markdown(f'<div class="chart-container"><b style="color:{COR_SECUNDARIA}; font-size:14px;">VOLUME DE RODAGEM MENSAL</b>', unsafe_allow_html=True)
                chart_bar = alt.Chart(df_filtrado).mark_bar(
                    color=COR_PRIMARIA, cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=35
                ).encode(
                    x=alt.X('Mês', title=None, axis=axis_config),
                    y=alt.Y('KM', title=None, axis=alt.Axis(format=',.0f', grid=True, gridDash=[2,2], labelPadding=10, domain=False, ticks=False, labelColor=COR_TEXTO_SUAVE, gridColor='#e2e8f0'))
                ).configure_view(strokeOpacity=0).properties(height=300)
                st.altair_chart(chart_bar, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown(f'<div class="chart-container"><b style="color:{COR_SECUNDARIA}; font-size:14px;">DETALHAMENTO TÉCNICO DOS REGISTROS</b>', unsafe_allow_html=True)
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True, column_config={
                "Gasto": st.column_config.NumberColumn("Gasto Real", format="R$ %.2f"),
                "KM": st.column_config.NumberColumn("KM Rodados", format="%d km"),
                "Custo/KM": st.column_config.NumberColumn("Eficiência (R$/KM)", format="R$ %.3f")
            })
            st.markdown('</div>', unsafe_allow_html=True)

    with aba2:
        st.markdown(f"<h2 style='color:{COR_SECUNDARIA}; margin-top:0; font-weight:700;'>Análise de Meta vs Realizado</h2>", unsafe_allow_html=True)
        mes_diagnostico = st.selectbox("Auditar Período:", df_base['Mês'].unique(), key="foco_diag")
        
        media_anual = df_base['Gasto'].mean()
        dados_mes = df_base[df_base['Mês'] == mes_diagnostico].iloc[0]
        desvio = ((dados_mes['Gasto'] - media_anual) / media_anual) * 100

        diag1, diag2, diag3 = st.columns(3)
        diag1.metric(f"Investimento: {mes_diagnostico}", f"R$ {dados_mes['Gasto']:,.2f}", f"{desvio:.1f}% vs meta", delta_color="inverse")
        diag2.metric("Meta de Controle (Média)", f"R$ {media_anual:,.2f}")
        status = "⚠️ ACIMA DA META" if desvio > 0 else "✅ SOB CONTROLE"
        diag3.metric("Status Operacional", status)

        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        diag_chart = alt.Chart(df_base).mark_bar().encode(
            x=alt.X('Mês', title=None, axis=axis_config),
            y=alt.Y('Gasto', title=None, axis=alt.Axis(gridDash=[2,2], domain=False, ticks=False, labelColor=COR_TEXTO_SUAVE, gridColor='#e2e8f0')),
            color=alt.condition(alt.datum.Mês == mes_diagnostico, alt.value(COR_PRIMARIA), alt.value('#e2e8f0'))
        ).configure_view(strokeOpacity=0).properties(height=350)
        
        linha_ref = alt.Chart(pd.DataFrame({'y': [media_anual]})).mark_rule(color='#ef4444', strokeDash=[4,4], size=2).encode(y='y')
        st.altair_chart(diag_chart + linha_ref, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if desvio > 10:
            st.markdown(f'<div class="alert-error">🚨 O mês de <b>{mes_diagnostico}</b> superou a meta de controle em {desvio:.1f}%. Verifique manutenções corretivas.</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alert-success">✅ <b>Excelente!</b> {mes_diagnostico} operou dentro ou abaixo da meta ({abs(desvio):.1f}% de economia).</div>', unsafe_allow_html=True)
else:
    st.info("Conectando aos dados...")