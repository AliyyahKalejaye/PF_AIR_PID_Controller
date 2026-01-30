import time
import asyncio
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from pid_core import PID
from bluetooth_link import BluetoothLink  # Your async BLE helper


# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(
    page_title="PROFORCE AIRSYSTEMS PID CONTROLLER",
    layout="wide"
)

st.image("PF_Air_Logo black.png", width=180)
st.title("PROFORCE AIRSYSTEMS PID CONTROLLER")

# ==============================
# PAGE NAVIGATION
# ==============================
page = st.sidebar.radio(
    "Navigation",
    ["Controller", "Documentation"]
)

# ==============================
# CONTROLLER PAGE
# ==============================
if page == "Controller":
    st.write("A general-purpose feedback controller for real hardware systems.")

    # ------------------------------
    # HARDWARE CONFIGURATION
    # ------------------------------
    HARDWARE_CONFIG = {
        "Self Balancing Arm": {"units": ["Degrees", "Radians"], "setpoint_deg": (-160, 160)},
        "Direct Current Motor": {"units": ["Revolutions per Minute"], "setpoint_rpm": (0, 6000)},
        "Brushless Motor with ESC": {"units": ["Normalized Output"], "setpoint_norm": (0.0, 1.0)},
        "Single Axis Drone Control": {"units": ["Degrees"], "setpoint_deg": (-45, 45)},
        "Custom System": {"units": ["Degrees", "Radians", "Normalized Output"], 
                          "setpoint_deg": (-180, 180), 
                          "setpoint_norm": (-1.0, 1.0)}
    }

    # ------------------------------
    # SYSTEM & UNIT SELECTION
    # ------------------------------
    st.sidebar.header("System Configuration")
    hardware_type = st.sidebar.selectbox("Select Hardware Type", list(HARDWARE_CONFIG.keys()))
    unit_type = st.sidebar.selectbox("Measurement Unit", HARDWARE_CONFIG[hardware_type]["units"])

    # Determine setpoint range dynamically
    if unit_type.lower() == "degrees":
        set_min, set_max = HARDWARE_CONFIG[hardware_type].get("setpoint_deg", (-180, 180))
    elif unit_type.lower() == "radians":
        set_min, set_max = -3.14, 3.14
    elif unit_type.lower() == "normalized output":
        set_min, set_max = HARDWARE_CONFIG[hardware_type].get("setpoint_norm", (0.0, 1.0))
    elif unit_type.lower() == "revolutions per minute":
        set_min, set_max = HARDWARE_CONFIG[hardware_type].get("setpoint_rpm", (0, 6000))
    else:
        set_min, set_max = -100.0, 100.0

    # ------------------------------
    # PID GAINS
    # ------------------------------
    st.sidebar.header("Controller Gains")
    kp = st.sidebar.slider("Proportional Gain", 0.0, 500.0, 20.0, 1.0)
    ki = st.sidebar.slider("Integral Gain", 0.0, 100.0, 0.0, 0.1)
    kd = st.sidebar.slider("Derivative Gain", 0.0, 200.0, 2.0, 0.5)

    # ------------------------------
    # TARGET & SAFETY
    # ------------------------------
    st.sidebar.header("Target and Safety")
    setpoint = st.sidebar.slider(
        f"Target Value ({unit_type})",
        float(set_min),
        float(set_max),
        0.0,
        step=float((set_max - set_min)/500)
    )
    motor_output_limit = st.sidebar.slider("Motor Output Limit", 0.0, 100.0, 50.0, 1.0)
    emergency_stop = st.sidebar.toggle("Emergency Stop")
    reset_controller = st.sidebar.button("Reset Controller")

    # ------------------------------
    # BLUETOOTH CONNECTION
    # ------------------------------
    st.sidebar.header("Bluetooth Connection")
    bluetooth_address = st.sidebar.text_input("Device Address", value="AA:BB:CC:DD:EE:FF")
    connect_bluetooth = st.sidebar.button("Connect to Hardware")

    # ------------------------------
    # SESSION STATE
    # ------------------------------
    if "pid" not in st.session_state:
        st.session_state.pid = PID(kp, ki, kd)
    if "bluetooth" not in st.session_state:
        st.session_state.bluetooth = None
    if "running" not in st.session_state:
        st.session_state.running = True
    if "history" not in st.session_state or reset_controller:
        st.session_state.history = {"time": [], "measurement": [], "control": [], "error": []}
        st.session_state.start_time = time.time()
        st.session_state.pid.reset()

    pid = st.session_state.pid
    pid.kp = kp
    pid.ki = ki
    pid.kd = kd

    # ------------------------------
    # ASYNC HELPER
    # ------------------------------
    def run_async(coro):
        return asyncio.get_event_loop().run_until_complete(coro)

    # ------------------------------
    # CONNECT TO BLUETOOTH
    # ------------------------------
    if connect_bluetooth and st.session_state.bluetooth is None:
        link = BluetoothLink(bluetooth_address)
        run_async(link.connect())
        characteristics = run_async(link.list_characteristics())
        char_option = st.sidebar.selectbox("Select Characteristic", characteristics)
        st.session_state.bluetooth = link
        st.session_state.char_uuid = char_option
        st.success("Bluetooth connected successfully.")

    # ------------------------------
    # REAL-TIME CONTROL LOOP
    # ------------------------------
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
        measurement = 0.0
        if st.session_state.bluetooth:
            measurement = run_async(st.session_state.bluetooth.read_measurement(st.session_state.char_uuid))
        control_output = pid.update(setpoint, measurement, dt)
        control_output = np.clip(control_output, -motor_output_limit, motor_output_limit)
        if st.session_state.bluetooth:
            run_async(st.session_state.bluetooth.send_control_output(st.session_state.char_uuid, control_output))
        error = setpoint - measurement

        st.session_state.history["time"].append(current_time)
        st.session_state.history["measurement"].append(measurement)
        st.session_state.history["control"].append(control_output)
        st.session_state.history["error"].append(error)

    # ------------------------------
    # VISUALIZATION (BIG GRAPHS)
    # ------------------------------
    col1, col2, col3 = st.columns(3)
    figsize = (9, 5)

    with col1:
        st.subheader("System Output")
        fig1, ax1 = plt.subplots(figsize=figsize)
        ax1.plot(st.session_state.history["time"], st.session_state.history["measurement"], label="Measured Value")
        ax1.axhline(setpoint, linestyle="--", label="Target")
        ax1.set_xlabel("Time (s)")
        ax1.set_ylabel(unit_type)
        ax1.legend()
        ax1.grid(True)
        st.pyplot(fig1)

    with col2:
        st.subheader("Control Output")
        fig2, ax2 = plt.subplots(figsize=figsize)
        ax2.plot(st.session_state.history["time"], st.session_state.history["control"], label="Controller Output")
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Output Level")
        ax2.grid(True)
        st.pyplot(fig2)

    with col3:
        st.subheader("Error")
        fig3, ax3 = plt.subplots(figsize=figsize)
        ax3.plot(st.session_state.history["time"], st.session_state.history["error"], label="Error")
        ax3.set_xlabel("Time (s)")
        ax3.set_ylabel("Error")
        ax3.grid(True)
        st.pyplot(fig3)

    # ------------------------------
    # AUTO REFRESH
    # ------------------------------
    if st.session_state.running:
        time.sleep(dt)
        st.experimental_rerun()

