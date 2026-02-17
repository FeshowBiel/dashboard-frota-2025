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

        .chart-container {{
            background-color: #ffffff;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }}
        
        /* Estilização Customizada para Alertas com Texto Preto */
        .alert-success {{
            background-color: #dcfce7;
            padding: 1rem;
            border-radius: 8px;
            border-left: 5px solid #22c55e;
            color: black !important;
            margin-bottom: 1rem;
        }}
        .alert-error {{
            background-color: #fee2e2;
            padding: 1rem;
            border-radius: 8px;
            border-left: 5px solid #ef4444;
            color: black !important;
            margin-bottom: 1rem;
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
        
        # Mapeamento de Meses para Nomes Completos
        mapa_meses = {
            'Jan': 'Janeiro', 'Fev': 'Fevereiro', 'Mar': 'Março', 'Abr': 'Abril',
            'Mai': 'Maio', 'Jun': 'Junho', 'Jul': 'Julho', 'Ago': 'Agosto',
            'Set': 'Setembro', 'Out': 'Outubro', 'Nov': 'Novembro', 'Dez': 'Dezembro'
        }
        
        # Converte se os dados estiverem abreviados
        if df['mes'].iloc[0] in mapa_meses:
            df['mes'] = df['mes'].map(mapa_meses)
            
        ordem_completa = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                         'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        
        df['mes'] = pd.Categorical(df['mes'], categories=ordem_completa, ordered=True)
        df = df.sort_values('mes').rename(columns={'mes': 'Mês', 'gasto_real': 'Gasto', 'km_rodado': 'KM'})
        df['Custo/KM'] = df['Gasto'] / df['KM']
        return df
    except Exception as e:
        st.error(f"Erro ao carregar banco: {e}")
        return pd.DataFrame()

df_base = carregar_dados_sql()

# --- 3. Sidebar com Filtros de Performance ---
with st.sidebar:
    st.markdown(f"### ⚙️ Filtros de Tendência")
    st.divider()
    
    if not df_base.empty:
        meses_selecionados = st.multiselect("Filtrar Período dos Gráficos:", df_base['Mês'].unique(), default=df_base['Mês'].unique())
        
        gasto_min, gasto_max = float(df_base['Gasto'].min()), float(df_base['Gasto'].max())
        filtro_gasto = st.slider("Faixa de Investimento (R$):", gasto_min, gasto_max, (gasto_min, gasto_max))
        
        custo_km_max = float(df_base['Custo/KM'].max())
        filtro_eficiencia = st.slider("Limite de Custo por KM (R$):", 0.0, custo_km_max, custo_km_max)
        
        st.divider()
        if st.button("Resetar Filtros"):
            st.rerun()

    st.caption(f"Painel de Gestão de Frota")

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

    with aba1:
        st.markdown(f"<h2 style='color:{COR_SECUNDARIA}; margin-top:0;'>Dashboard Estratégico</h2>", unsafe_allow_html=True)
        
        if df_filtrado.empty:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
        else:
            mes_foco = st.selectbox("Selecione o Mês para Foco nos Indicadores:", df_filtrado['Mês'].unique(), key="foco_geral")
            dados_foco = df_filtrado[df_filtrado['Mês'] == mes_foco].iloc[0]
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric(f"Gasto em {mes_foco}", f"R$ {dados_foco['Gasto']:,.2f}")
            c2.metric(f"KM em {mes_foco}", f"{dados_foco['KM']:,.0f}".replace(',', '.'))
            c3.metric(f"Eficiência em {mes_foco}", f"R$ {dados_foco['Custo/KM']:.3f}")
            c4.metric("Gasto Total (Período)", f"R$ {df_filtrado['Gasto'].sum():,.2f}")

            col_esq, col_dir = st.columns(2)
            with col_esq:
                st.markdown('<div class="chart-container"><b style="color:#1e293b">Evolução de Custos (R$)</b>', unsafe_allow_html=True)
                chart_area = alt.Chart(df_filtrado).mark_area(line={'color':COR_PRIMARIA}, color=alt.Gradient(gradient='linear', stops=[alt.GradientStop(color=COR_PRIMARIA, offset=0), alt.GradientStop(color='white', offset=1)], x1=1, x2=1, y1=1, y2=0), interpolate='monotone').encode(x=alt.X('Mês', title=None, axis=alt.Axis(labelAngle=-45)), y=alt.Y('Gasto', title=None, axis=alt.Axis(format=',.0f', grid=True, labelPadding=10))).properties(height=300)
                st.altair_chart(chart_area, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col_dir:
                st.markdown('<div class="chart-container"><b style="color:#1e293b">Volume de Quilometragem</b>', unsafe_allow_html=True)
                chart_bar = alt.Chart(df_filtrado).mark_bar(color=COR_PRIMARIA, cornerRadiusTopLeft=6, cornerRadiusTopRight=6, size=35).encode(x=alt.X('Mês', title=None, axis=alt.Axis(labelAngle=-45)), y=alt.Y('KM', title=None, axis=alt.Axis(format=',.0f', grid=True, labelPadding=10))).properties(height=300)
                st.altair_chart(chart_bar, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="chart-container"><b style="color:#1e293b">Dados Consolidados</b>', unsafe_allow_html=True)
            st.dataframe(df_filtrado, use_container_width=True, hide_index=True, column_config={
                "Gasto": st.column_config.ProgressColumn("Gasto", format="R$ %.2f", min_value=0, max_value=df_base['Gasto'].max()),
                "Custo/KM": st.column_config.NumberColumn("R$/KM", format="R$ %.3f")
            })
            st.markdown('</div>', unsafe_allow_html=True)

    with aba2:
        st.markdown(f"<h2 style='color:{COR_SECUNDARIA}; margin-top:0;'>Análise de Desvio e Controle</h2>", unsafe_allow_html=True)
        mes_diagnostico = st.selectbox("Escolha o mês para auditoria:", df_base['Mês'].unique(), key="foco_diag")
        
        media_anual = df_base['Gasto'].mean()
        dados_mes = df_base[df_base['Mês'] == mes_diagnostico].iloc[0]
        desvio = ((dados_mes['Gasto'] - media_anual) / media_anual) * 100

        diag1, diag2, diag3 = st.columns(3)
        diag1.metric(f"Gasto em {mes_diagnostico}", f"R$ {dados_mes['Gasto']:,.2f}", f"{desvio:.1f}% vs meta", delta_color="inverse")
        diag2.metric("Meta de Controle (Média)", f"R$ {media_anual:,.2f}")
        status = "⚠️ ACIMA DA META" if desvio > 0 else "✅ DENTRO DA META"
        diag3.metric("Status Operacional", status)

        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        diag_chart = alt.Chart(df_base).mark_bar().encode(
            x=alt.X('Mês', title=None, axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('Gasto', title=None),
            color=alt.condition(alt.datum.Mês == mes_diagnostico, alt.value(COR_PRIMARIA), alt.value('#e2e8f0')),
            tooltip=['Mês', alt.Tooltip('Gasto', format='$,.2f')]
        ).properties(height=350)
        
        linha_ref = alt.Chart(pd.DataFrame({'y': [media_anual]})).mark_rule(color='#ef4444', strokeDash=[5,5], size=2).encode(y='y')
        st.altair_chart(diag_chart + linha_ref, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Mensagens de Diagnóstico com Escrita Preta
        if desvio > 10:
            st.markdown(f"""
                <div class="alert-error">
                    🚨 O mês de <b>{mes_diagnostico}</b> superou a meta de controle. Recomenda-se auditoria nas despesas.
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="alert-success">
                    ✅ <b>Excelente!</b> {mes_diagnostico} operou dentro ou abaixo da meta estabelecida.
                </div>
            """, unsafe_allow_html=True)

else:
    st.info("Aguardando dados...")