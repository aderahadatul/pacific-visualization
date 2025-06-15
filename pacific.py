import streamlit as st
import pandas as pd
import plotly.express as px

# === Load Data 1: Summary of Disaster Effects by Sector ===
xls = pd.ExcelFile("Summary of Disaster Effects by Sector_0.xlsx")
df = xls.parse(xls.sheet_names[0])
data_raw = df.iloc[2:].reset_index(drop=True)
data_raw.columns = [
    "Sector",
    "Damage (VT millions)",
    "Losses (VT millions)",
    "Total (VT millions)",
    "Private Share (%)",
    "Public Share (%)",
    "Lost Personal Income (VT millions)"
]
data_clean = data_raw[1:].copy()
data_clean = data_clean[data_clean["Sector"].notna()].reset_index(drop=True)

# Konversi ke numerik
for col in data_clean.columns[1:]:
    data_clean[col] = pd.to_numeric(data_clean[col], errors='coerce')

# Hitung rasio dengan menghindari pembagian nol
data_clean["Losses to Damage Ratio"] = data_clean["Losses (VT millions)"] / data_clean["Damage (VT millions)"]
data_clean["Losses to Damage Ratio"].replace([float("inf"), -float("inf")], None, inplace=True)
data_clean = data_clean[data_clean["Losses to Damage Ratio"].notnull()]

# Hapus baris-baris tidak relevan
data1 = data_clean[~data_clean["Sector"].isin(["Grand Total", "Source: Vanuatu PDNA, Pam 2015"])].copy()

# === Load Data 2: Summary of Recovery and Reconstruction Needs ===
df2 = pd.read_csv("Summary of recovery and reconstruction needs.csv")
df2_clean = df2.iloc[1:].copy()
df2_clean.columns = [
    "Sector",
    "Recovery Needs (VT millions)",
    "Reconstruction Needs (VT millions)",
    "Total Needs (VT millions)",
    "Private Share (%)",
    "Public Share (%)",
    "Drop1", "Drop2", "Drop3"
]
df2_clean = df2_clean.loc[:, df2_clean.columns[:6]]
df2_clean = df2_clean[df2_clean["Sector"].notna()].copy()

for col in df2_clean.columns[1:]:
    df2_clean[col] = df2_clean[col].astype(str).str.replace(",", "").astype(float)

# === Streamlit Layout ===
st.set_page_config(page_title="Dashboard Bencana Vanuatu", layout="wide")
st.sidebar.title("Pilih Indikator")
indikator = st.sidebar.selectbox(
    "Indikator Utama",
    ["Total Dampak Ekonomi", "Rasio Losses/Damage", "Kebutuhan Recovery"]
)

st.title("Dashboard Visualisasi Dampak Bencana Vanuatu 2015")

# === Pilihan Filter Interaktif ===
available_sectors = data1["Sector"].unique().tolist()
selected_sectors = st.sidebar.multiselect("Filter Sektor", available_sectors, default=available_sectors)

filtered_data1 = data1[data1["Sector"].isin(selected_sectors)]
filtered_data2 = df2_clean[df2_clean["Sector"].isin(selected_sectors)]

# === Visualisasi 1: Total Dampak Ekonomi ===
if indikator == "Total Dampak Ekonomi":
    st.subheader("Visualisasi Total Kerusakan dan Kerugian per Sektor")
    fig1 = px.bar(
        filtered_data1,
        x="Sector",
        y=["Damage (VT millions)", "Losses (VT millions)", "Total (VT millions)"],
        barmode="group",
        labels={"value": "Kerugian (juta VT)", "variable": "Jenis Dampak"},
        title="Perbandingan Dampak Ekonomi Bencana per Sektor",
        hover_data={"Sector": True}
    )
    fig1.update_layout(yaxis_tickformat=",")
    st.plotly_chart(fig1, use_container_width=True)

# === Visualisasi 2: Rasio Losses/Damage ===
elif indikator == "Rasio Losses/Damage":
    st.subheader("Visualisasi Rasio Kerugian terhadap Kerusakan")

    # Cek jika ada data valid
    if not filtered_data1.empty and filtered_data1["Losses to Damage Ratio"].notnull().any():
        # Pastikan tidak ada inf/nan
        filtered_data1 = filtered_data1.replace([float("inf"), -float("inf")], None)
        filtered_data1 = filtered_data1[filtered_data1["Losses to Damage Ratio"].notnull()]

        min_ratio = float(filtered_data1["Losses to Damage Ratio"].min())
        max_ratio = float(filtered_data1["Losses to Damage Ratio"].max())

        # Batasi max slider agar tidak lebih dari 5.0 untuk kestabilan UI
        upper_limit = min(max_ratio, 5.0)

        ratio_range = st.sidebar.slider(
            "Filter Rasio Losses ÷ Damage",
            min_value=0.0,
            max_value=float(upper_limit),
            value=(float(min_ratio), float(upper_limit)),
            step=0.1
        )

        ratio_filtered = filtered_data1[
            (filtered_data1["Losses to Damage Ratio"] >= ratio_range[0]) &
            (filtered_data1["Losses to Damage Ratio"] <= ratio_range[1])
        ]

        fig2 = px.bar(
            ratio_filtered.sort_values("Losses to Damage Ratio", ascending=True),
            x="Losses to Damage Ratio",
            y="Sector",
            orientation="h",
            labels={"Losses to Damage Ratio": "Rasio Losses ÷ Damage"},
            title="Rasio Kerugian Ekonomi dibanding Kerusakan Fisik per Sektor",
            hover_data=["Damage (VT millions)", "Losses (VT millions)"]
        )
        fig2.update_traces(texttemplate="%{x:.2f}", textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Tidak ada data rasio yang valid untuk ditampilkan.")

# === Visualisasi 3: Kebutuhan Recovery dan Reconstruction ===
elif indikator == "Kebutuhan Recovery":
    st.subheader("Visualisasi Kebutuhan Recovery dan Reconstruction")
    fig3 = px.bar(
        filtered_data2,
        x="Sector",
        y=["Recovery Needs (VT millions)", "Reconstruction Needs (VT millions)"],
        barmode="group",
        labels={"value": "Nilai (juta VT)", "variable": "Jenis Kebutuhan"},
        title="Perbandingan Kebutuhan Recovery dan Reconstruction per Sektor",
        hover_data=["Public Share (%)", "Private Share (%)"]
    )
    fig3.update_layout(yaxis_tickformat=",")
    st.plotly_chart(fig3, use_container_width=True)

# === Footer ===
st.markdown("---")
st.markdown("📊 Data bersumber dari [Pacific Data Hub](https://data.gouv.nc)")
st.markdown("🔗 Lihat versi analisis di Google Colab: [tautan](https://colab.research.google.com/)")
