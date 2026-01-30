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
# GLOBAL STYLE FIXES
# ==============================
st.markdown(
    """
    <style>
        /* Align header exactly with Streamlit content */
        .block-container {
            padding-top: 1.2rem;
        }

        .header {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 0.5rem;
        }

        .logo {
            height: 95px;
            width: auto;
        }

        /* Theme-aware logo switching (robust) */
        @media (prefers-color-scheme: dark) {
            .logo-light { display: none; }
        }

        @media (prefers-color-scheme: light) {
            .logo-dark { display: none; }
        }

        h1 {
            margin: 0;
            padding: 0;
            line-height: 1.05;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ==============================
# HEADER
# ==============================
st.markdown(
    """
    <div class="header">
        <img src="PF_Air_Logo black.png" class="logo logo-light">
        <img src="PF_Air_Logo white.png.jpeg" class="logo logo-dark">
        <h1>PID Controller</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# ==============================
# DESCRIPTION (UNCHANGED)
# ==============================
st.write("A General-Purpose PID controller")

# ==============================
# IMPORT PID CORE
# ==============================
from pid_core import PID

# ==============================
# SIDEBAR
# ==============================
st.sidebar.header("PID Gains")

kp = st.sidebar.slider("Kp (Proportional)", 0.0, 500.0, 20.0, 1.0, key="kp")
ki = st.sidebar.slider("Ki (Integral)", 0.0, 50.0, 0.0, 0.1, key="ki")
kd = st.sidebar.slider("Kd (Derivative)", 0.0, 100.0, 2.0, 0.5, key="kd")

st.sidebar.divider()
st.sidebar.header("Target & Safety")

setpoint = st.sidebar.slider(
    "Setpoint",
    -180.0,
    180.0,
    0.0,
    0.5,
    key="setpoint"
)

motor_output_limit = st.sidebar.slider(
    "Motor Output Limit (±)",
    0.0,
    100.0,
    50.0,
    1.0,
    key="motor_limit"
)

emergency_stop = st.sidebar.toggle("🛑 Emergency Stop", key="estop")

# ==============================
# SESSION STATE
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
pid.kp, pid.ki, pid.kd = kp, ki, kd

# ==============================
# REAL-TIME LOOP
# ==============================
dt = 0.02

if not emergency_stop:
    t_now = time.time() - st.session_state.start_time

    measured_value = (
        st.session_state.history["measurement"][-1]
        if st.session_state.history["measurement"]
        else 0.0
    )

    control = pid.update(setpoint, measured_value, dt)
    control = np.clip(control, -motor_output_limit, motor_output_limit)

    error = setpoint - measured_value

    st.session_state.history["t"].append(t_now)
    st.session_state.history["measurement"].append(measured_value)
    st.session_state.history["control"].append(control)
    st.session_state.history["error"].append(error)
else:
    pid.reset()

# ==============================
# VISUALIZATION
# ==============================
col1, col2 = st.columns(2)

with col1:
    st.subheader("System Output")
    fig1, ax1 = plt.subplots()
    ax1.plot(st.session_state.history["t"],
             st.session_state.history["measurement"],
             label="Measured Value")
    ax1.axhline(setpoint, linestyle="--", label="Setpoint")
    ax1.set_xlabel("Time (s)")
    ax1.legend()
    ax1.grid(True)
    st.pyplot(fig1)

with col2:
    st.subheader("Control Signal")
    fig2, ax2 = plt.subplots()
    ax2.plot(st.session_state.history["t"],
             st.session_state.history["control"],
             label="Controller Output")
    ax2.set_xlabel("Time (s)")
    ax2.grid(True)
    st.pyplot(fig2)

st.subheader("Error")
fig3, ax3 = plt.subplots()
ax3.plot(st.session_state.history["t"],
         st.session_state.history["error"])
ax3.set_xlabel("Time (s)")
ax3.grid(True)
st.pyplot(fig3)

# ==============================
# AUTO-REFRESH (ONLY IF RUNNING)
# ==============================
if not emergency_stop:
    time.sleep(dt)
    st.rerun()
