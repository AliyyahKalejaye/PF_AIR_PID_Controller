import time
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

from pid_core import PID

# ==================================================
# PAGE CONFIGURATION
# ==================================================
st.set_page_config(
    page_title="PROFORCE AIRSYSTEMS PID CONTROLLER",
    layout="wide"
)

# ==================================================
# LOGO + TITLE (ROBUST)
# ==================================================
st.image("PF_Air_Logo black.png", width=140)  # black/white logo with transparent background
st.title("PROFORCE AIRSYSTEMS PID CONTROLLER")
st.write("A general-purpose proportional, integral, and derivative controller for real hardware systems.")

# ==================================================
# PAGE NAVIGATION
# ==================================================
page = st.sidebar.radio(
    "Navigation",
    ["Controller", "Documentation"]
)

# ==================================================
# HARDWARE PROFILES
# ==================================================
HARDWARE_PROFILES = {
    "Self-Balancing Arm": {
        "units": ["Degrees", "Radians"],
        "kp": (0.0, 500.0),
        "ki": (0.0, 50.0),
        "kd": (0.0, 100.0),
        "setpoint_deg": (-160.0, 160.0)
    },
    "Motor Speed Control": {
        "units": ["Normalized"],
        "kp": (0.0, 50.0),
        "ki": (0.0, 20.0),
        "kd": (0.0, 10.0),
        "setpoint_norm": (-1.0, 1.0)
    },
    "Position Control System": {
        "units": ["Degrees"],
        "kp": (0.0, 300.0),
        "ki": (0.0, 40.0),
        "kd": (0.0, 80.0),
        "setpoint_deg": (-180.0, 180.0)
    },
    "Custom Hardware": {
        "units": ["Degrees", "Radians", "Normalized"],
        "kp": (0.0, 1000.0),
        "ki": (0.0, 200.0),
        "kd": (0.0, 300.0),
        "setpoint_deg": (-180.0, 180.0),
        "setpoint_norm": (-1.0, 1.0)
    }
}

# ==================================================
# CONTROLLER PAGE
# ==================================================
if page == "Controller":

    # ------------------------------
    # SYSTEM CONFIGURATION
    # ------------------------------
    st.sidebar.header("System Configuration")

    hardware_type = st.sidebar.selectbox(
        "Hardware Type",
        list(HARDWARE_PROFILES.keys())
    )

    unit_type = st.sidebar.selectbox(
        "Measurement Unit",
        HARDWARE_PROFILES[hardware_type]["units"]
    )

    # ------------------------------
    # SETPOINT RANGE LOGIC
    # ------------------------------
    if unit_type == "Degrees":
        set_min, set_max = HARDWARE_PROFILES[hardware_type]["setpoint_deg"]
        unit_label = "degrees"
    elif unit_type == "Radians":
        set_min, set_max = -3.14, 3.14
        unit_label = "radians"
    else:
        set_min, set_max = HARDWARE_PROFILES[hardware_type]["setpoint_norm"]
        unit_label = "normalized units"

    # ------------------------------
    # CONTROLLER GAINS (DYNAMIC)
    # ------------------------------
    st.sidebar.header("Controller Gains")

    kp_min, kp_max = HARDWARE_PROFILES[hardware_type]["kp"]
    ki_min, ki_max = HARDWARE_PROFILES[hardware_type]["ki"]
    kd_min, kd_max = HARDWARE_PROFILES[hardware_type]["kd"]

    kp = st.sidebar.slider("Proportional Gain", kp_min, kp_max, kp_min, 1.0)
    ki = st.sidebar.slider("Integral Gain", ki_min, ki_max, ki_min, 0.1)
    kd = st.sidebar.slider("Derivative Gain", kd_min, kd_max, kd_min, 0.5)

    # ------------------------------
    # TARGET AND SAFETY
    # ------------------------------
    st.sidebar.header("Target and Safety")

    setpoint = st.sidebar.slider(
        f"Target Value ({unit_label})",
        min_value=set_min,
        max_value=set_max,
        value=0.0,
        step=(set_max - set_min) / 500,
        key="setpoint"
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

    # ------------------------------
    # SESSION STATE
    # ------------------------------
    if "pid" not in st.session_state:
        st.session_state.pid = PID(kp, ki, kd)

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

    # ------------------------------
    # CONTROL UPDATE
    # ------------------------------
    dt = 0.02

    if emergency_stop:
        control_output = 0.0
        measurement = (
            st.session_state.history["measurement"][-1]
            if st.session_state.history["measurement"]
            else 0.0
        )
    else:
        measurement = (
            st.session_state.history["measurement"][-1]
            if st.session_state.history["measurement"]
            else 0.0
        )

        control_output = pid.update(setpoint, measurement, dt)
        control_output = np.clip(
            control_output,
            -motor_output_limit,
            motor_output_limit
        )

        current_time = time.time() - st.session_state.start_time
        error = setpoint - measurement

        st.session_state.history["time"].append(current_time)
        st.session_state.history["measurement"].append(measurement)
        st.session_state.history["control"].append(control_output)
        st.session_state.history["error"].append(error)

    # ------------------------------
    # VISUALIZATION
    # ------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("System Output")

        fig1, ax1 = plt.subplots()
        ax1.plot(
            st.session_state.history["time"],
            st.session_state.history["measurement"],
            label="Measured Value"
        )
        ax1.axhline(setpoint, linestyle="--", label="Target Value")
        ax1.set_xlabel("Time (seconds)")
        ax1.set_ylabel(unit_label)
        ax1.legend()
        ax1.grid(True)
        st.pyplot(fig1)

    with col2:
        st.subheader("Control Output")

        fig2, ax2 = plt.subplots()
        ax2.plot(
            st.session_state.history["time"],
            st.session_state.history["control"],
            label="Control Output"
        )
        ax2.set_xlabel("Time (seconds)")
        ax2.set_ylabel("Output Level")
        ax2.grid(True)
        st.pyplot(fig2)

# ==================================================
# DOCUMENTATION PAGE
# ==================================================
else:
    st.header("Controller Documentation")

    st.markdown("""
### What this controller is

This application implements a proportional, integral, and derivative controller.  
It continuously compares a measured value from a physical system to a desired target value and computes a corrective output.

### The control equation

**Technical form**

Control Output =  
(Proportional Gain × Error)  
+ (Integral Gain × Accumulated Error)  
+ (Derivative Gain × Rate of Change of Error)

**Simpler explanation**

- The proportional term reacts to how far the system is from the target right now.
- The integral term corrects long-term bias that does not go away on its own.
- The derivative term anticipates future motion and reduces overshoot.

### Hardware and units

Different hardware behaves differently.  
This is why the controller automatically adjusts gain ranges and setpoint limits based on the selected hardware and measurement unit.

- Rotational systems use degrees or radians.
- Speed and power systems use normalized units.
- Custom hardware allows full manual control.

### Reading the graphs

- **System Output** shows what the hardware is actually doing.
- **Control Output** shows how much effort the controller is applying.
- A well-tuned system reaches the target smoothly and remains stable.

### Safety

Always begin with:
- Low motor output limits
- Emergency stop enabled
- Gradual increase of gains

### Conclusion

This controller is designed to be reusable across many real-world systems.  
By adjusting hardware type, units, and limits, it can be safely adapted to new projects without rewriting control logic.
""")
