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
st.markdown(
    """
    <style>
        .header {
            display: flex;
            align-items: center;
            gap: 12px;               /* natural spacing */
            margin-bottom: -10px;    /* reduce gap to content */
        }

        .logo {
            height: 90px;            /* noticeable but professional */
            width: auto;
            display: none;
        }

        /* Light mode */
        html:not([data-theme="dark"]) .logo-black {
            display: block;
        }

        /* Dark mode */
        html[data-theme="dark"] .logo-white {
            display: block;
        }

        h1 {
            margin: 0;
            padding: 0;
            line-height: 1.1;
        }
    </style>

    <div class="header">
        <img src="PF_Air_Logo black.png" class="logo logo-black" alt="Logo">
        <img src="PF_Air_Logo white.png.jpeg" class="logo logo-white" alt="Logo">
        <h1>PID Controller</h1>
    </div>
    """,
    unsafe_allow_html=True
)


# ==============================
# TITLE & DESCRIPTION
# ==============================
#st.title("PID Controller")

st.write(
    "A General-Purpose PID controller"
)

# ==============================
# IMPORT PID CORE
# ==============================
from pid_core import PID

# ==============================
# SIDEBAR — UNIVERSAL CONTROLLER
# ==============================
st.sidebar.header("PID Gains")

kp = st.sidebar.slider("Kp (Proportional)", 0.0, 500.0, 20.0, 1.0)
ki = st.sidebar.slider("Ki (Integral)", 0.0, 50.0, 0.0, 0.1)
kd = st.sidebar.slider("Kd (Derivative)", 0.0, 100.0, 2.0, 0.5)

st.sidebar.divider()

st.sidebar.header("Target & Safety")

setpoint = st.sidebar.slider(
    "Setpoint",
    min_value=-180,
    max_value=180,
    value=0.0,
    step=0.5
)

motor_output_limit = st.sidebar.slider(
    "Motor Output Limit (±)",
    0.0,
    100.0,
    50.0,
    1.0
)

emergency_stop = st.sidebar.toggle("🛑 Stop")

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
pid.kp = kp
pid.ki = ki
pid.kd = kd

# ==============================
# REAL-TIME LOOP
# ==============================
dt = 0.02
t_now = time.time() - st.session_state.start_time

# --------------------------------------------------
# 🔌 USER DATA SOURCE (REPLACE FOR REAL SYSTEMS)
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
    control = np.clip(control, -motor_output_limit, motor_output_limit)

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
