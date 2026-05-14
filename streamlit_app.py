import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
from ta.momentum import RSIIndicator

st.title("Mini Dashboard de Análisis Técnico")

# --- GESTIÓN DE ESTADO (MEMORIA) ---
# Streamlit se reinicia de arriba a abajo en cada interacción.
# Usamos st.session_state para que los datos descargados no se borren al tocar un botón.
# De esta manera cuando se descargan los datos y se calculan los indicadores, quedan guardados en session_state.data,
# y no se pierden al hacer clic en otro botón o cambiar el selector de ticker.
# Por ende, lo que le decimos es "si no hay data en el session state, creá un diccionario vacío para guardarla".
if 'data' not in st.session_state:
    st.session_state.data = {}

# --- CACHÉ DE DATOS ---
# @st.cache_data evita descargar los mismos datos de Yahoo Finance una y otra vez,
# ahorrando tiempo y ancho de banda. Solo se ejecuta si cambian los parámetros.
#Cuando pones @st.cache_data arriba de una función, Streamlit dice: 
# "Si ya me pediste los datos de AAPL del 2022 al 2025 antes, no voy a internet de nuevo; 
# te doy la copia que guardé en el archivador".
@st.cache_data
def download_data(tickers, start, end):
    df = yf.download(tickers, start=start, end=end, group_by="column", auto_adjust=False)
    return df

# --- ENTRADA DE DATOS DEL USUARIO ---
# Input de texto para tickers (ej: "AAPL, MSFT, GOOGL")
ticker_raw = st.text_input("Ticker (uno o varios separados por espacio o coma)", value="AAPL")
start = st.date_input("Fecha inicio", value=pd.to_datetime("2022-01-01"))
end = st.date_input("Fecha fin", value=pd.to_datetime("2026-05-04"))

# Limpieza de los tickers ingresados: quitamos comas, espacios y pasamos a mayúsculas
tickers = [t.strip().upper() for t in ticker_raw.replace(",", " ").split() if t.strip()]

# --- PROCESAMIENTO AL HACER CLIC EN EL BOTÓN ---
if st.button("Cargar datos"):
    if not tickers:
        st.error("Ingresá al menos un ticker.")
        st.stop() # Detiene la ejecución si no hay texto

    # Llamada a la función con caché para descargar o cargar los datos desde la memoria si ya se descargaron antes
    df = download_data(tickers, start, end)

    #Si el df esta vació dar avisar del error.
    if df is None or df.empty:
        st.error("No se descargaron datos. Revisá el ticker y el rango de fechas.")
        st.stop()

    # Extraemos solo los precios de cierre ("Close"), 
    # vamos a tener un DataFrame con columnas por cada ticker, o una Serie si es un solo ticker
    close = df["Close"]
    # Si es un solo ticker, yfinance devuelve una Serie; la convertimos a DataFrame para iterar
    if isinstance(close, pd.Series):
        close = close.to_frame()

    # --- CÁLCULO DE INDICADORES TÉCNICOS ---
    #Para cada ticker en el DataFrame de precios de cierre, calculamos las medias móviles y el RSI,
    #y guardamos todo en un nuevo DataFrame.
    for ticker in close.columns:
        # Eliminamos valores nulos para el ticker actual
        close_ticker = close[ticker].dropna()
        # Creamos un nuevo DataFrame limpio para este activo
        df_out = pd.DataFrame(index=close_ticker.index)
        df_out["Close"] = close_ticker
        # Calculamos las medias móviles y el RSI
        df_out["SMA20"] = df_out["Close"].rolling(20).mean()
        df_out["SMA50"] = df_out["Close"].rolling(50).mean()
        rsi = RSIIndicator(close=df_out["Close"], window=14)
        df_out["RSI"] = rsi.rsi()
        # GUARDADO EN MEMORIA: Almacenamos el DataFrame procesado en el session_state
        st.session_state.data[ticker] = df_out

# --- VISUALIZACIÓN ---
# Verificamos si ya hay datos en la memoria (session_state) para mostrar el resto de la app
if st.session_state.data:
    # Creamos un selector para que el usuario elija cuál de los tickers cargados quiere ver
    available_tickers = list(st.session_state.data.keys())
    selected_ticker = st.selectbox("Elegí ticker para analizar", available_tickers)

    # Recuperamos el DataFrame específico del ticker seleccionado
    df_out = st.session_state.data[selected_ticker]

    # Gráficos: Precio con medias móviles y RSI
    st.subheader(f"Precio y Medias Móviles - {selected_ticker}")
    fig, ax = plt.subplots()
    ax.plot(df_out.index, df_out["Close"], label="Close")
    ax.plot(df_out.index, df_out["SMA20"], label="SMA20")
    ax.plot(df_out.index, df_out["SMA50"], label="SMA50")
    ax.legend()
    st.pyplot(fig)

    st.subheader(f"RSI - {selected_ticker}")
    fig2, ax2 = plt.subplots()
    ax2.plot(df_out.index, df_out["RSI"], label="RSI")
    ax2.axhline(70, color="red", linestyle="--")
    ax2.axhline(30, color="green", linestyle="--")
    ax2.legend()
    st.pyplot(fig2)
else:
    # Si no hay datos cargados, mostramos un mensaje informativo
    st.info("Cargá datos primero presionando 'Cargar datos'.")
