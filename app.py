import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. IMPOSTAZIONI PAGINA ---
st.set_page_config(page_title="Monitoraggio Cetacei PRO", layout="wide", page_icon="🐋")

# --- 2. CARICAMENTO DATI ---
NOME_FILE = "Avvistamenti.xlsx"

@st.cache_data
def load_data():
    try:
        df = pd.read_excel(NOME_FILE)
        df.columns = df.columns.str.strip()
        # Pulizia coordinate: trasforma in numeri e toglie righe vuote
        for col in ['lat', 'lon', 'latitudine', 'longitudine', 'Lat', 'Lon']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Identificazione automatica colonne lat/lon
        c_lat = next((c for c in df.columns if c.lower() in ['lat', 'latitudine']), None)
        c_lon = next((c for c in df.columns if c.lower() in ['lon', 'longitudine']), None)
        
        return df.dropna(subset=[c_lat, c_lon]), c_lat, c_lon
    except Exception as e:
        st.error(f"Errore caricamento: {e}")
        return None, None, None

df, lat_col, lon_col = load_data()

if df is not None:
    # --- 3. SIDEBAR (FILTRI) ---
    st.sidebar.header("📊 Pannello di Controllo")
    tipo_visualizzazione = st.sidebar.radio("Stile Mappa:", ["Punti Classici", "Heatmap (Densità)"])
    
    # Filtro Specie
    col_specie = next((c for c in df.columns if c.lower() in ['specie', 'specie avvistata']), 'specie')
    specie_unid = df[col_specie].unique()
    sel_specie = st.sidebar.multiselect("Filtra per Specie:", specie_unid, default=specie_unid)
    
    # Applicazione filtri
    df_f = df[df[col_specie].isin(sel_specie)]

    # --- 4. HEADER E KPI ---
    st.title("🛰️ Dashboard Scientifica Cetacei")
    st.markdown("---")
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Punti Rilevati", len(df_f))
    k2.metric("Esemplari Totali", int(df_f['n_esemplari'].sum()) if 'n_esemplari' in df_f.columns else "N/D")
    k3.metric("Temp. Media", f"{df_f['temperatura_acqua'].mean():.1f} °C" if 'temperatura_acqua' in df_f.columns else "N/D")
    k4.metric("Profondità Max", f"{int(df_f['profondita_mare'].max())} m" if 'profondita_mare' in df_f.columns else "N/D")

    # --- 5. MAPPA PROFESSIONALE ---
    st.subheader("📍 Analisi Geografica e Hot-Spots")
    
    if tipo_visualizzazione == "Punti Classici":
        fig = px.scatter_mapbox(df_f, lat=lat_col, lon=lon_col, color=col_specie, 
                                size="n_esemplari" if "n_esemplari" in df_f.columns else None,
                                hover_name=col_specie, zoom=5, height=700,
                                mapbox_style="stamen-terrain")
    else:
        # Heatmap (Mappa di Calore)
        fig = px.density_mapbox(df_f, lat=lat_col, lon=lon_col, z="n_esemplari" if "n_esemplari" in df_f.columns else None,
                                radius=25, zoom=5, height=700,
                                mapbox_style="stamen-terrain",
                                color_continuous_scale=px.colors.sequential.YlOrRd)

    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig, use_container_width=True)

    # --- 6. GRAFICI SCIENTIFICI ---
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("📈 Distribuzione Popolazione")
        fig_bar = px.bar(df_f, x=col_specie, y="n_esemplari" if "n_esemplari" in df_f.columns else None, 
                         color=col_specie, barmode="group", template="plotly_white")
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with c2:
        st.subheader("🌡️ Correlazione Ambientale")
        if 'temperatura_acqua' in df_f.columns and 'profondita_mare' in df_f.columns:
            fig_scat = px.scatter(df_f, x="temperatura_acqua", y="profondita_mare", color=col_specie, size_max=20)
            fig_scat.update_yaxes(autorange="reversed") # Mare verso il basso
            st.plotly_chart(fig_scat, use_container_width=True)
        else:
            st.info("Aggiungi colonne 'temperatura_acqua' e 'profondita_mare' per questo grafico.")

    # --- 7. DATABASE ---
    with st.expander("📂 Esplora Database Analitico"):
        st.dataframe(df_f, use_container_width=True)
        st.download_button("📥 Scarica Report CSV", df_f.to_csv(index=False).encode('utf-8'), "dati.csv", "text/csv")
