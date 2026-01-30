
import time
import asyncio
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from pid_core import PID
from doc import show_documentation  # Import your doc.py page

# ==============================
# PAGE CONFIGURATION
# ==============================
st.set_page_config(
    page_title="PROFORCE AIRSYSTEMS PID CONTROLLER",
    layout="wide"
)

st.image("PF_Air_Logo black.png", width=180)
st.title("PROFORCE AIRSYSTEMS PID CONTROLLER")
st.write("A general-purpose feedback controller for real hardware systems.")

# ==============================
# PAGE NAVIGATION
# ==============================
page = st.sidebar.radio(
    "Navigation",
    ["Controller", "Documentation"]
)

# ==================================================
# CONTROLLER PAGE
# ==================================================
if page == "Controller":

    # ==============================
    # HARDWARE CONFIGURATION
    # ==============================
    HARDWARE_CONFIG = {
        "Self Balancing Arm": {"unit": "Degrees", "setpoint": (-90.0, 90.0)},
        "Direct Current Motor": {"unit": "Revolutions Per Minute", "setpoint": (0.0, 6000.0)},
        "Brushless Motor with ESC": {"unit": "Normalized Output", "setpoint": (0.0, 1.0)},
        "Single Axis Drone Control": {"unit": "Degrees", "setpoint": (-45.0, 45.0)},
        "Custom System": {"unit": "User Defined", "setpoint": (-100.0, 100.0)}
    }

    st.sidebar.header("System Configuration")

    hardware_type = st.sidebar.selectbox(
        "Select Hardware Type",
        list(HARDWARE_CONFIG.keys())
    )

    unit_type = st.sidebar.selectbox(
        "Measurement Unit",
        ["Degrees", "Radians"]
    )

    # Adjust setpoint range dynamically
    if unit_type == "Degrees":
        setpoint_min, setpoint_max = -180.0, 180.0
    elif unit_type == "Radians":
        setpoint_min, setpoint_max = -3.14, 3.14
    else:
        setpoint_min, setpoint_max = HARDWARE_CONFIG[hardware_type]["setpoint"]

    # ==============================
    # CONTROLLER GAINS
    # ==============================
    st.sidebar.header("Controller Gains")
    # You can expand this to dynamic ranges per hardware/unit
    kp = st.sidebar.slider("Proportional Gain", 0.0, 500.0, 20.0, 1.0)
    ki = st.sidebar.slider("Integral Gain", 0.0, 100.0, 0.0, 0.1)
    kd = st.sidebar.slider("Derivative Gain", 0.0, 200.0, 2.0, 0.5)

    # ==============================
    # TARGET AND SAFETY
    # ==============================
    st.sidebar.header("Target and Safety")
    setpoint = st.sidebar.slider(
        f"Target Value ({unit_type})",
        min_value=setpoint_min,
        max_value=setpoint_max,
        value=0.0,
        step=0.5,
        key="setpoint_value"
    )

    motor_output_limit = st.sidebar.slider(
        "Motor Output Limit",
        0.0,
        100.0,
        50.0,
        1.0
    )

    emergency_stop = st.sidebar.toggle("Emergency Stop")
    reset_controller = st.sidebar.button("Reset Controller")

    # ==============================
    # BLUETOOTH SETUP
    # ==============================
    st.sidebar.header("Bluetooth Connection")
    bluetooth_address = st.sidebar.text_input("Device Address", value="AA:BB:CC:DD:EE:FF")
    characteristic_uuid = st.sidebar.text_input("Characteristic UUID", value="0000ffe1-0000-1000-8000-00805f9b34fb")
    connect_bluetooth = st.sidebar.button("Connect to Hardware")

    # ==============================
    # SESSION STATE
    # ==============================
    if "pid" not in st.session_state:
        st.session_state.pid = PID(kp, ki, kd)

    if "bluetooth" not in st.session_state:
        st.session_state.bluetooth = None

    if "running" not in st.session_state:
        st.session_state.running = True

    if "history" not in st.session_state or reset_controller:
        st.session_state.history = {
            "time": [],
            "measurement": [],
            "control": [],
            "error": []
        }
        st.session_state.start_time = time.time()
        st.session_state.pid.reset()

    pid = st.session_state.pid
    pid.kp = kp
    pid.ki = ki
    pid.kd = kd

    # ==============================
    # ASYNC HELPER
    # ==============================
    def run_async(coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    # ==============================
    # BLUETOOTH CONNECTION
    # ==============================
    if connect_bluetooth and st.session_state.bluetooth is None:
        link = BluetoothLink(bluetooth_address, characteristic_uuid)
        run_async(link.connect())
        st.session_state.bluetooth = link
        st.success("Bluetooth connected successfully.")

    # ==============================
    # REAL-TIME CONTROL LOOP
    # ==============================
    dt = 0.02
    current_time = time.time() - st.session_state.start_time

    if emergency_stop:
        st.session_state.running = False
        pid.reset()
        control_output = 0.0
        measurement = st.session_state.history["measurement"][-1] if st.session_state.history["measurement"] else 0.0
        error = setpoint - measurement
    else:
        st.session_state.running = True

        if st.session_state.bluetooth:
            measurement = run_async(st.session_state.bluetooth.read_measurement())
        else:
            measurement = 0.0  # simulation fallback

        control_output = pid.update(setpoint, measurement, dt)
        control_output = np.clip(control_output, -motor_output_limit, motor_output_limit)

        if st.session_state.bluetooth:
            run_async(st.session_state.bluetooth.send_control_output(control_output))

        error = setpoint - measurement

        # store data
        st.session_state.history["time"].append(current_time)
        st.session_state.history["measurement"].append(measurement)
        st.session_state.history["control"].append(control_output)
        st.session_state.history["error"].append(error)

    # ==============================
    # VISUALIZATION
    # ==============================
    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("System Output")
        fig1, ax1 = plt.subplots()
        ax1.plot(st.session_state.history["time"], st.session_state.history["measurement"], label="Measured Value")
        ax1.axhline(setpoint, linestyle="--", label="Target")
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel(unit_type)
        ax1.legend()
        ax1.grid(True)
        st.pyplot(fig1)

    with col2:
        st.subheader("Control Output")
        fig2, ax2 = plt.subplots()
        ax2.plot(st.session_state.history["time"], st.session_state.history["control"], label="Controller Output")
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Output Level")
        ax2.grid(True)
        st.pyplot(fig2)

    with col3:
        st.subheader("Error")
        fig3, ax3 = plt.subplots()
        ax3.plot(st.session_state.history["time"], st.session_state.history["error"], label="Error")
        ax3.set_xlabel("Time (s)")
        ax3.set_ylabel("Error")
        ax3.grid(True)
        st.pyplot(fig3)

    # ==============================
    # AUTO REFRESH
    # ==============================
    if st.session_state.running:
        time.sleep(dt)
        st.rerun()

# ==================================================
# DOCUMENTATION PAGE
# ==================================================
else:
    show_documentation()  # call your doc.py function
