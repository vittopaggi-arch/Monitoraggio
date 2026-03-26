import streamlit as st
import pandas as pd
from streamlit_folium import st_folium
import folium

# --- 1. CONFIGURAZIONE ---
st.set_page_config(page_title="Monitoraggio Cetacei PRO", layout="wide")

st.title("🛰️ Sistema Cartografico Professionale Cetacei")
st.markdown("Visualizzazione geografica ad alta precisione su base OpenStreetMap.")

# --- 2. CARICAMENTO DATI ---
NOME_FILE = "Avvistamenti.xlsx"

@st.cache_data
def load_data():
    try:
        df = pd.read_excel(NOME_FILE)
        df.columns = df.columns.str.strip()
        # Pulizia coordinate: forziamo i numeri
        df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
        df['lon'] = pd.to_numeric(df['lon'], errors='coerce')
        return df.dropna(subset=['lat', 'lon'])
    except Exception as e:
        st.error(f"Errore caricamento Excel: {e}")
        return None

df = load_data()

if df is not None:
    # --- 3. SIDEBAR FILTRI ---
    st.sidebar.header("Filtri Mappa")
    specie_unid = df['specie'].unique()
    sel_specie = st.sidebar.multiselect("Seleziona Specie:", specie_unid, default=specie_unid)
    df_f = df[df['specie'].isin(sel_specie)]

    # --- 4. CREAZIONE MAPPA PROFESSIONALE (FOLIUM) ---
    st.subheader("📍 Posizionamento Geografico Avvistamenti")
    
    # Centro della mappa basato sui dati
    centro_lat = df_f['lat'].mean()
    centro_lon = df_f['lon'].mean()
    
    # Creiamo l'oggetto Mappa con griglia e scala
    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=6, control_scale=True)
    
    # Aggiungiamo i puntini (Markers) professionali
    for i, row in df_f.iterrows():
        # Creiamo un fumetto (popup) con tutti i dettagli scientifici
        html_popup = f"""
        <div style="font-family: Arial; font-size: 12px;">
            <b>Specie:</b> {row['specie']}<br>
            <b>Esemplari:</b> {row['n_esemplari']}<br>
            <b>Comportamento:</b> {row['comportamento']}<br>
            <b>Profondità:</b> {row['profondita_mare']}m
        </div>
        """
        
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=7,
            popup=folium.Popup(html_popup, max_width=200),
            color='blue' if row['specie'] != 'Gordazzo' else 'red',
            fill=True,
            fill_opacity=0.7
        ).add_to(m)

    # Visualizziamo la mappa nel sito
    st_folium(m, width=1200, height=600)

    # --- 5. ANALISI DATI ---
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Statistiche")
        st.bar_chart(df_f.groupby('specie')['n_esemplari'].sum())
    with c2:
        st.subheader("📋 Ultimi Rilevamenti")
        st.write(df_f[['data', 'specie', 'n_esemplari', 'comportamento']].tail())

else:
    st.warning("Carica il file Avvistamenti.xlsx per vedere la mappa.")
