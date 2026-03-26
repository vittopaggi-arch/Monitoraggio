import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- 1. CONFIGURAZIONE ESTETICA E UI ---
st.set_page_config(page_title="Gordazzoni Institute Research", layout="wide", page_icon="🐋")

# Password di sistema
PASSWORD_ISTITUTO = "Gordazzo2026"

# CSS Professionale per l'Istituto
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Source+Code+Pro&display=swap');
    .main { background-color: #050a14; color: #e0e0e0; }
    .stMetric { 
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 20px; border-radius: 15px; border: 1px solid #38bdf8;
        box-shadow: 0 4px 15px rgba(56, 189, 248, 0.2);
    }
    h1 { font-family: 'Orbitron', sans-serif; color: #38bdf8; text-transform: uppercase; letter-spacing: 3px; font-size: 2.5rem !important; }
    h2, h3 { font-family: 'Orbitron', sans-serif; color: #38bdf8; }
    code { color: #00f2ff; font-family: 'Source Code Pro', monospace; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #1e293b; border-radius: 5px; padding: 10px 20px; color: white; border: 1px solid #334155;
    }
    .stTabs [aria-selected="true"] { background-color: #38bdf8 !important; color: #050a14 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SISTEMA DI SICUREZZA GATEKEEPER ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.title("🔐 GORDAZZONI GATEWAY")
    st.markdown("---")
    col_l, col_r = st.columns([1, 2])
    with col_l:
        st.image("https://cdn-icons-png.flaticon.com/512/2592/2592223.png", width=200)
    with col_r:
        st.subheader("Restricted Access Area")
        pwd = st.text_input("Inserire Security Token per decriptare i dati:", type="password")
        if st.button("SBLOCCA SISTEMA"):
            if pwd == PASSWORD_ISTITUTO:
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("CHIAVE DI ACCESSO NON VALIDA")
    st.stop()

# --- 3. DATA ENGINE (PULIZIA SCIENTIFICA) ---
@st.cache_data
def load_all_data():
    try:
        df = pd.read_excel("Avvistamenti.xlsx")
        df.columns = df.columns.str.strip().str.lower()
        
        # Mapping flessibile per nomi comuni
        m = {'n_esemplari': 'count', 'latitudine': 'lat', 'longitudine': 'lon'}
        df = df.rename(columns=m)
        
        # Pulizia forzata dei numeri (gestione virgola italiana)
        cols_to_fix = ['lat', 'lon', 'profondita_mare', 'temperatura_acqua', 'count']
        for col in cols_to_fix:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
            
        return df.dropna(subset=['lat', 'lon'])
    except Exception as e:
        st.error(f"ERRORE CARICAMENTO DATABASE: {e}")
        return None

df = load_all_data()

if df is not None:
    # --- 4. SIDEBAR TERMINAL ---
    with st.sidebar:
        st.title("🛰️ MISSION CONTROL")
        st.code(f"STATION: GORDAZZONI-1\nSYNC: {datetime.now().strftime('%H:%M:%S')}\nSEC-LEVEL: 5", language="bash")
        st.markdown("---")
        
        map_mode = st.selectbox("SENSOR MODE", ["Satellite Hybrid", "Deep Sea Radar", "Dark Ops"])
        
        specie_list = df['specie'].unique()
        sel_specie = st.multiselect("TARGET SPECIE", specie_list, default=specie_list)
        df_f = df[df['specie'].isin(sel_specie)]
        
        st.markdown("---")
        if st.button("🔴 TERMINA SESSIONE"):
            st.session_state["auth"] = False
            st.rerun()

    # --- 5. DASHBOARD MAIN ---
    st.title("Gordazzoni Institute Research")
    
    # KPI Dinamici
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("TRACKS", len(df_f))
    k2.metric("INDIVIDUALS", int(df_f['count'].sum()) if 'count' in df_f.columns else "N/D")
    k3.metric("AVG TEMP", f"{df_f['temperatura_acqua'].mean():.1f}°C" if 'temperatura_acqua' in df_f.columns else "N/D")
    k4.metric("MAX DEPTH", f"{int(df_f['profondita_mare'].max())}m" if 'profondita_mare' in df_f.columns else "N/D")

    # --- 6. NAVIGAZIONE TABS ---
    t_geo, t_science, t_env, t_data = st.tabs(["🌐 GEOSPATIAL RADAR", "🧬 ANALYTICS", "🌡️ ENVIRONMENT", "💾 LOGS"])

    with t_geo:
        st.subheader("Rilevamento Posizione Asset")
        st_map = {"Satellite Hybrid": "white-bg", "Deep Sea Radar": "stamen-terrain", "Dark Ops": "carto-darkmatter"}
        
        fig_map = px.scatter_mapbox(
            df_f, lat="lat", lon="lon", color="specie", 
            size="count" if "count" in df_f.columns else None,
            hover_name="specie", hover_data=["lat", "lon", "temperatura_acqua"],
            zoom=5, height=700, mapbox_style=st_map[map_mode],
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        
        if map_mode == "Satellite Hybrid":
            fig_map.update_layout(mapbox_layers=[{
                "sourcetype": "raster",
                "source": ["https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"]
            }])
        
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_map, use_container_width=True)

    with t_science:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Gerarchia Biologica")
            fig_sun = px.sunburst(df_f, path=['specie', 'comportamento'], values='count' if 'count' in df_f.columns else None,
                                 template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_sun, use_container_width=True)
        with c2:
            st.subheader("Frequenza Attività")
            fig_bar = px.histogram(df_f, x="specie", color="comportamento", barmode="group", template="plotly_dark")
            st.plotly_chart(fig_bar, use_container_width=True)

    with t_env:
        st.subheader("Niche Ambientale: Correlazione Profondità/Temperatura")
        col_env1, col_env2 = st.columns([2, 1])
        
        with col_env1:
            # Scatter plot scientifico con asse invertito
            fig_scat = px.scatter(df_f, x="temperatura_acqua", y="profondita_mare", color="specie", 
                                size="count" if "count" in df_f.columns else None, 
                                template="plotly_dark", labels={"profondita_mare": "Profondità (m)", "temperatura_acqua": "Temp (°C)"})
            fig_scat.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_scat, use_container_width=True)
        
        with col_env2:
            # Box plot della distribuzione batimetrica
            fig_box = px.box(df_f, x="specie", y="profondita_mare", color="specie", template="plotly_dark")
            fig_box.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_box, use_container_width=True)

    with t_data:
        st.subheader("Ispezione Data-Log")
        st.dataframe(df_f, use_container_width=True)
        csv = df_f.to_csv(index=False).encode('utf-8')
        st.download_button("📥 EXPORT REPORT (CSV)", csv, "gordazzoni_report.csv", "text/csv")

# Footer
st.markdown("---")
st.caption("© 2026 GORDAZZONI INSTITUTE RESEARCH | PROTECTED DATA STREAM")
