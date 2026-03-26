import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="GORDAZZONI MISSION CONTROL", layout="wide")

PASSWORD_ISTITUTO = "Gordazzo2026"

# --- 2. LOGIN ---
if "auth" not in st.session_state:
    st.session_state["auth"] = False

if not st.session_state["auth"]:
    st.title("🔐 GORDAZZONI GATEWAY")
    pwd = st.text_input("Inserire Security Token:", type="password")
    if pwd == PASSWORD_ISTITUTO:
        st.session_state["auth"] = True
        st.rerun()
    st.stop()

# --- 3. DATA ENGINE (VERSIONE INFALLIBILE) ---
@st.cache_data
def load_clean_data():
    try:
        # Carica il file
        df = pd.read_excel("Avvistamenti.xlsx")
        
        # Pulizia nomi colonne: toglie spazi e mette in minuscolo per il controllo
        df.columns = df.columns.str.strip()
        
        # Identificazione colonne (Latitudine e Longitudine)
        c_lat = next((c for c in df.columns if c.lower() in ['lat', 'latitudine', 'latitude']), None)
        c_lon = next((c for c in df.columns if c.lower() in ['lon', 'longitudine', 'longitude']), None)
        c_specie = next((c for c in df.columns if c.lower() in ['specie', 'species']), None)
        c_num = next((c for c in df.columns if c.lower() in ['n_esemplari', 'count', 'numero']), None)

        if c_lat and c_lon:
            # TRUCCO MAGICO: Sostituisce la virgola col punto se i dati sono testi
            df[c_lat] = df[c_lat].astype(str).str.replace(',', '.')
            df[c_lon] = df[c_lon].astype(str).str.replace(',', '.')
            
            # Converte in numeri veri e propri
            df[c_lat] = pd.to_numeric(df[c_lat], errors='coerce')
            df[c_lon] = pd.to_numeric(df[c_lon], errors='coerce')
            
            # Rinomina per il grafico
            df = df.rename(columns={c_lat: 'lat', c_lon: 'lon'})
            if c_specie: df = df.rename(columns={c_specie: 'specie'})
            if c_num: df = df.rename(columns={c_num: 'n_esemplari'})
            
            # Rimuove righe dove la conversione è fallita (NaN)
            df = df.dropna(subset=['lat', 'lon'])
            return df
        return None
    except Exception as e:
        st.error(f"Errore tecnico: {e}")
        return None

df = load_clean_data()

# --- 4. INTERFACCIA ---
st.title("Gordazzoni Institute Research")

if df is not None and not df.empty:
    # Sidebar Filtri
    st.sidebar.header("Filtri Sensori")
    specie_list = df['specie'].unique() if 'specie' in df.columns else []
    sel_specie = st.sidebar.multiselect("Seleziona Specie", specie_list, default=specie_list)
    
    df_f = df[df['specie'].isin(sel_specie)] if 'specie' in df.columns else df

    # MAPPA PUNTI (SCATTER)
    st.subheader("📍 Rilevamento Posizioni")
    
    # Usiamo un colore fisso se 'specie' non esiste, altrimenti coloriamo per specie
    color_param = 'specie' if 'specie' in df_f.columns else None
    size_param = 'n_esemplari' if 'n_esemplari' in df_f.columns else None

    fig = px.scatter_mapbox(
        df_f,
        lat="lat",
        lon="lon",
        color=color_param,
        size=size_param,
        hover_name=color_param,
        zoom=5,
        height=600,
        mapbox_style="stamen-terrain" # Mostra coste e profondità
    )

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)
    
    # Ispezione per capire cosa vede il codice
    with st.expander("Ispezione Tecnica Dati (Se vuoto, l'Excel ha problemi
