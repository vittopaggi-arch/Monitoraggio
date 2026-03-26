import streamlit as st
import pandas as pd
import plotly.express as px

# --- SETUP DASHBOARD ---
st.set_page_config(page_title="OCEAN-TRACK PRO", layout="wide", page_icon="🌍")

# Stile CSS per un look moderno
st.markdown("""
    <style>
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #3d4150; }
    </style>
    """, unsafe_allow_html=True)

# --- CARICAMENTO DATI ---
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("Avvistamenti.xlsx")
        df.columns = df.columns.str.strip().str.lower()
        
        # Mapping flessibile nomi colonne
        col_map = {'specie avvistata': 'specie', 'n_esemplari': 'count', 'latitudine': 'lat', 'longitudine': 'lon'}
        df = df.rename(columns=col_map)
        
        # Pulizia coordinate
        if 'lat' in df.columns and 'lon' in df.columns:
            df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
            df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
            df = df.dropna(subset=['lat', 'lon'])
        return df
    except Exception as e:
        st.error(f"Errore caricamento: {e}")
        return None

df = load_data()

if df is not None:
    # --- SIDEBAR: CONTROLLI MAPPA ---
    st.sidebar.title("🗺️ OPZIONI MAPPA")
    
    # SELETTORE STILE GOOGLE-STYLE
    map_choice = st.sidebar.radio(
        "Seleziona Tipo di Mappa:",
        ["Satellite Ibrido", "Mappa Stradale (Google Style)", "Terreno Scientifico"]
    )
    
    specie_sel = st.sidebar.multiselect("Filtra Specie", df['specie'].unique(), default=df['specie'].unique())
    df_f = df[df['specie'].isin(specie_sel)]

    # --- MAIN CONTENT ---
    st.title("🛰️ Monitoraggio Geospaziale Interattivo")
    
    # Metriche
    c1, c2, c3 = st.columns(3)
    c1.metric("AVVISTAMENTI", len(df_f))
    if 'count' in df_f.columns:
        c2.metric("ESEMPLARI", int(df_f['count'].sum()))
    c3.metric("AREA COPERTA", f"{df_f['lat'].nunique()} coordinate")

    # --- MAPPA INTERATTIVA ---
    st.subheader("📍 Visualizzazione Satellitare e Navigazione")
    
    # Mapping degli stili Plotly
    styles = {
        "Satellite Ibrido": "white-bg", # Useremo un layer esterno sotto
        "Mappa Stradale (Google Style)": "open-street-map",
        "Terreno Scientifico": "stamen-terrain"
    }

    fig = px.scatter_mapbox(
        df_f,
        lat="lat",
        lon="lon",
        color="specie",
        size="count" if "count" in df_f.columns else None,
        hover_name="specie",
        hover_data=list(df_f.columns),
        zoom=6,
        height=700,
        mapbox_style=styles[map_choice],
        color_discrete_sequence=px.colors.qualitative.Bold
    )

    # SE SATELLITE: Aggiungiamo il layer fotografico ad alta risoluzione
    if map_choice == "Satellite Ibrido":
        fig.update_layout(
            mapbox_layers=[{
                "below": 'traces',
                "sourcetype": "raster",
                "source": ["https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"]
            }]
        )

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)

    # --- TABELLA E DOWNLOAD ---
    with st.expander("📂 Esplora Database Completo"):
        st.dataframe(df_f, use_container_width=True)
        csv = df_f.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Scarica CSV", csv, "dati_mappa.csv", "text/csv")
