import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Gordazzoni Institute Research", layout="wide", page_icon="🐋")
PASSWORD_ISTITUTO = "Gordazzo2026"

# --- 2. SICUREZZA ---
if "auth" not in st.session_state: st.session_state["auth"] = False
if not st.session_state["auth"]:
    st.title("🔐 GORDAZZONI GATEWAY")
    pwd = st.text_input("Security Token:", type="password")
    if st.button("SBLOCCA"):
        if pwd == PASSWORD_ISTITUTO:
            st.session_state["auth"] = True
            st.rerun()
    st.stop()

# --- 3. DATA ENGINE (CORREZIONE PUNTINI) ---
@st.cache_data
def load_and_fix_data():
    try:
        df = pd.read_excel("Avvistamenti.xlsx")
        df.columns = df.columns.str.strip().str.lower()
        
        # Identificazione automatica colonne coordinate
        c_lat = next((c for c in df.columns if c in ['lat', 'latitudine', 'latitude']), None)
        c_lon = next((c for c in df.columns if c in ['lon', 'longitudine', 'longitude', 'long']), None)
        c_specie = next((c for c in df.columns if c in ['specie', 'species']), 'specie')
        c_count = next((c for c in df.columns if c in ['count', 'n_esemplari', 'numero']), 'n_esemplari')
        
        if c_lat and c_lon:
            # Pulizia e conversione numerica (fondamentale per i puntini)
            df[c_lat] = pd.to_numeric(df[c_lat].astype(str).str.replace(',', '.'), errors='coerce')
            df[c_lon] = pd.to_numeric(df[c_lon].astype(str).str.replace(',', '.'), errors='coerce')
            
            # Rinomina per uniformità interna
            df = df.rename(columns={c_lat: 'lat_map', c_lon: 'lon_map', c_specie: 'specie_map'})
            if c_count in df.columns: df = df.rename(columns={c_count: 'count_map'})
            
            # Rimuove solo le righe dove mancano le coordinate
            return df.dropna(subset=['lat_map', 'lon_map'])
        return None
    except Exception as e:
        st.error(f"Errore: {e}")
        return None

df = load_and_fix_data()

if df is not None:
    # --- UI E DESIGN ---
    st.markdown("""<style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron&display=swap');
        .main { background-color: #050a14; color: #e0e0e0; }
        h1 { font-family: 'Orbitron', sans-serif; color: #38bdf8; text-transform: uppercase; }
        .stMetric { background: #0f172a; border: 1px solid #38bdf8; border-radius: 10px; padding: 20px; }
    </style>""", unsafe_allow_html=True)

    # Sidebar
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
    k3.metric("AVG TEMP", f"{df_f['temperatura_acqua'].mean():.1f}°C" if 'temperatura_acqua' in df_f.columns else "N/A")
    k4.metric("MAX DEPTH", f"{int(df_f['profondita_mare'].max())}m" if 'profondita_mare' in df_f.columns else "N/A")

    # TABS
    t_map, t_science, t_env, t_data = st.tabs(["🌐 RADAR MAP", "🧬 ANALYTICS", "🌡️ ENVIRONMENT", "💾 LOGS"])

    with t_map:
        st.subheader("Rilevamento Posizioni")
        map_dict = {"Dark Matter": "carto-darkmatter", "Satellite Hybrid": "white-bg", "Open Street": "open-street-map"}
        
        # FIGURA SCATTER MAPBOX (I PUNTINI)
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
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Gerarchia Biologica")
            st.plotly_chart(px.sunburst(df_f, path=['specie_map', 'comportamento'], template="plotly_dark"), use_container_width=True)
        with c2:
            st.subheader("Frequenza Attività")
            st.plotly_chart(px.histogram(df_f, x="specie_map", color="comportamento", barmode="group", template="plotly_dark"), use_container_width=True)

    with t_env:
        st.subheader("Niche Ambientale")
        col_e1, col_e2 = st.columns([2, 1])
        with col_e1:
            fig_env = px.scatter(df_f, x="temperatura_acqua", y="profondita_mare", color="specie_map", template="plotly_dark")
            fig_env.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_env, use_container_width=True)
        with col_e2:
            fig_box = px.box(df_f, x="specie_map", y="profondita_mare", color="specie_map", template="plotly_dark")
            fig_box.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_box, use_container_width=True)

    with t_data:
        st.dataframe(df_f, use_container_width=True)