# ==============================
# DOCUMENTATION PAGE
# ==============================
else:
    st.header("Documentation")
    st.markdown("""
## Introduction

This documentation explains how the Proportional, Integral, and Derivative controller works, how it is used with real hardware, and how to interpret the graphs shown in the controller interface.

The goal is not only to explain the mathematics, but also to explain how to use the controller in practical engineering systems.

---

## What a Proportional, Integral, and Derivative Controller Is

A Proportional, Integral, and Derivative controller is a feedback control system.
It continuously adjusts the output to make the system reach and hold a desired value.

It works by comparing:
- the value you want the system to reach (the setpoint)
- the value measured by a sensor

The difference between these two values is called the error.

---

## The Control Equation

### Full Mathematical Form

**u(t) = Kp·e(t) + Ki∫e(t)dt + Kd·de(t)/dt**

Output =  
(Proportional Gain × Error) + (Integral Gain × Sum of Error Over Time) + (Derivative Gain × Rate of Change of Error)

### Simplified Explanation

The controller:
- reacts to how far the system is from the target
- remembers how long it has been off target
- predicts where the system is heading next

All three actions are combined into one control signal.

---

## Explanation of Each Term

### Proportional Term

The proportional term reacts to the current error.
If the error is large, the output is large.
If the error is small, the output is small.

This makes the system respond quickly, but too much proportional gain can cause oscillation.

### Integral Term

The integral term looks at error over time.
If the system stays slightly away from the target for a long time, the integral term increases the output until the error disappears.

Too much integral gain can cause slow response or instability.

### Derivative Term

The derivative term looks at how fast the error is changing.
It slows the system down as it approaches the target.

This reduces overshoot and improves stability.

---

## Hardware Types, Units, and Setpoints

### Self-Balancing Arm

- Unit: Degrees
- Typical Setpoint Range: -90 to +90 degrees

The controller keeps the arm at a desired angle using feedback from an angle sensor.

### Direct Current Motor

- Unit: Revolutions per Minute
- Typical Setpoint Range: 0 to maximum rated speed

The controller regulates motor speed using an encoder or a Hall effect sensor.

### Brushless Direct Current Motor with Electronic Speed Controller

- Unit: Normalized Output (0 to 1)

The controller outputs a normalized value that the electronic speed controller converts
into motor power.

### Single Axis Drone Control

- Unit: Degrees
- Typical Setpoint Range: -45 to +45 degrees

The controller stabilizes pitch, roll, or yaw using inertial measurement sensors.

---

## Understanding the Graphs

The measured system response graph shows what the system is actually doing.

The horizontal line represents the desired target value.

The control output graph shows how hard the controller is driving the system.

A good controller setup:
- reaches the target smoothly
- has minimal overshoot
- settles quickly without oscillation

---

## Conclusion

This system is designed to be hardware independent, flexible, and safe.
The same controller logic can be used across motors, robotic arms, and aerial systems.

Understanding both the mathematics and the physical behavior of the system is essential for effective control tuning.

With careful tuning and correct sensor feedback, this controller provides stable and precise control over real-world systems.
""")
