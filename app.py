import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAZIONE DASHBOARD ---
st.set_page_config(page_title="Monitoraggio Cetacei PRO", layout="wide", page_icon="🐋")

# Nome del file (Attenzione alla maiuscola!)
NOME_FILE = "Avvistamenti.xlsx"

@st.cache_data
def load_data():
    try:
        df = pd.read_excel(NOME_FILE)
        # Pulizia: togliamo spazi vuoti dai nomi delle colonne
        df.columns = df.columns.str.strip()
        
        # Convertiamo la data se esiste
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
        
        # Pulizia coordinate: assicuriamoci che siano numeri
        for col in ['lat', 'lon', 'latitudine', 'longitudine', 'Lat', 'Lon']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Errore nel caricamento del file: {e}")
        return None

df = load_data()

if df is not None:
    # --- IDENTIFICAZIONE AUTOMATICA COLONNE MAPPA ---
    # Cerchiamo i nomi più comuni per latitudine e longitudine
    col_lat = next((c for c in df.columns if c.lower() in ['lat', 'latitudine', 'latitude']), None)
    col_lon = next((c for c in df.columns if c.lower() in ['lon', 'longitudine', 'longitude']), None)
    col_specie = next((c for c in df.columns if c.lower() in ['specie', 'specie avvistata']), 'specie')

    # --- TITOLO E ALERT ---
    st.title("🌊 Portale Scientifico Avvistamenti")
    
    if "Gordazzo" in df[col_specie].astype(str).values:
        st.warning("✨ **RILEVAMENTO SPECIALE**: Sono stati avvistati dei Gordazzi! Controlla la mappa.")

    # --- METRICHE IN ALTO ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Totale Avvistamenti", len(df))
    if 'n_esemplari' in df.columns:
        m1.metric("Esemplari Totali", int(df['n_esemplari'].sum()))
    if 'temperatura_acqua' in df.columns:
        m3.metric("Temp. Media Acqua", f"{df['temperatura_acqua'].mean():.1f} °C")
    if 'profondita_mare' in df.columns:
        m4.metric("Profondità Max", f"{int(df['profondita_mare'].max())} m")

    # --- FILTRI LATERALE ---
    st.sidebar.header("Filtri Ricerca")
    lista_specie = df[col_specie].unique()
    specie_sel = st.sidebar.multiselect("Seleziona Specie", options=lista_specie, default=lista_specie)
    
    # Filtro dati
    df_f = df[df[col_specie].isin(specie_sel)]

    # --- TAB A SCHEDE ---
    tab_map, tab_charts, tab_data = st.tabs(["📍 Mappa Distribuzione", "📊 Analisi Scientifica", "📋 Database"])

    with tab_map:
        st.subheader("Localizzazione Geografica")
        if col_lat and col_lon:
            # Rimuoviamo righe senza coordinate per non far crashare la mappa
            df_map = df_f.dropna(subset=[col_lat, col_lon])
            
            fig_map = px.scatter_mapbox(
                df_map, 
                lat=col_lat, 
                lon=col_lon, 
                color=col_specie, 
                size="n_esemplari" if "n_esemplari" in df_map.columns else None,
                hover_name=col_specie, 
                hover_data=list(df_map.columns),
                zoom=5, 
                height=600, 
                mapbox_style="carto-positron"
            )
            fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.error("❌ Mappa non disponibile: non trovo colonne chiamate 'lat' e 'lon' (o simili) nel tuo Excel.")
            st.write("Colonne attuali nel file:", list(df.columns))

    with tab_charts:
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Suddivisione Specie")
            fig_pie = px.pie(df_f, names=col_specie, hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_right:
            st.subheader("Parametri Ambientali")
            if 'temperatura_acqua' in df_f.columns and 'profondita_mare' in df_f.columns:
                fig_env = px.scatter(df_f, x="temperatura_acqua", y="profondita_mare", color=col_specie)
                fig_env.update_yaxes(autorange="reversed")
                st.plotly_chart(fig_env, use_container_width=True)
            else:
                st.info("Aggiungi colonne 'temperatura_acqua' e 'profondita_mare' per questo grafico.")

    with tab_data:
        st.subheader("Esploratore Dati")
        st.dataframe(df_f, use_container_width=True)
        csv = df_f.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Scarica dati (CSV)", csv, "avvistamenti_filtrati.csv", "text/csv")
