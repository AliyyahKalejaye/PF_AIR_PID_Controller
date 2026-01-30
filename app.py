import time
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from pid_core import PID
from bluetooth_link import BluetoothLink

st.set_page_config(
    page_title="PROFORCE AIRSYSTEMS PID CONTROLLER",
    layout="wide"
)

st.image("lPF_Air_Logo black.png", width=180)
st.title("PROFORCE AIRSYSTEMS PID CONTROLLER")

st.write(
    "This interface allows real-time tuning of a Proportional, Integral, and Derivative controller."
)

# =============================
# HARDWARE CONFIGURATION
# =============================
HARDWARE_CONFIG = {
    "Self Balancing Arm": {
        "unit": "Degrees",
        "setpoint": (-90.0, 90.0)
    },
    "Direct Current Motor": {
        "unit": "Revolutions Per Minute",
        "setpoint": (0.0, 6000.0)
    },
    "Brushless Direct Current Motor with Electronic Speed Controller": {
        "unit": "Normalized Output",
        "setpoint": (0.0, 1.0)
    },
    "Single Axis Drone Control": {
        "unit": "Degrees",
        "setpoint": (-45.0, 45.0)
    },
    "Custom System": {
        "unit": "User Defined",
        "setpoint": (-100.0, 100.0)
    }
}

# =============================
# SIDEBAR
# =============================
st.sidebar.header("Hardware Selection")

hardware = st.sidebar.selectbox(
    "Select Control System",
    list(HARDWARE_CONFIG.keys())
)

unit = HARDWARE_CONFIG[hardware]["unit"]
set_min, set_max = HARDWARE_CONFIG[hardware]["setpoint"]

st.sidebar.write(f"Control Unit: **{unit}**")

setpoint = st.sidebar.slider(
    "Desired Target Value",
    set_min,
    set_max,
    (set_min + set_max) / 2
)

st.sidebar.divider()
st.sidebar.header("Controller Gains")

kp = st.sidebar.slider("Proportional Gain", 0.0, 500.0, 20.0)
ki = st.sidebar.slider("Integral Gain", 0.0, 50.0, 0.0)
kd = st.sidebar.slider("Derivative Gain", 0.0, 100.0, 2.0)

reset = st.sidebar.button("Reset Controller")

# =============================
# BLUETOOTH
# =============================
st.sidebar.divider()
st.sidebar.header("Bluetooth Connection")

bluetooth_address = st.sidebar.text_input(
    "Microcontroller Bluetooth Address"
)

connect = st.sidebar.button("Connect")

if "bluetooth" not in st.session_state and connect:
    st.session_state.bluetooth = BluetoothLink(bluetooth_address)
    st.session_state.bluetooth.connect()

# =============================
# CONTROLLER STATE
# =============================
if "pid" not in st.session_state or reset:
    st.session_state.pid = PID(kp, ki, kd)
    st.session_state.history = {
        "time": [],
        "measurement": [],
        "control": []
    }
    st.session_state.start = time.time()

pid = st.session_state.pid
pid.kp, pid.ki, pid.kd = kp, ki, kd

# =============================
# REAL TIME LOOP
# =============================
dt = 0.02

if "bluetooth" in st.session_state:
    measured = st.session_state.bluetooth.read_sensor()
    control = pid.update(setpoint, measured, dt)
    st.session_state.bluetooth.send_control(control)

    t = time.time() - st.session_state.start
    st.session_state.history["time"].append(t)
    st.session_state.history["measurement"].append(measured)
    st.session_state.history["control"].append(control)

# =============================
# GRAPHS
# =============================
col1, col2 = st.columns(2)

with col1:
    st.subheader("Measured System Response")
    fig, ax = plt.subplots()
    ax.plot(st.session_state.history["time"],
            st.session_state.history["measurement"])
    ax.axhline(setpoint, linestyle="--")
    ax.set_xlabel("Time (seconds)")
    ax.set_ylabel(unit)
    ax.grid(True)
    st.pyplot(fig)

with col2:
    st.subheader("Control Output")
    fig, ax = plt.subplots()
    ax.plot(st.session_state.history["time"],
            st.session_state.history["control"])
    ax.set_xlabel("Time (seconds)")
    ax.grid(True)
    st.pyplot(fig)

time.sleep(dt)
st.rerun()

