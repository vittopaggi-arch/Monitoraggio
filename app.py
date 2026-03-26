import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURAZIONE ESTETICA AVANZATA ---
st.set_page_config(page_title="Gordazzoni Institute Research", layout="wide", page_icon="🐋")

# CSS Custom per UI Accattivante e Font Futuristico
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    
    .main { background-color: #050a14; color: #e0e0e0; }
    .stMetric { 
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 20px; border-radius: 15px; border: 1px solid #38bdf8;
        box-shadow: 0 4px 15px rgba(56, 189, 248, 0.2);
    }
    h1 { font-family: 'Orbitron', sans-serif; color: #38bdf8; text-transform: uppercase; letter-spacing: 3px; font-size: 3rem !important; }
    h2, h3 { font-family: 'Orbitron', sans-serif; color: #38bdf8; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #1e293b; border-radius: 10px; padding: 10px 20px; color: white; border: 1px solid #334155;
    }
    .stTabs [aria-selected="true"] { background-color: #38bdf8 !important; color: #050a14 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CARICAMENTO DATI ---
@st.cache_data
def load_full_data():
    try:
        df = pd.read_excel("Avvistamenti.xlsx")
        df.columns = df.columns.str.strip().str.lower()
        # Mapping flessibile per i nomi delle colonne
        col_map = {'specie avvistata': 'specie', 'n_esemplari': 'count', 'latitudine': 'lat', 'longitudine': 'lon'}
        df = df.rename(columns=col_map)
        
        if 'lat' in df.columns:
            df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
            df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
            df = df.dropna(subset=['lat', 'lon'])
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"DATABASE ERROR: {e}")
        return None

df = load_full_data()

if df is not None:
    # --- SIDEBAR HI-TECH ---
    with st.sidebar:
        st.title("🛰️ NAVIGATION")
        st.markdown("---")
        
        map_style = st.selectbox("SENSORE MAPPA", ["Satellite Ibrido", "Dark Navigation", "Scientific Terrain"])
        
        specie_filter = st.multiselect("TARGET SPECIE", df['specie'].unique(), default=df['specie'].unique())
        
        # Filtro Data se presente
        if 'data' in df.columns:
            min_d, max_d = df['data'].min().date(), df['data'].max().date()
            d_range = st.date_input("PERIODO DI ANALISI", [min_d, max_d])
            df_f = df[(df['specie'].isin(specie_filter)) & (df['data'].dt.date >= d_range[0]) & (df['data'].dt.date <= d_range[1])]
        else:
            df_f = df[df['specie'].isin(specie_filter)]

    # --- TITOLO RICHIESTO ---
    st.title("Gordazzoni Institute Research")
    st.markdown("#### *Advanced Oceanographic Monitoring & Species Tracking*")
    
    # KPI Row
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("TRACKS", len(df_f))
    with m2: st.metric("INDIVIDUALS", int(df_f['count'].sum()) if 'count' in df_f.columns else "N/A")
    with m3: st.metric("AVG TEMP", f"{df_f['temperatura_acqua'].mean():.1f}°C" if 'temperatura_acqua' in df_f.columns else "N/A")
    with m4: st.metric("MAX DEPTH", f"{int(df_f['profondita_mare'].max())}m" if 'profondita_mare' in df_f.columns else "N/A")

    st.markdown("---")

    # --- LAYOUT A SCHEDE ---
    tab_geo, tab_science, tab_data = st.tabs(["🌐 GEOSPATIAL MAP", "📊 ANALYTICS", "💾 DATASET"])

    with tab_geo:
        st.subheader("Rilevamento Posizione Satellitare")
        
        styles = {"Satellite Ibrido": "white-bg", "Dark Navigation": "carto-darkmatter", "Scientific Terrain": "stamen-terrain"}
        
        fig_map = px.scatter_mapbox(
            df_f, lat="lat", lon="lon", color="specie", size="count" if "count" in df_f.columns else None,
            hover_name="specie", hover_data=list(df_f.columns), zoom=6, height=750,
            mapbox_style=styles[map_style], color_discrete_sequence=px.colors.qualitative.Prism
        )
        
        if map_style == "Satellite Ibrido":
            fig_map.update_layout(mapbox_layers=[{
                "below": 'traces', "sourcetype": "raster",
                "source": ["https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"]
            }])
        
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_map, use_container_width=True)

    with tab_science:
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Distribuzione per Specie")
            fig_sun = px.sunburst(df_f, path=['specie', 'comportamento'], values='count' if 'count' in df_f.columns else None,
                                 template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_sun, use_container_width=True)
            
        with c2:
            st.subheader("Correlazione Profondità/Temperatura")
            fig_env = px.scatter(df_f, x="temperatura_acqua", y="profondita_mare", color="specie", 
                                size="count" if "count" in df_f.columns else None, template="plotly_dark")
            fig_env.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_env, use_container_width=True)

    with tab_data:
        st.subheader("Data Inspection Unit")
        st.dataframe(df_f, use_container_width=True)
        st.download_button("📥 DOWNLOAD REPORT (CSV)", df_f.to_csv(index=False).encode('utf-8'), "gordazzoni_data.csv", "text/csv")

else:
    st.error("CARICARE IL FILE 'Avvistamenti.xlsx' PER ATTIVARE IL SISTEMA.")
