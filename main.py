import streamlit as st
import pandas as pd
import mysql.connector
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Google Sheets setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
import json
creds_dict = json.loads(st.secrets["gcp_service_account"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("Aceapp").worksheet("Esa výsledky")

# --- DB connection ---
@st.cache_data
def load_data():
    conn = mysql.connector.connect(
        host="db4free.net",
        user="paajicek",
        password="Bohemka1905",
        database="esatenis"
    )
    query = "SELECT * FROM Esa_prepared"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- Calculation logic ---
def calculate(server, receiver):
    gender = server["Gender"]
    ah = server["ah"]
    df_val = server["df"]
    va_receiver = receiver["va"]

    serves = 70 if gender == "M" else 65
    tour_avg = 0.089 if gender == "M" else 0.042

    aces = serves * ah * (va_receiver / tour_avg)
    dfs = serves * df_val
    percent_aces = ah * 100
    percent_received = server["va"] * 100

    return round(aces, 2), round(dfs, 2), round(percent_aces, 2), round(percent_received, 2), df_val * 100

# --- Streamlit UI ---
st.title("Tenisová esa a dvojchyby")
data = load_data()

gender_filter = st.radio("Filtrovat hráče podle pohlaví", ("Všichni", "Muži", "Ženy"))

if gender_filter == "Muži":
    filtered_data = data[data["Gender"] == "M"]
elif gender_filter == "Ženy":
    filtered_data = data[data["Gender"] == "F"]
else:
    filtered_data = data

players = sorted(filtered_data["Player"].tolist())
player1_name = st.selectbox("Vyber prvního hráče", players)
player2_name = st.selectbox("Vyber druhého hráče", players, index=1)

if st.button("Vypočítat"):
    p1 = data[data["Player"] == player1_name].iloc[0]
    p2 = data[data["Player"] == player2_name].iloc[0]

    aces1, dfs1, perc_ah1, perc_va1, perc_df1 = calculate(p1, p2)
    aces2, dfs2, perc_ah2, perc_va2, perc_df2 = calculate(p2, p1)

    total_aces = round(aces1 + aces2, 2)
    total_dfs = round(dfs1 + dfs2, 2)

    st.write(f"### Výsledky")
    st.write(f"{player1_name}: {aces1} es, {dfs1} dvojchyb, {perc_ah1}% es, {perc_va1}% přijatých es")
    st.write(f"{player2_name}: {aces2} es, {dfs2} dvojchyb, {perc_ah2}% es, {perc_va2}% přijatých es")
    st.write(f"**Celkem: {total_aces} es, {total_dfs} dvojchyb**")

    # Zápis do Google Sheets ve správném pořadí
    sheet.append_row([
        player1_name, perc_ah1, perc_va1, perc_df1, aces1, dfs1,
        player2_name, perc_ah2, perc_va2, perc_df2, aces2, dfs2,
        total_aces, total_dfs
    ])
