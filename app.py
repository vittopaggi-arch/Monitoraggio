import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAZIONE DASHBOARD ---
st.set_page_config(
    page_title="OCEAN-TRACK | Monitoraggio",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Stile Dark Mode personalizzato
st.markdown("""
    <style>
    .stMetric { background-color: #1a1c24; padding: 15px; border-radius: 10px; border: 1px solid #3d4150; }
    [data-testid="stHeader"] {background: rgba(0,0,0,0);}
    </style>
    """, unsafe_allow_html=True)

# --- CARICAMENTO DATI ---
@st.cache_data
def load_and_clean_data():
    try:
        # Carica il file Avvistamenti.xlsx
        df = pd.read_excel("Avvistamenti.xlsx")
        # Pulizia automatica nomi colonne
        df.columns = df.columns.str.strip().str.lower()
        
        # Mapping flessibile per nomi comuni
        col_map = {
            'specie avvistata': 'specie', 
            'n_esemplari': 'count', 
            'latitudine': 'lat', 
            'longitudine': 'lon'
        }
        df = df.rename(columns=col_map)
        
        # Conversione numeri e pulizia righe senza coordinate
        if 'lat' in df.columns and 'lon' in df.columns:
            df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
            df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
            df = df.dropna(subset=['lat', 'lon'])
            
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
            
        return df
    except Exception as e:
        st.error(f"Errore caricamento file: {e}")
        return None

df = load_and_clean_data()

if df is not None:
    # --- SIDEBAR ---
    st.sidebar.title("🛰️ CONTROLLI")
    
    specie_list = df['specie'].unique()
    selected_specie = st.sidebar.multiselect("Filtra Specie", specie_list, default=specie_list)
    
    view_mode = st.sidebar.selectbox("Stile Mappa", ["Scientific Terrain", "Dark Navigation", "Light Map"])
    
    df_f = df[df['specie'].isin(selected_specie)]

    # --- HEADER ---
    st.title("🐋 OCEAN-TRACK: Sistema Monitoraggio Geospaziale")
    
    # Metriche (KPI)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("AVVISTAMENTI", len(df_f))
    
    count_col = 'count' if 'count' in df_f.columns else None
    if count_col:
        m2.metric("ESEMPLARI", int(df_f[count_col].sum()))
    
    if 'profondita_mare' in df_f.columns:
        m3.metric("PROFONDITÀ MAX", f"{int(df_f['profondita_mare'].max())}m")
        
    if 'temperatura_acqua' in df_f.columns:
        m4.metric("TEMP. MEDIA", f"{df_f['temperatura_acqua'].mean():.1f}°C")

    # --- MAPPA PROFESSIONALE ---
    st.subheader("📍 Distribuzione Geografica")
    
    map_styles = {
        "Scientific Terrain": "stamen-terrain",
        "Dark Navigation": "carto-darkmatter",
        "Light Map": "carto-positron"
    }

    fig = px.scatter_mapbox(
        df_f,
        lat="lat",
        lon="lon",
        color="specie",
        size=count_col if count_col else None,
        hover_name="specie",
        hover_data=list(df_f.columns),
        zoom=5,
        height=700,
        mapbox_style=map_styles[view_mode],
        color_discrete_sequence=px.colors.qualitative.Bold
    )

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)

    # --- GRAFICI ANALITICI ---
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Densità Popolazione")
        fig_bar = px.bar(df_f, x="specie", y=count_col if count_col else None, color="specie")
        st.plotly_chart(fig_bar, use_container_width=True)
    with c2:
        st.subheader("🌡️ Analisi Ambientale")
        if 'temperatura_acqua' in df_f.columns and 'profondita_mare' in df_f.columns:
            fig_scat = px.scatter(df_f, x="temperatura_acqua", y="profondita_mare", color="specie")
            fig_scat.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_scat, use_container_width=True)

    # --- DATABASE (Corretto senza errore Style) ---
    with st.expander("📂 Ispezione Database Completo"):
        # Visualizzazione tabella pulita per evitare ImportError
        st.dataframe(df_f, use_container_width=True)
        # Tasto Download CSV
        csv = df_f.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Scarica Dati (CSV)", csv, "report_ocean_track.csv", "text/csv")
