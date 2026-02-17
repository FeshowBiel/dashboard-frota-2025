import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

# --- 1. Configuração da Página ---
st.set_page_config(
    page_title="Gestão de Frota | BI Pro",
    page_icon="🚛",
    layout="wide"
)

# Cores Corporativas (Harmonia Emerald & Slate)
COR_PRIMARIA = "#10b981"  # Verde Esmeralda
COR_SECUNDARIA = "#1e293b" # Azul Escuro
COR_TEXTO = "#334155" # Cinza Azulado
FUNDO_GRAFICO = "#ffffff"

# --- 2. CSS Avançado ---
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
        
        html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
        .stApp {{ background-color: #f8fafc; }}

        /* Sidebar */
        [data-testid="stSidebar"] {{
            background-color: {COR_SECUNDARIA};
            padding-top: 1rem;
        }}
        [data-testid="stSidebar"] * {{ color: #f1f5f9 !important; }}

        /* Containers */
        .chart-container {{
            background-color: #ffffff;
            padding: 25px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            margin-bottom: 20px;
        }}

        /* Cabeçalho */
        .app-header {{
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            border-left: 10px solid {COR_PRIMARIA};
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }}

        /* Métricas */
        div[data-testid="stMetric"] {{
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0;
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
        }}
        [data-testid="stMetricLabel"] p {{
            font-size: 1rem !important;
            color: #64748b !important; 
            font-weight: 600 !important;
        }}
        [data-testid="stMetricValue"] div {{
            font-size: 1.8rem !important;
            color: {COR_SECUNDARIA} !important;
            font-weight: 800 !important;
        }}

        #MainMenu, footer, header {{ visibility: hidden; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. Dados ---
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

# --- 4. Sidebar ---
with st.sidebar:
    st.markdown("### 🔍 Filtros")
    st.divider()
    if not df_base.empty:
        meses_filtro = st.multiselect("Período:", df_base['Mês'].unique(), default=df_base['Mês'].unique())
        st.divider()
        csv = df_base[df_base['Mês'].isin(meses_filtro)].to_csv(index=False).encode('utf-8')
        st.download_button("📥 Baixar CSV", data=csv, file_name='relatorio_2025.csv', mime='text/csv')
    st.caption("Gabriel Barbosa | Analista")

# --- 5. Interface Principal ---

st.markdown(f"""
    <div class="app-header">
        <h1 style='margin:0; font-size: 24px; color:{COR_SECUNDARIA};'>Relatório Executivo de Manutenção</h1>
        <p style='margin:0; color:#64748b; font-size:14px;'>Consolidado Anual 2025</p>
    </div>
""", unsafe_allow_html=True)

if not df_base.empty:
    df_filtrado = df_base[df_base['Mês'].isin(meses_filtro)]

    if not df_filtrado.empty:
        # Métricas
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Gasto Total", f"R$ {df_filtrado['Gasto'].sum():,.2f}")
        c2.metric("Eficiência Média", f"R$ {df_filtrado['Custo/KM'].mean():.3f}")
        c3.metric("KM Rodados", f"{df_filtrado['KM'].sum():,}".replace(',', '.'))
        c4.metric("Economia", "R$ 1.567.120,66")

        st.markdown("<br>", unsafe_allow_html=True)

        # SEÇÃO DE GRÁFICOS
        col_esq, col_dir = st.columns(2)

        with col_esq:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown(f"<b style='color:{COR_SECUNDARIA}; font-size:16px;'>Evolução de Custos (R$)</b>", unsafe_allow_html=True)
            
            # Gráfico de Área
            base = alt.Chart(df_filtrado).encode(
                x=alt.X('Mês', title=None, axis=alt.Axis(labelAngle=0, labelColor=COR_TEXTO, domain=False, tickSize=0)),
                tooltip=[alt.Tooltip('Mês'), alt.Tooltip('Gasto', format='$,.2f')]
            )

            area = base.mark_area(
                line={'color': COR_PRIMARIA, 'strokeWidth': 3},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color=COR_PRIMARIA, offset=0),
                           alt.GradientStop(color='white', offset=1)],
                    x1=1, x2=1, y1=1, y2=0
                ),
                interpolate='monotone'
            ).encode(
                y=alt.Y('Gasto', title=None, axis=alt.Axis(format=',.0f', grid=True, domain=False, ticks=False, labelPadding=10))
            )

            points = base.mark_circle(size=80, color='white', opacity=1).encode(
                y=alt.Y('Gasto'),
                stroke=alt.value(COR_PRIMARIA),
                strokeWidth=alt.value(2)
            )

            st.altair_chart((area + points).properties(height=320), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with col_dir:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown(f"<b style='color:{COR_SECUNDARIA}; font-size:16px;'>Volume de KM</b>", unsafe_allow_html=True)
            
            # Gráfico de Barras
            bar_chart = alt.Chart(df_filtrado).mark_bar(
                color=COR_PRIMARIA,
                cornerRadiusTopLeft=6,
                cornerRadiusTopRight=6,
                size=35 
            ).encode(
                x=alt.X('Mês', title=None, axis=alt.Axis(labelAngle=0, labelColor=COR_TEXTO, domain=False, tickSize=0)),
                y=alt.Y('KM', title=None, axis=alt.Axis(grid=True, format=',.0f', domain=False, ticks=False, labelPadding=10)),
                tooltip=[alt.Tooltip('Mês'), alt.Tooltip('KM', format=',')]
            ).properties(height=320)
            
            st.altair_chart(bar_chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Tabela (Revertida para ProgressColumn)
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown(f"<b style='color:{COR_SECUNDARIA}; font-size:16px;'>Detalhamento</b>", unsafe_allow_html=True)
        
        st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Mês": st.column_config.TextColumn("Mês"),
                # REVERTIDO AQUI: Volta a ser ProgressColumn
                "Gasto": st.column_config.ProgressColumn(
                    "Gasto Real", 
                    format="R$ %.2f",
                    min_value=0, 
                    max_value=df_base['Gasto'].max()
                ),
                "KM": st.column_config.NumberColumn("KM", format="%d km"),
                "Custo/KM": st.column_config.NumberColumn("Eficiência", format="R$ %.3f")
            }
        )
        st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.warning("Selecione os dados na barra lateral.")
else:
    st.info("Conectando ao banco de dados...")