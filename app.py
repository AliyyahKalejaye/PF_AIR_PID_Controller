import time
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="Universal PID Controller",
    layout="wide"
)

# ==============================
# LOGO (BLACK / WHITE AUTO-SWITCH)
# ==============================
logo_col, _ = st.columns([1, 7])

with logo_col:
    st.markdown(
        """
        <style>
            .logo {
                height: 110px;
                width: auto;
                display: none;
            }

            /* Light mode → black logo */
            html:not([data-theme="dark"]) .logo-black {
                display: block;
            }

            /* Dark mode → white logo */
            html[data-theme="dark"] .logo-white {
                display: block;
            }

            h1 {
                margin-top: 0.3rem !important;
            }
        </style>

        <img src="PF_Air_Logo black.png"
             class="logo logo-black"
             alt="Logo">

        <img src="PF_Air_Logo white.png.jpeg"
             class="logo logo-white"
             alt="Logo">
        """,
        unsafe_allow_html=True
    )

# ==============================
# TITLE & DESCRIPTION
# ==============================
st.title("PID Controller")

st.write(
    "A General-Purpose PID Tuning Dashboard That Adapts To Different Plants."
)

# ==============================
# IMPORT PURE PID CORE
# ==============================
from pid_core import PID

# ==============================
# SIDEBAR — CONTROLLER CONFIG
# ==============================
st.sidebar.header("PID Gains")

kp = st.sidebar.slider("Kp (Proportional)", 0.0, 100.0, 10.0, 0.5)
ki = st.sidebar.slider("Ki (Integral)", 0.0, 10.0, 0.0, 0.05)
kd = st.sidebar.slider("Kd (Derivative)", 0.0, 20.0, 1.0, 0.1)

st.sidebar.divider()

st.sidebar.header("Target & Safety")

setpoint = st.sidebar.slider(
    "Setpoint",
    min_value=-1000.0,
    max_value=1000.0,
    value=0.0,
    step=1.0
)

output_limit = st.sidebar.slider(
    "Output Limit (±)",
    0.0,
    100.0,
    50.0,
    1.0
)

emergency_stop = st.sidebar.toggle("🛑 Emergency Stop")

# ==============================
# SESSION STATE INIT
# ==============================
if "pid" not in st.session_state:
    st.session_state.pid = PID(kp, ki, kd)

if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()

if "history" not in st.session_state:
    st.session_state.history = {
        "t": [],
        "measurement": [],
        "control": [],
        "error": []
    }

pid = st.session_state.pid
pid.kp = kp
pid.ki = ki
pid.kd = kd

# ==============================
# REAL-TIME LOOP
# ==============================
dt = 0.02
t_now = time.time() - st.session_state.start_time

# --------------------------------------------------
# 🔌 MEASUREMENT SOURCE (REPLACE FOR REAL HARDWARE)
# --------------------------------------------------
measured_value = (
    st.session_state.history["measurement"][-1]
    if st.session_state.history["measurement"]
    else 0.0
)

# ==============================
# CONTROL COMPUTATION
# ==============================
if emergency_stop:
    control = 0.0
    pid.reset()
else:
    control = pid.update(setpoint, measured_value, dt)
    control = np.clip(control, -output_limit, output_limit)

error = setpoint - measured_value

# ==============================
# STORE DATA
# ==============================
st.session_state.history["t"].append(t_now)
st.session_state.history["measurement"].append(measured_value)
st.session_state.history["control"].append(control)
st.session_state.history["error"].append(error)

# ==============================
# VISUALIZATION
# ==============================
col1, col2 = st.columns(2)

with col1:
    st.subheader("System Output")

    fig1, ax1 = plt.subplots()
    ax1.plot(
        st.session_state.history["t"],
        st.session_state.history["measurement"],
        label="Measured Value"
    )
    ax1.axhline(setpoint, linestyle="--", label="Setpoint")
    ax1.set_xlabel("Time (s)")
    ax1.legend()
    ax1.grid(True)
    st.pyplot(fig1)

with col2:
    st.subheader("Control Signal")

    fig2, ax2 = plt.subplots()
    ax2.plot(
        st.session_state.history["t"],
        st.session_state.history["control"],
        label="Controller Output"
    )
    ax2.set_xlabel("Time (s)")
    ax2.grid(True)
    st.pyplot(fig2)

st.subheader("Error")

fig3, ax3 = plt.subplots()
ax3.plot(
    st.session_state.history["t"],
    st.session_state.history["error"],
    label="Error"
)
ax3.set_xlabel("Time (s)")
ax3.grid(True)
st.pyplot(fig3)

# ==============================
# AUTO-REFRESH
# ==============================
time.sleep(dt)
st.rerun()
