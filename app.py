import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- 1. CONFIGURAZIONE ESTETICA E PAGINA ---
st.set_page_config(page_title="Gordazzoni Institute Research", layout="wide", page_icon="🐋")

PASSWORD_ISTITUTO = "Gordazzo2026"

# CSS Custom per look Cyber-Scientifico
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    .main { background-color: #050a14; color: #e0e0e0; }
    .stMetric { 
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 20px; border-radius: 15px; border: 1px solid #38bdf8;
        box-shadow: 0 4px 15px rgba(56, 189, 248, 0.2);
    }
    h1 { font-family: 'Orbitron', sans-serif; color: #38bdf8; text-transform: uppercase; letter-spacing: 3px; font-size: 2.8rem !important; }
    h2, h3 { font-family: 'Orbitron', sans-serif; color: #38bdf8; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #1e293b; border-radius: 5px; padding: 10px 20px; color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SISTEMA DI ACCESSO ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.title("🔐 GORDAZZONI GATEWAY")
    pwd = st.text_input("Inserire Security Token per decriptare i dati:", type="password")
    if pwd == PASSWORD_ISTITUTO:
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# --- 3. DATA ENGINE (PULIZIA COORDINATE) ---
@st.cache_data
def load_all_data():
    try:
        df = pd.read_excel("Avvistamenti.xlsx")
        df.columns = df.columns.str.strip().str.lower()
        
        # Mapping flessibile
        m = {'n_esemplari': 'count', 'latitudine': 'lat', 'longitudine': 'lon'}
        df = df.rename(columns=m)
        
        # Pulizia coordinate (gestione virgola e stringhe)
        for col in ['lat', 'lon']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
            
        return df.dropna(subset=['lat', 'lon'])
    except Exception as e:
        st.error(f"DATABASE ERROR: {e}")
        return None

df = load_all_data()

if df is not None:
    # --- SIDEBAR TECNICA ---
    with st.sidebar:
        st.title("🛰️ MISSION CONTROL")
        st.code(f"STATUS: ONLINE\nREF: {datetime.now().strftime('%H:%M')}\nENC: AES-256", language="bash")
        st.markdown("---")
        
        style_map = st.selectbox("SENSORE MAPPA", ["Dark Matter", "Satellite Ibrido", "Terrain"])
        specie_list = df['specie'].unique()
        sel_specie = st.multiselect("TARGET SPECIE", specie_list, default=specie_list)
        
        df_f = df[df['specie'].isin(sel_specie)]
        
        if st.button("🔴 TERMINA SESSIONE"):
            st.session_state["auth"] = False
            st.rerun()

    # --- HEADER E KPI ---
    st.title("Gordazzoni Institute Research")
    st.markdown("#### *Advanced Oceanographic Telemetry System*")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("AVVISTAMENTI", len(df_f))
    k2.metric("ESEMPLARI", int(df_f['count'].sum()) if 'count' in df_f.columns else "N/A")
    k3.metric("TEMP MEDIA", f"{df_f['temperatura_acqua'].mean():.1f}°C" if 'temperatura_acqua' in df_f.columns else "N/A")
    k4.metric("PROF. MAX", f"{int(df_f['profondita_mare'].max())}m" if 'profondita_mare' in df_f.columns else "N/A")

    # --- LAYOUT TAB ---
    tab_geo, tab_stats, tab_env, tab_raw = st.tabs(["🌐 GEOSPATIAL RADAR", "📊 ANALYTICS", "🌡️ ENVIRONMENT", "💾 DATABASE"])

    with tab_geo:
        st.subheader("Rilevamento Posizione Asset")
        
        styles = {"Dark Matter": "carto-darkmatter", "Satellite Ibrido": "white-bg", "Terrain": "stamen-terrain"}
        
        fig_map = px.scatter_mapbox(
            df_f, lat="lat", lon="lon", color="specie", 
            size="count" if "count" in df_f.columns else None,
            hover_name="specie", 
            hover_data={"lat": True, "lon": True, "temperatura_acqua": True},
            zoom=5, height=750,
            mapbox_style=styles[style_map],
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        
        if style_map == "Satellite Ibrido":
            fig_map.update_layout(mapbox_layers=[{
                "sourcetype": "raster",
                "source": ["https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"]
            }])
        
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_map, use_container_width=True)

    with tab_stats:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Gerarchia Biologica")
            fig_sun = px.sunburst(df_f, path=['specie', 'comportamento'], values='count' if 'count' in df_f.columns else None,
                                 template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_sun, use_container_width=True)
        with c2:
            st.subheader("Trend Temporale")
            if 'data' in df_f.columns:
                df_trend = df_f.groupby([df_f['data'].dt.date, 'specie']).size().reset_index(name='n')
                fig_trend = px.line(df_trend, x='data', y='n', color='specie', markers=True, template="plotly_dark")
                st.plotly_chart(fig_trend, use_container_width=True)

    with tab_env:
        st.subheader("Analisi Correlazione Profondità/Temperatura")
        fig_env = px.scatter(df_f, x="temperatura_acqua", y="profondita_mare", color="specie", 
                            size="count" if "count" in df_f.columns else None, 
                            hover_data=['comportamento'], template="plotly_dark")
        fig_env.update_yaxes(autorange="reversed")
        st.plotly_chart(fig_env, use_container_width=True)

    with tab_raw:
        st.subheader("Ispezione Data-Log")
        st.dataframe(df_f, use_container_width=True)
        st.download_button("📥 DOWNLOAD ENCRYPTED CSV", df_f.to_csv(index=False).encode('utf-8'), "gordazzoni_export.csv", "text/csv")

# Footer NASA Style
st.markdown("---")
st.caption("🔒 GORDAZZONI INSTITUTE RESEARCH - AREA SOGGETTA A PROTOCOLLO DI RISERVATEZZA LIVELLO 5")
