import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

# --- 1. Configuração de Identidade Visual ---
COR_PRIMARIA = "#10b981"  # Verde (Sucesso)
COR_SECUNDARIA = "#1e293b" # Azul Marinho (Sobriedade)
COR_ALERTA = "#ef4444"    # Vermelho (Atenção)

st.set_page_config(page_title="BI Inteligente | Gestão de Frota", page_icon="🧠", layout="wide")

# CSS para Layout de Software e Estilização de Alertas
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
        .stApp {{ background-color: #f8fafc; }}
        [data-testid="stSidebar"] {{ background-color: {COR_SECUNDARIA}; }}
        [data-testid="stSidebar"] * {{ color: #e2e8f0 !important; }}
        .chart-container {{
            background-color: #ffffff;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }}
        .main-header {{
            background: linear-gradient(90deg, {COR_SECUNDARIA} 0%, {COR_PRIMARIA} 100%);
            padding: 2rem;
            border-radius: 12px;
            color: white;
            margin-bottom: 2rem;
        }}
        #MainMenu, footer, header {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. Processamento de Dados Inteligente ---
@st.cache_data
def carregar_dados_sql():
    try:
        conn = sqlite3.connect('manutencao.db')
        df = pd.read_sql("SELECT mes, gasto_real, km_rodado FROM custos_frota", conn)
        conn.close()
        ordem = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        df['mes'] = pd.Categorical(df['mes'], categories=ordem, ordered=True)
        df = df.sort_values('mes').rename(columns={'mes': 'Mês', 'gasto_real': 'Gasto', 'km_rodado': 'KM'})
        return df
    except Exception as e:
        st.error(f"Erro ao acessar dados: {e}")
        return pd.DataFrame()

df_base = carregar_dados_sql()

# --- 3. Filtros e Inteligência ---
with st.sidebar:
    st.markdown("### 📊 Inteligência Analítica")
    mes_analise = st.selectbox("Selecione o Mês para Diagnóstico:", df_base['Mês'].unique())
    st.divider()
    st.caption("Gabriel Barbosa | Analista Administrativo") #

if not df_base.empty:
    # CÁLCULOS DE INTELIGÊNCIA
    media_gasto_anual = df_base['Gasto'].mean()
    media_km_anual = df_base['KM'].mean()
    
    # Dados do mês selecionado
    dados_mes = df_base[df_base['Mês'] == mes_analise].iloc[0]
    gasto_mes = dados_mes['Gasto']
    km_mes = dados_mes['KM']
    
    # Cálculo de Desvio (A inteligência do Dashboard)
    desvio_gasto = ((gasto_mes - media_gasto_anual) / media_gasto_anual) * 100

    # --- 4. Interface ---
    st.markdown(f"""
        <div class="main-header">
            <h1 style='margin:0;'>Diagnóstico de Performance: {mes_analise}</h1>
            <p style='margin:0; opacity:0.8;'>Comparativo automático contra a média anual de 2025</p>
        </div>
    """, unsafe_allow_html=True)

    # Métricas com Deltas Inteligentes
    c1, c2, c3 = st.columns(3)
    
    c1.metric(
        label="Gasto no Mês", 
        value=f"R$ {gasto_mes:,.2f}", 
        delta=f"{desvio_gasto:.1f}% vs média", 
        delta_color="inverse" # Vermelho se subir, verde se descer
    )
    
    c2.metric(
        label="Média Anual de Referência", 
        value=f"R$ {media_gasto_anual:,.2f}"
    )
    
    status = "ACIMA DA MÉDIA" if desvio_gasto > 0 else "DENTRO DA META"
    c3.metric(label="Status Operacional", value=status)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gráfico de Apoio Visual
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown(f"<b>Comparativo de Gastos Mensais vs Média (R$)</b>", unsafe_allow_html=True)
    
    # Gráfico que destaca o mês selecionado
    chart = alt.Chart(df_base).mark_bar().encode(
        x=alt.X('Mês', title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Gasto', title=None),
        color=alt.condition(
            alt.datum.Mês == mes_analise,
            alt.value(COR_PRIMARIA), # Cor de destaque
            alt.value('#cbd5e1')      # Cor neutra para os outros
        ),
        tooltip=['Mês', 'Gasto']
    ).properties(height=350)
    
    # Linha da Média (Referência Visual)
    linha_media = alt.Chart(pd.DataFrame({'y': [media_gasto_anual]})).mark_rule(
        color=COR_ALERTA, 
        strokeDash=[5,5],
        size=2
    ).encode(y='y')

    st.altair_chart(chart + linha_media, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Insights Automáticos
    if desvio_gasto > 10:
        st.error(f"🚨 **Atenção:** O gasto de {mes_analise} está significativamente acima da média (↑{desvio_gasto:.1f}%). Recomenda-se revisar as ordens de serviço deste período.")
    elif desvio_gasto < -10:
        st.success(f"✅ **Excelente:** O mês de {mes_analise} apresentou uma economia de {abs(desvio_gasto):.1f}% em relação à média anual.")
    else:
        st.info(f"ℹ️ **Estabilidade:** Os gastos de {mes_analise} estão alinhados com a média operacional esperada.")

else:
    st.warning("Aguardando conexão com o banco de dados...")
    