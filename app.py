import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURAZIONE AVANZATA UI ---
st.set_page_config(
    page_title="OCEAN-TRACK | Sistema Monitoraggio Cetacei",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS per rendere l'interfaccia più "Tech"
st.markdown("""
    <style>
    .stMetric { background-color: #0e1117; padding: 10px; border-radius: 5px; border: 1px solid #31333f; }
    .main { background-color: #0e1117; }
    </style>
    """, unsafe_allow_html=True)

# --- CARICAMENTO E OTTIMIZZAZIONE DATI ---
@st.cache_data
def load_and_clean_data():
    try:
        df = pd.read_excel("Avvistamenti.xlsx")
        # Normalizzazione brutale dei nomi colonne per evitare ogni errore
        df.columns = df.columns.str.strip().str.lower()
        
        # Mapping nomi colonne flessibile
        col_map = {
            'specie avvistata': 'specie', 
            'n_esemplari': 'count', 
            'latitudine': 'lat', 
            'longitudine': 'lon'
        }
        df = df.rename(columns=col_map)
        
        # Casting tipologico forzato
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        df = df.dropna(subset=['lat', 'lon']) # Sicurezza assoluta per la mappa
        
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
            
        return df
    except Exception as e:
        st.error(f"ERRORE CRITICO DATABASE: {e}")
        return None

df = load_and_clean_data()

if df is not None:
    # --- SIDEBAR TECNICA ---
    st.sidebar.title("🛰️ CORE CONTROLS")
    st.sidebar.markdown("---")
    
    specie_list = df['specie'].unique()
    selected_specie = st.sidebar.multiselect("Filtro Specie", specie_list, default=specie_list)
    
    view_mode = st.sidebar.selectbox("Stile Mappa", ["Satellite-Hybrid", "Terrain-Scientific", "Dark-Navigation"])
    
    # Filtro temporale dinamico
    if 'data' in df.columns:
        min_date, max_date = df['data'].min().date(), df['data'].max().date()
        date_range = st.sidebar.date_input("Range Temporale", [min_date, max_date])

    # --- MAIN DASHBOARD ---
    st.title("🐋 OCEAN-TRACK: Real-Time Cetacean Monitoring")
    
    # KPI Row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("AVVISTAMENTI", len(df))
    with k2:
        total_e = int(df['count'].sum()) if 'count' in df.columns else "N/D"
        st.metric("ESEMPLARI TOTALI", total_e)
    with k3:
        depth_avg = f"{int(df['profondita_mare'].mean())}m" if 'profondita_mare' in df.columns else "N/D"
        st.metric("AVG DEPTH", depth_avg)
    with k4:
        temp_avg = f"{df['temperatura_acqua'].mean():.1f}°C" if 'temperatura_acqua' in df.columns else "N/D"
        st.metric("SEA TEMP", temp_avg)

    # --- LA MAPPA "DELLA MADONNA" ---
    st.markdown("### 📍 Geospatial Distribution Analysis")
    
    # Mapping stili mappa
    map_styles = {
        "Satellite-Hybrid": "white-bg",
        "Terrain-Scientific": "stamen-terrain",
        "Dark-Navigation": "carto-darkmatter"
    }

    # Creazione figura Plotly
    fig = px.scatter_mapbox(
        df[df['specie'].isin(selected_specie)],
        lat="lat",
        lon="lon",
        color="specie",
        size="count" if "count" in df.columns else None,
        hover_name="specie",
        hover_data=["comportamento", "profondita_mare"] if "comportamento" in df.columns else None,
        zoom=6,
        height=750,
        mapbox_style=map_styles[view_mode],
        color_discrete_sequence=px.colors.qualitative.Vivid
    )

    # Aggiunta strato per il Satellite se selezionato (usa tile gratuite)
    if view_mode == "Satellite-Hybrid":
        fig.update_layout(
            mapbox_layers=[{
                "below": 'traces',
                "sourcetype": "raster",
                "source": ["https://basemaps.cartocdn.com/rastertiles/voyager_labels_under/{z}/{x}/{y}.png"]
            }]
        )

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="#0e1117")
    st.plotly_chart(fig, use_container_width=True)

    # --- ANALISI CORRELATA ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Densità Popolazione")
        fig_bar = px.bar(df, x="specie", y="count" if "count" in df.columns else None, color="specie", template="plotly_dark")
        st.plotly_chart(fig_bar, use_container_width=True)
    with c2:
        st.subheader("🌡️ Correlazione Profondità/Temperatura")
        if 'temperatura_acqua' in df.columns and 'profondita_mare' in df.columns:
            fig_scat = px.scatter(df, x="temperatura_acqua", y="profondita_mare", color="specie", template="plotly_dark")
            fig_scat.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_scat, use_container_width=True)

    # --- DATABASE ISPECTION ---
    with st.expander("📂 RAW DATA INSPECTION UNIT"):
        st.dataframe(df.style.background_gradient(cmap='Blues'), use_container_width=True)
