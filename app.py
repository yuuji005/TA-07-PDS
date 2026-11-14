import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from scipy.integrate import solve_ivp
from scipy.optimize import curve_fit

st.set_page_config(page_title="Simulasi Penduduk Indonesia", layout="wide")
st.title("Simulasi Pertumbuhan Penduduk Indonesia (Model Logistik)")
st.caption("dP/dt = r·P·(1 − P/K) | Data: UN World Population Prospects 1960–2024")

def logistic_model(t, P, r, K):
    return r * P * (1 - P / K)

def logistic_analytic(t, P0, r, K):
    return K / (1 + ((K - P0) / P0) * np.exp(-r * t))

def euler(f, P0, t_end, h, args=()):
    n = int(round(t_end / h)); t = np.linspace(0, n * h, n + 1); P = np.zeros(n + 1); P[0] = P0
    for i in range(n):
        P[i + 1] = P[i] + h * f(t[i], P[i], *args)
    return t, P

def rk4(f, P0, t_end, h, args=()):
    n = int(round(t_end / h)); t = np.linspace(0, n * h, n + 1); P = np.zeros(n + 1); P[0] = P0
    for i in range(n):
        k1 = f(t[i], P[i], *args); k2 = f(t[i] + h / 2, P[i] + h * k1 / 2, *args)
        k3 = f(t[i] + h / 2, P[i] + h * k2 / 2, *args); k4 = f(t[i] + h, P[i] + h * k3, *args)
        P[i + 1] = P[i] + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6
    return t, P

@st.cache_data
def load():
    df = pd.read_csv("indonesia_population.csv")
    df["P"] = df["Population"] / 1e6
    return df

df = load()
t_data = (df["Year"] - df["Year"].min()).values.astype(float)
P_data = df["P"].values
P0 = P_data[0]
(r_fit, K_fit), _ = curve_fit(lambda t, r, K: logistic_analytic(t, P0, r, K), t_data, P_data, p0=[0.04, 350], maxfev=20000)

st.sidebar.header("Parameter")
r = st.sidebar.slider("r (laju pertumbuhan per tahun)", 0.005, 0.10, float(round(r_fit, 4)), 0.0005, format="%.4f")
K = st.sidebar.slider("K (kapasitas dukung, juta jiwa)", 285.0, 600.0, float(round(K_fit, 1)), 1.0)
metode = st.sidebar.selectbox("Metode numerik", ["Euler", "RK4", "solve_ivp"])
h = st.sidebar.select_slider("Langkah waktu h (tahun)", options=[0.1, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0], value=1.0)
horizon = st.sidebar.slider("Proyeksi sampai tahun", 2024, 2100, 2024)

t_end = t_data.max() + (horizon - 2024)
if metode == "Euler":
    t_s, P_s = euler(logistic_model, P0, t_end, h, args=(r, K))
elif metode == "RK4":
    t_s, P_s = rk4(logistic_model, P0, t_end, h, args=(r, K))
else:
    sol = solve_ivp(logistic_model, (0, t_end), [P0], args=(r, K), t_eval=np.linspace(0, t_end, 400))
    t_s, P_s = sol.t, sol.y[0]

pred = np.interp(t_data, t_s, P_s)
rmse = float(np.sqrt(np.mean((P_data - pred) ** 2)))
mape = float(np.mean(np.abs(P_data - pred) / P_data) * 100)

c1, c2, c3 = st.columns(3)
c1.metric("RMSE (juta jiwa)", f"{rmse:.2f}")
c2.metric("MAPE (%)", f"{mape:.2f}")
c3.metric(f"Penduduk {horizon} (model)", f"{P_s[-1]:.1f} juta")

fig, ax = plt.subplots(figsize=(9, 4.8))
ax.scatter(df["Year"], P_data, s=14, label="Data asli")
ax.plot(1960 + t_s, P_s, color="red", lw=2, label=f"Simulasi {metode} (h={h})")
ax.axhline(K, color="gray", ls="--", lw=1)
ax.set_xlabel("Tahun"); ax.set_ylabel("Penduduk (juta jiwa)"); ax.legend(); ax.grid(alpha=0.3)
st.pyplot(fig)
st.info("Geser r dan K untuk melihat efeknya (What-If). Nilai awal slider adalah hasil kalibrasi dari data.")
