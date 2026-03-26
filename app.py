import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- 1. CONFIGURAZIONE SISTEMA ---
st.set_page_config(page_title="GORDAZZONI PRIVATE ACCESS", layout="wide", page_icon="🔐")

# PASSWORD DI ACCESSO (Puoi cambiarla qui)
PASSWORD_ISTITUTO = "Gordazzo2026"

# --- 2. INTERFACCIA DI SICUREZZA (LOGIN) ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def check_password():
    if st.session_state["password_input"] == PASSWORD_ISTITUTO:
        st.session_state["authenticated"] = True
        st.success("✅ ACCESSO AUTORIZZATO. Caricamento sistemi...")
    else:
        st.error("❌ CHIAVE ERRATA. Accesso negato.")

if not st.session_state["authenticated"]:
    st.title("🔐 GORDAZZONI INSTITUTE | SECURE GATEWAY")
    st.markdown("---")
    col_lock, col_input = st.columns([1, 2])
    with col_lock:
        st.image("https://cdn-icons-png.flaticon.com/512/2592/2592223.png", width=200)
    with col_input:
        st.subheader("Autenticazione Richiesta")
        st.text_input("Inserire Security Token per decriptare i dati:", type="password", key="password_input", on_change=check_password)
        st.info("I dati contenuti in questo portale sono protetti da embargo scientifico NASA-OS.")
    st.stop() # Blocca tutto il resto se non autenticato

# --- 3. ESTETICA DARK SCIENTIFIC (DOPO IL LOGIN) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    .main { background-color: #050a14; color: #e0e0e0; }
    .stMetric { 
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 20px; border-radius: 15px; border: 1px solid #38bdf8;
    }
    h1 { font-family: 'Orbitron', sans-serif; color: #38bdf8; text-transform: uppercase; letter-spacing: 3px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. DATA ENGINE ---
@st.cache_data
def load_secure_data():
    try:
        df = pd.read_excel("Avvistamenti.xlsx")
        df.columns = df.columns.str.strip().str.lower()
        # Mapping flessibile
        m = {'specie avvistata': 'specie', 'n_esemplari': 'count', 'latitudine': 'lat', 'longitudine': 'lon'}
        df = df.rename(columns=m)
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        return df.dropna(subset=['lat', 'lon'])
    except Exception as e:
        st.error(f"DATABASE OFFLINE: {e}")
        return None

df = load_secure_data()

if df is not None:
    # --- SIDEBAR CONTROL ---
    with st.sidebar:
        st.title("🛰️ MISSION CONTROL")
        st.code(f"USER: AUTHORIZED\nSYNC: {datetime.now().strftime('%H:%M:%S')}\nSTATUS: ENCRYPTED", language="bash")
        st.markdown("---")
        map_style = st.selectbox("SENSORS MODE", ["Satellite Hybrid", "Deep Sea Terrain", "Dark Ops"])
        specie_sel = st.multiselect("TARGET SPECIE", df['specie'].unique(), default=df['specie'].unique())
        df_f = df[df['specie'].isin(specie_sel)]
        if st.button("🔴 LOGOUT"):
            st.session_state["authenticated"] = False
            st.rerun()

    # --- MAIN DASHBOARD ---
    st.title("Gordazzoni Institute Research")
    st.markdown("### *Restricted Research Environment - Level 5 Clearance*")

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("TRACKS", len(df_f))
    m2.metric("TOTAL SPECIMENS", int(df_f['count'].sum()) if 'count' in df_f.columns else "N/A")
    m3.metric("SEA TEMP AVG", f"{df_f['temperatura_acqua'].mean():.1f}°C")
    m4.metric("MAX DEPTH", f"{int(df_f['profondita_mare'].max())}m")

    # --- TABS ---
    t1, t2, t3 = st.tabs(["🌎 GEOSPATIAL RADAR", "📊 ANALYTICS", "💾 ENCRYPTED DATA"])

    with t1:
        st.subheader("Rilevamento Satellitare in Tempo Reale")
        st_map = {"Satellite Hybrid": "white-bg", "Deep Sea Terrain": "stamen-terrain", "Dark Ops": "carto-darkmatter"}
        
        fig_map = px.scatter_mapbox(df_f, lat="lat", lon="lon", color="specie", 
                                  size="count" if "count" in df_f.columns else None,
                                  hover_name="specie", zoom=6, height=700,
                                  mapbox_style=st_map[map_style], color_discrete_sequence=px.colors.qualitative.Prism)
        
        if map_style == "Satellite Hybrid":
            fig_map.update_layout(mapbox_layers=[{
                "sourcetype": "raster",
                "source": ["https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"]
            }])
        
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_map, use_container_width=True)

    with t2:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Gerarchia Biologica")
            st.plotly_chart(px.sunburst(df_f, path=['specie', 'comportamento'], template="plotly_dark"), use_container_width=True)
        with c2:
            st.subheader("Correlazione Ambiente")
            fig_env = px.scatter(df_f, x="temperatura_acqua", y="profondita_mare", color="specie", template="plotly_dark")
            fig_env.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_env, use_container_width=True)

    with t3:
        st.subheader("Ispezione Dati Protetti")
        st.dataframe(df_f, use_container_width=True)
        st.download_button("📥 EXPORT ENCRYPTED CSV", df_f.to_csv(index=False).encode('utf-8'), "gordazzoni_secret.csv", "text/csv")
