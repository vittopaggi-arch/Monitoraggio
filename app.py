import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURAZIONE PAGINA (Layout Largo e Titolo) ---
st.set_page_config(page_title="Monitoraggio Cetacei PRO", layout="wide", page_icon="🐋")

# --- 2. HEADER E TITOLO ---
st.title("🛰️ Sistema di Monitoraggio Geografico Cetacei")
st.markdown("Visualizzazione professionale degli avvistamenti basata sui dati Excel.")

# --- 3. CARICAMENTO DATI ---
# Nome del tuo file Excel (assicurati che sia esattamente questo nel tuo repository)
NOME_FILE = "Avvistamenti.xlsx"

@st.cache_data
def load_data():
    try:
        # Carichiamo l'Excel
        df = pd.read_excel(NOME_FILE)
        
        # Puliamo i nomi delle colonne (togliamo spazi vuoti accidentali)
        df.columns = df.columns.str.strip()
        
        # --- PULIZIA COORDINATE ---
        # Cerchiamo colonne lat/lon standard (lat, lon, Lat, Lon, lat, lon)
        c_lat = next((c for c in df.columns if c.lower() == 'lat'), None)
        c_lon = next((c for c in df.columns if c.lower() == 'lon'), None)
        
        # Se non troviamo lat/lon, proviamo lat, lon
        if not c_lat or not c_lon:
            c_lat = next((c for c in df.columns if c.lower() == 'lat'), None)
            c_lon = next((c for c in df.columns if c.lower() == 'lon'), None)
            
        # Se non troviamo nemmeno quelli, proviamo lat, lon
        if not c_lat or not c_lon:
            c_lat = next((c for c in df.columns if c.lower() == 'lat'), None)
            c_lon = next((c for c in df.columns if c.lower() == 'lon'), None)
        
        # Se troviamo le colonne, assicuriamoci che siano numeri puliti
        if c_lat and c_lon:
            df[c_lat] = pd.to_numeric(df[c_lat], errors='coerce')
            df[c_lon] = pd.to_numeric(df[c_lon], errors='coerce')
            # Rimuoviamo righe senza coordinate valide
            df = df.dropna(subset=[c_lat, c_lon])
            return df, c_lat, c_lon
        
        return None, None, None
    except Exception as e:
        st.error(f"Errore critico nel caricamento: {e}")
        return None, None, None

df, lat_col, lon_col = load_data()

# --- 4. VERIFICA E VISUALIZZAZIONE MAPPA ---
if df is not None and lat_col and lon_col:
    
    # Cerchiamo la colonna Specie per i colori
    c_specie = next((c for c in df.columns if c.lower() in ['specie', 'specie avvistata']), None)
    
    # --- FILTRO LATERALE ---
    st.sidebar.header("Filtra Specie")
    if c_specie:
        tutte_le_specie = df[c_specie].unique()
        specie_scelte = st.sidebar.multiselect("Seleziona Specie", tutte_le_specie, default=tutte_le_specie)
        df_f = df[df[c_specie].isin(specie_scelte)]
    else:
        df_f = df

    # --- MAPPA PROFESSIONALE (Puntini Visibili!) ---
    st.subheader("📍 Mappa Geografica degli Avvistamenti")
    st.markdown("Usa il mouse per navigare, fare zoom e vedere i dettagli.")
    
    # Creiamo la mappa a punti (scatter) con stile professionale
    fig_map = px.scatter_mapbox(
        df_f, 
        lat=lat_col, 
        lon=lon_col, 
        color=c_specie if c_specie else None, # Colore diverso per specie
        size="n_esemplari" if "n_esemplari" in df_f.columns else None, # Dimensione del punto basata sul numero esemplari
        hover_name=c_specie if c_specie else None, # Nome al passaggio del mouse
        hover_data=list(df_f.columns), # Altri dati al passaggio del mouse
        zoom=5, # Zoom iniziale
        height=700, # Altezza della mappa
        mapbox_style="stamen-terrain", # Stile professionale (mostra coste e rilievi)
        color_discrete_sequence=px.colors.qualitative.Prism # Scala colori professionale
    )
    
    # Rimuoviamo i margini bianchi per occupare tutto lo spazio
    fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    
    # Mostriamo la mappa
    st.plotly_chart(fig_map, use_container_width=True)

    # --- ANALISI AGGIUNTIVA ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📊 Avvistamenti per Specie")
        if c_specie and 'n_esemplari' in df_f.columns:
            fig_bar = px.bar(df_f, x=c_specie, y='n_esemplari', color=c_specie, barmode='group')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Aggiungi colonne 'specie' e 'n_esemplari' per questo grafico.")
            
    with col2:
        st.subheader("🌡️ Profilo Ambientale")
        if 'temperatura_acqua' in df_f.columns and 'profondita_mare' in df_f.columns:
            fig_env = px.scatter(df_f, x="temperatura_acqua", y="profondita_mare", color=c_specie if c_specie else None)
            fig_env.update_yaxes(autorange="reversed") # Mare verso il basso
            st.plotly_chart(fig_env, use_container_width=True)
        else:
            st.info("Aggiungi colonne 'temperatura_acqua' e 'profondita_mare' per questo grafico.")

    # --- DATABASE ---
    with st.expander("Vedi Database completo"):
        st.dataframe(df_f, use_container_width=True)

else:
    st.error("❌ Mappa non disponibile.")
    if not df is None:
        st.warning("⚠️ Non riesco a trovare le colonne delle coordinate. Assicurati che nel tuo Excel si chiamino esattamente `lat` e `lon` (o `lat`, `lon`).")
        st.write("Le colonne che ho trovato nel tuo file sono:", list(df.columns) if not df is None else [])
    else:
        st.info("Verifica che il file 'Avvistamenti.xlsx' sia stato caricato correttamente su GitHub.")
