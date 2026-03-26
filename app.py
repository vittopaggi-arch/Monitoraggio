import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAZIONE DASHBOARD ---
st.set_page_config(page_title="Monitoraggio Cetacei PRO", layout="wide", page_icon="🐋")

# Nome del file aggiornato (Attenzione alla maiuscola!)
NOME_FILE = "Avvistamenti.xlsx"

@st.cache_data
def load_data():
    # Caricamento e pulizia
    df = pd.read_excel(NOME_FILE)
    df.columns = df.columns.str.strip() # Rimuove spazi nei nomi colonne
    if 'data' in df.columns:
        df['data'] = pd.to_datetime(df['data'])
    return df

try:
    df = load_data()

    # --- TITOLO E ALERT GORDAZZI ---
    st.title("🌊 Portale Scientifico Avvistamenti")
    
    if "Gordazzo" in df['specie'].values:
        st.warning("✨ **RILEVAMENTO SPECIALE**: La flotta ha individuato dei Gordazzi! Controlla la mappa per la posizione esatta.")

    # --- METRICHE IN ALTO ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Totale Avvistamenti", len(df))
    m2.metric("Esemplari Totali", int(df['n_esemplari'].sum()))
    m3.metric("Temp. Media Acqua", f"{df['temperatura_acqua'].mean():.1f} °C")
    m4.metric("Profondità Max", f"{int(df['profondita_mare'].max())} m")

    # --- FILTRI LATERALE ---
    st.sidebar.header("Filtri Ricerca")
    specie_sel = st.sidebar.multiselect("Seleziona Specie", options=df['specie'].unique(), default=df['specie'].unique())
    
    # Filtro dinamico sui dati
    df_f = df[df['specie'].isin(specie_sel)]

    # --- TAB A SCHEDE ---
    tab_map, tab_charts, tab_data = st.tabs(["📍 Mappa", "📊 Analisi Scientifica", "📋 Database"])

    with tab_map:
        st.subheader("Distribuzione Geografica")
        # Mappa professionale
        fig_map = px.scatter_mapbox(df_f, lat="lat", lon="lon", color="specie", size="n_esemplari",
                                  hover_name="specie", hover_data=["comportamento", "profondita_mare"],
                                  zoom=5, height=600, mapbox_style="stamen-terrain")
        st.plotly_chart(fig_map, use_container_width=True)

    with tab_charts:
        col_left, col_right = st.columns(2)
        with col_left:
            st.subheader("Suddivisione Specie")
            fig_pie = px.pie(df_f, names='specie', values='n_esemplari', hole=0.4,
                             color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_right:
            st.subheader("Correlazione Profondità/Temperatura")
            fig_env = px.scatter(df_f, x="temperatura_acqua", y="profondita_mare", 
                                color="specie", size="n_esemplari")
            fig_env.update_yaxes(autorange="reversed") # Il fondo del mare è in basso
            st.plotly_chart(fig_env, use_container_width=True)

    with tab_data:
        st.subheader("Esploratore Dati")
        st.dataframe(df_f, use_container_width=True)
        # Bottone Download
        csv = df_f.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Scarica dati (CSV)", csv, "avvistamenti_filtrati.csv", "text/csv")

except FileNotFoundError:
    st.error(f"❌ Errore: Non trovo il file '{NOME_FILE}' nel repository.")
    st.info("Assicurati che il file Excel si chiami esattamente così, con la 'A' maiuscola.")
except Exception as e:
    st.error(f"Si è verificato un errore imprevisto: {e}")
