import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURAZIONE SISTEMA ---
st.set_page_config(page_title="GORDAZZONI MISSION CONTROL", layout="wide", page_icon="🔐")

PASSWORD_ISTITUTO = "Gordazzo2026"

# --- 2. GESTIONE AUTENTICAZIONE ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

def login():
    if st.session_state["pwd_input"] == PASSWORD_ISTITUTO:
        st.session_state["authenticated"] = True
    else:
        st.error("❌ CHIAVE ERRATA.")

if not st.session_state["authenticated"]:
    st.title("🔐 GORDAZZONI INSTITUTE | GATEWAY")
    st.text_input("Inserire Security Token:", type="password", key="pwd_input", on_change=login)
    st.stop()

# --- 3. ESTETICA ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    .main { background-color: #050a14; }
    h1 { font-family: 'Orbitron', sans-serif; color: #38bdf8; text-transform: uppercase; }
    .stMetric { background: #0f172a; border: 1px solid #38bdf8; border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. DATA ENGINE (CORRETTO PER I PUNTINI) ---
@st.cache_data
def load_data_blindato():
    try:
        df = pd.read_excel("Avvistamenti.xlsx")
        # Pulizia nomi colonne
        df.columns = df.columns.str.strip()
        
        # TROVA LATITUDINE E LONGITUDINE (Qualsiasi nome abbiano)
        lat_c = next((c for c in df.columns if c.lower() in ['lat', 'latitudine', 'latitude']), None)
        lon_c = next((c for c in df.columns if c.lower() in ['lon', 'longitudine', 'longitude']), None)
        specie_c = next((c for c in df.columns if c.lower() in ['specie', 'species']), 'specie')
        count_c = next((c for c in df.columns if c.lower() in ['n_esemplari', 'count', 'numero']), None)

        if lat_c and lon_c:
            # Forza la conversione a numero (se ci sono virgole o testi, li pulisce)
            df[lat_c] = pd.to_numeric(df[lat_c], errors='coerce')
            df[lon_c] = pd.to_numeric(df[lon_c], errors='coerce')
            # Rinomina per il codice interno
            df = df.rename(columns={lat_c: 'lat', lon_c: 'lon', specie_c: 'specie'})
            if count_c: df = df.rename(columns={count_c: 'count'})
            
            # ELIMINA RIGHE SENZA COORDINATE (Cruciale per i puntini!)
            df = df.dropna(subset=['lat', 'lon'])
            return df
        return None
    except Exception as e:
        st.error(f"Errore caricamento: {e}")
        return None

df = load_data_blindato()

if df is not None:
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🛰️ CONTROLLI")
        map_style = st.selectbox("MAPPA", ["Satellite Ibrido", "Mappa Stradale", "Terreno"])
        specie_sel = st.multiselect("FILTRA SPECIE", df['specie'].unique(), default=df['specie'].unique())
        df_f = df[df['specie'].isin(specie_sel)]
        if st.button("🔴 LOGOUT"):
            st.session_state["authenticated"] = False
            st.rerun()

    # --- DASHBOARD ---
    st.title("Gordazzoni Institute Research")
    
    # KPI
    c1, c2, c3 = st.columns(3)
    c1.metric("AVVISTAMENTI", len(df_f))
    c2.metric("ESEMPLARI", int(df_f['count'].sum()) if 'count' in df_f.columns else "N/D")
    c3.metric("AREA", "MEDITERRANEO SETT.")

    # --- MAPPA (CORRETTA) ---
    st.subheader("📍 Geoposizionamento Asset")
    
    styles = {"Satellite Ibrido": "white-bg", "Mappa Stradale": "open-street-map", "Terreno": "stamen-terrain"}
    
    # Creazione figura con i PUNTINI (Scatter Mapbox)
    fig = px.scatter_mapbox(
        df_f, 
        lat="lat", 
        lon="lon", 
        color="specie",
        size="count" if "count" in df_f.columns else None,
        hover_name="specie",
        hover_data=list(df_f.columns),
        zoom=5, 
        height=700,
        mapbox_style=styles[map_style]
    )

    # Layer Satellitare (Se selezionato)
    if map_style == "Satellite Ibrido":
        fig.update_layout(mapbox_layers=[{
            "below": 'traces', "sourcetype": "raster",
            "source": ["https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"]
        }])

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, use_container_width=True)

    # Database
    with st.expander("Ispezione Dati"):
        st.dataframe(df_f, use_container_width=True)
else:
    st.error("Impossibile generare la mappa. Controlla che nel file Excel ci siano colonne chiamate 'lat' e 'lon' con dei numeri.")
