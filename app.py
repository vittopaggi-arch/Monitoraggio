import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Gordazzoni Institute Research", layout="wide", page_icon="🐋")
PASSWORD_ISTITUTO = "Gordazzo2026"

# Sicurezza
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    st.title("🔐 GORDAZZONI GATEWAY")
    pwd = st.text_input("Security Token:", type="password")
    if st.button("SBLOCCA"):
        if pwd == PASSWORD_ISTITUTO:
            st.session_state["auth"] = True
            st.rerun()
    st.stop()

# --- 2. DATA ENGINE (FIX PUNTINI E COORDINATE) ---
@st.cache_data
def load_and_fix_data():
    try:
        df = pd.read_excel("Avvistamenti.xlsx")
        df.columns = df.columns.str.strip().str.lower()
        
        c_lat = next((c for c in df.columns if c in ['lat', 'latitudine', 'latitude']), None)
        c_lon = next((c for c in df.columns if c in ['lon', 'longitudine', 'longitude']), None)
        c_specie = next((c for c in df.columns if c in ['specie', 'species']), 'specie')
        c_count = next((c for c in df.columns if c in ['count', 'n_esemplari', 'numero']), 'n_esemplari')
        
        if c_lat and c_lon:
            df[c_lat] = pd.to_numeric(df[c_lat].astype(str).str.replace(',', '.'), errors='coerce')
            df[c_lon] = pd.to_numeric(df[c_lon].astype(str).str.replace(',', '.'), errors='coerce')
            
            df = df.rename(columns={c_lat: 'lat_map', c_lon: 'lon_map', c_specie: 'specie_map'})
            if c_count in df.columns: df = df.rename(columns={c_count: 'count_map'})
            
            return df.dropna(subset=['lat_map', 'lon_map'])
        return None
    except Exception as e:
        st.error(f"Errore: {e}")
        return None

df = load_and_fix_data()

if df is not None:
    # Estetica
    st.markdown("""<style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron&display=swap');
        .main { background-color: #050a14; color: #e0e0e0; }
        h1 { font-family: 'Orbitron', sans-serif; color: #38bdf8; text-transform: uppercase; }
        .stMetric { background: #0f172a; border: 1px solid #38bdf8; border-radius: 10px; padding: 20px; }
    </style>""", unsafe_allow_html=True)

    with st.sidebar:
        st.title("🛰️ MISSION CONTROL")
        map_style = st.selectbox("SENSOR MODE", ["Dark Matter", "Satellite Hybrid", "Open Street"])
        sel_specie = st.multiselect("SPECIE", df['specie_map'].unique(), default=df['specie_map'].unique())
        df_f = df[df['specie_map'].isin(sel_specie)]
        if st.button("🔴 LOGOUT"):
            st.session_state["auth"] = False
            st.rerun()

    st.title("Gordazzoni Institute Research")
    
    # KPI
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("TRACKS", len(df_f))
    k2.metric("INDIVIDUALS", int(df_f['count_map'].sum()) if 'count_map' in df_f.columns else "N/A")
    k3.metric("AVG TEMP", f"{df_f['temperatura_acqua'].mean():.1f}°C" if 'temperatura_acqua' in df_f.columns else "N/D")
    k4.metric("MAX DEPTH", f"{int(df_f['profondita_mare'].max())}m" if 'profondita_mare' in df_f.columns else "N/D")

    # TABS
    t_map, t_science, t_env, t_data = st.tabs(["🌐 RADAR MAP", "🧬 POPULATION DENSITY", "🌡️ ENVIRONMENTAL NICHE", "💾 LOGS"])

    with t_map:
        st.subheader("Rilevamento Posizioni Satellitari")
        map_dict = {"Dark Matter": "carto-darkmatter", "Satellite Hybrid": "white-bg", "Open Street": "open-street-map"}
        
        fig_map = px.scatter_mapbox(
            df_f, lat="lat_map", lon="lon_map", color="specie_map",
            size="count_map" if "count_map" in df_f.columns else None,
            hover_name="specie_map", hover_data=["temperatura_acqua", "profondita_mare"],
            zoom=5, height=700, mapbox_style=map_dict[map_style]
        )
        if map_style == "Satellite Hybrid":
            fig_map.update_layout(mapbox_layers=[{"sourcetype": "raster", "source": ["https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"]}])
        
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_map, use_container_width=True)

    with t_science:
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.subheader("TreeMap: Rilevanza Specie")
            # Sostituisce la torta: mostra l'abbondanza relativa in modo molto più chiaro
            fig_tree = px.treemap(df_f, path=[px.Constant("Tutte le Specie"), 'specie_map'], 
                                 values='count_map' if 'count_map' in df_f.columns else None,
                                 color='specie_map', template="plotly_dark")
            st.plotly_chart(fig_tree, use_container_width=True)
        with col_s2:
            st.subheader("Frequenza Comportamentale")
            fig_bar = px.bar(df_f, x="specie_map", color="comportamento", barmode="stack", template="plotly_dark")
            st.plotly_chart(fig_bar, use_container_width=True)

    with t_env:
        st.subheader("Analisi della Niche Ambientale")
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            st.markdown("#### Distribuzione Profondità per Specie")
            fig_box = px.box(df_f, x="specie_map", y="profondita_mare", color="specie_map", template="plotly_dark", points="all")
            fig_box.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_box, use_container_width=True)
        with col_e2:
            st.markdown("#### Mappa di Calore: Temp vs Profondità")
            # Mostra dove si concentrano gli animali (Densità di avvistamento)
            fig_heat = px.density_heatmap(df_f, x="temperatura_acqua", y="profondita_mare", 
                                          marginal_x="histogram", marginal_y="histogram",
                                          template="plotly_dark", labels={'profondita_mare': 'Profondità', 'temperatura_acqua': 'Temp'})
            fig_heat.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_heat, use_container_width=True)

    with t_data:
        st.dataframe(df_f, use_container_width=True)
