import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# --- CONFIGURAZIONE ESTETICA AVANZATA ---
st.set_page_config(page_title="OCEAN-COMMAND PRO", layout="wide", page_icon="🛰️")

# CSS Custom per UI Accattivante
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    
    .main { background-color: #050a14; color: #e0e0e0; }
    .stMetric { 
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 20px; border-radius: 15px; border: 1px solid #38bdf8;
        box-shadow: 0 4px 15px rgba(56, 189, 248, 0.2);
    }
    h1, h2, h3 { font-family: 'Orbitron', sans-serif; color: #38bdf8; text-transform: uppercase; letter-spacing: 2px; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #1e293b; border-radius: 10px; padding: 10px 20px; color: white; border: 1px solid #334155;
    }
    .stTabs [aria-selected="true"] { background-color: #38bdf8 !format; color: #050a14 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- CARICAMENTO DATI ---
@st.cache_data
def load_full_data():
    try:
        df = pd.read_excel("Avvistamenti.xlsx")
        df.columns = df.columns.str.strip().str.lower()
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
        st.error(f"SYSTEM ERROR: {e}")
        return None

df = load_full_data()

if df is not None:
    # --- SIDEBAR HI-TECH ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2040/2040523.png", width=80)
        st.title("COMMAND CENTER")
        st.markdown("---")
        
        map_style = st.selectbox("TIPO SENSORE MAPPA", ["Satellite Ibrido", "Dark Matter", "Terrain Scientific"])
        
        specie_filter = st.multiselect("SPECIE TARGET", df['specie'].unique(), default=df['specie'].unique())
        
        # Filtro Data Slide
        if 'data' in df.columns:
            start_date, end_date = st.select_slider(
                "TIMELINE DI ANALISI",
                options=sorted(df['data'].dt.date.unique()),
                value=(df['data'].min().date(), df['data'].max().date())
            )
            df_f = df[(df['specie'].isin(specie_filter)) & (df['data'].dt.date >= start_date) & (df['data'].dt.date <= end_date)]
        else:
            df_f = df[df['specie'].isin(specie_filter)]

    # --- TOP METRICS (ANIMATED STYLE) ---
    st.title("🛰️ OCEAN-COMMAND | Cetacean Intelligence")
    
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("TRACKS", len(df_f), delta="LIVE")
    with m2: st.metric("INDIVIDUALS", int(df_f['count'].sum()) if 'count' in df_f.columns else "N/A")
    with m3: st.metric("AVG TEMP", f"{df_f['temperatura_acqua'].mean():.1f}°C" if 'temperatura_acqua' in df_f.columns else "N/A")
    with m4: st.metric("MAX DEPTH", f"{int(df_f['profondita_mare'].max())}m" if 'profondita_mare' in df_f.columns else "N/A")

    st.markdown("---")

    # --- LAYOUT A SCHEDE ---
    tab_geo, tab_science, tab_raw = st.tabs(["🌐 GEOSPATIAL ENGINE", "📊 SCIENTIFIC ANALYTICS", "💾 RAW DATA"])

    with tab_geo:
        # Mappa Satellitare ad alta risoluzione
        st.subheader("Rilevamento Posizione Satellitare")
        
        styles = {"Satellite Ibrido": "white-bg", "Dark Matter": "carto-darkmatter", "Terrain Scientific": "stamen-terrain"}
        
        fig_map = px.scatter_mapbox(
            df_f, lat="lat", lon="lon", color="specie", size="count" if "count" in df_f.columns else None,
            hover_name="specie", hover_data=list(df_f.columns), zoom=6, height=750,
            mapbox_style=styles[map_style], color_discrete_sequence=px.colors.qualitative.Vivid
        )
        
        if map_style == "Satellite Ibrido":
            fig_map.update_layout(mapbox_layers=[{
                "below": 'traces', "sourcetype": "raster",
                "source": ["https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"]
            }])
        
        fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig_map, use_container_width=True)

    with tab_science:
        c1, c2 = st.columns(2)
        
        with c1:
            st.subheader("Gerarchia Comportamentale")
            # Sunburst Chart (Specie -> Comportamento)
            fig_sun = px.sunburst(df_f, path=['specie', 'comportamento'], values='count' if 'count' in df_f.columns else None,
                                 color='specie', template="plotly_dark")
            st.plotly_chart(fig_sun, use_container_width=True)
            
        with c2:
            st.subheader("Profilo Ambientale (3D Scatter)")
            # Grafico 3D se possibile, altrimenti Scatter avanzato
            fig_env = px.scatter(df_f, x="temperatura_acqua", y="profondita_mare", size="count" if "count" in df_f.columns else None,
                                color="specie", hover_data=['comportamento'], template="plotly_dark")
            fig_env.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_env, use_container_width=True)
            
        st.markdown("---")
        st.subheader("Trend Temporale degli Avvistamenti")
        if 'data' in df_f.columns:
            df_trend = df_f.groupby([df_f['data'].dt.date, 'specie']).size().reset_index(name='count')
            fig_trend = px.line(df_trend, x='data', y='count', color='specie', markers=True, template="plotly_dark")
            st.plotly_chart(fig_trend, use_container_width=True)

    with tab_raw:
        st.subheader("Terminal Ispezione Dati")
        st.dataframe(df_f, use_container_width=True)
        st.download_button("📥 EXPORT DATABASE (CSV)", df_f.to_csv(index=False).encode('utf-8'), "ocean_data.csv", "text/csv")

else:
    st.error("DATABASE NON RILEVATO. Caricare 'Avvistamenti.xlsx' nel repository.")
