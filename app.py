import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Gordazzoni Institute Research", layout="wide", page_icon="🐋")

# Password di sicurezza
PASSWORD_ISTITUTO = "Gordazzo2026"

# --- 2. LOGIN AREA ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.title("🔐 GORDAZZONI GATEWAY")
    pwd = st.text_input("Inserire Security Token:", type="password")
    if pwd == PASSWORD_ISTITUTO:
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# --- 3. ESTETICA DARK SCIENTIFIC ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    .main { background-color: #050a14; color: #e0e0e0; }
    h1 { font-family: 'Orbitron', sans-serif; color: #38bdf8; text-transform: uppercase; letter-spacing: 3px; }
    .stMetric { background: #0f172a; border: 1px solid #38bdf8; border-radius: 10px; padding: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. DATA ENGINE (RIPRISTINATO) ---
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("Avvistamenti.xlsx")
        df.columns = df.columns.str.strip().str.lower()
        
        # Pulizia coordinate: forza i numeri e toglie le virgole
        for c in ['lat', 'lon', 'latitudine', 'longitudine']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c].astype(str).str.replace(',', '.'), errors='coerce')
        
        # Identificazione colonne per la mappa
        c_lat = next((c for c in df.columns if c in ['lat', 'latitudine']), None)
        c_lon = next((c for c in df.columns if c in ['lon', 'longitudine']), None)
        
        if c_lat and c_lon:
            return df.dropna(subset=[c_lat, c_lon]), c_lat, c_lon
        return None, None, None
    except Exception as e:
        st.error(f"Errore caricamento: {e}")
        return None, None, None

df, lat_col, lon_col = load_data()

if df is not None:
    # --- HEADER ---
    st.title("Gordazzoni Institute Research")
    
    # Metriche veloci
    m1, m2, m3 = st.columns(3)
    m1.metric("AVVISTAMENTI", len(df))
    m2.metric("COORD. RILEVATE", f"{len(df)} FIX")
    m3.metric("AREA DI RICERCA", "MEDITERRANEO")

    # --- 5. LA MAPPA (CON COORDINATE VISIBILI) ---
    st.subheader("📍 Geoposizionamento Asset e Coordinate")
    
    # Creazione della mappa con i punti
    fig = px.scatter_mapbox(
        df,
        lat=lat_col,
        lon=lon_col,
        color="specie" if "specie" in df.columns else None,
        size="n_esemplari" if "n_esemplari" in df.columns else None,
        # AGGIUNTA: Mostra Latitudine e Longitudine nel fumetto al passaggio del mouse
        hover_name="specie" if "specie" in df.columns else None,
        hover_data={lat_col: True, lon_col: True, "temperatura_acqua": True, "profondita_mare": True},
        zoom=5,
        height=700,
        mapbox_style="carto-darkmatter" # Stile Dark Professionale per far risaltare i punti
    )

    # Miglioramento estetica mappa
    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        paper_bgcolor="rgba(0,0,0,0)",
        # Visualizzazione della scala delle coordinate
        mapbox=dict(
            bearing=0,
            center=dict(lat=df[lat_col].mean(), lon=df[lon_col].mean()),
            pitch=0,
            zoom=5
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # --- 6. DATABASE ISPEZIONE ---
    with st.expander("📂 ISPEZIONE TELEMETRIA DATI"):
        st.dataframe(df, use_container_width=True)
else:
    st.error("ERRORE: Non trovo i dati delle coordinate nell'Excel. Controlla le colonne 'lat' e 'lon'.")
