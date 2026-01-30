import streamlit as st

st.set_page_config(
    page_title="PID Controller Documentation",
    layout="wide"
)

st.title("PID Controller Documentation")

st.markdown("""
## Introduction

This documentation explains how the Proportional, Integral, and Derivative controller works, 
how it is used with real hardware, and how to interpret the graphs shown in the controller interface.

The goal is not only to explain the mathematics, but also to explain how to use the controller
in practical engineering systems.

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
(Proportional Gain × Error)  
+ (Integral Gain × Sum of Error Over Time)  
+ (Derivative Gain × Rate of Change of Error)

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
If the system stays slightly away from the target for a long time,
The integral term increases the output until the error disappears.

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

---

### Direct Current Motor

- Unit: Revolutions per Minute
- Typical Setpoint Range: 0 to maximum rated speed

The controller regulates motor speed using an encoder or a Hall effect sensor.

---

### Brushless Direct Current Motor with Electronic Speed Controller

- Unit: Normalized Output (0 to 1)

The controller outputs a normalized value that the electronic speed controller converts
into motor power.

---

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

Understanding both the mathematics and the physical behavior of the system
is essential for effective control tuning.

With careful tuning and correct sensor feedback,
this controller provides stable and precise control over real-world systems.
""")
