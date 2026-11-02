import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(page_title="Aircraft Performance Analysis", page_icon="✈️", layout="wide")

# ----------------------------- PAGE STYLE ------------------------------------
st.title("✈️ Aircraft Performance Analysis")
st.caption("Interactive Flight Dynamics calculator | Based on the supplied aircraft-performance code")

# ----------------------------- SIDEBAR INPUTS -------------------------------
st.sidebar.header("Aircraft Parameters")
S = st.sidebar.number_input("Wing area, S (m²)", min_value=1.0, value=47.0, step=1.0)
AR = st.sidebar.number_input("Aspect ratio, AR", min_value=1.0, value=6.5, step=0.1)
e = st.sidebar.number_input("Oswald efficiency factor, e", min_value=0.1, max_value=1.0, value=0.87, step=0.01)
CD0 = st.sidebar.number_input("Zero-lift drag coefficient, CD₀", min_value=0.001, value=0.032, step=0.001, format="%.3f")
W = st.sidebar.number_input("Aircraft weight, W (N)", min_value=100.0, value=103047.0, step=1000.0)
num_engines = st.sidebar.number_input("Number of engines", min_value=1, value=2, step=1)
thrust_per_engine = st.sidebar.number_input("Thrust per engine (N)", min_value=100.0, value=40298.0, step=100.0)
rho_sl = st.sidebar.number_input("Sea-level density (kg/m³)", min_value=0.1, value=1.225, step=0.001, format="%.3f")

st.sidebar.header("Atmospheric Conditions")
rho_options = st.sidebar.multiselect(
    "Select air densities to compare (kg/m³)",
    options=[1.225, 1.112, 0.819, 0.736, 0.660],
    default=[1.112, 0.819],
    format_func=lambda x: f"{x:.3f}"
)
custom_rhos = st.sidebar.text_input("Or enter densities separated by commas", "")
if custom_rhos.strip():
    try:
        entered = [float(x.strip()) for x in custom_rhos.split(",") if x.strip()]
        densities = entered
    except ValueError:
        st.sidebar.error("Enter valid numbers separated by commas.")
        densities = rho_options
else:
    densities = rho_options

st.sidebar.header("Velocity Range")
v_min = st.sidebar.number_input("Minimum velocity (m/s)", min_value=1.0, value=30.0, step=5.0)
v_max = st.sidebar.number_input("Maximum velocity (m/s)", min_value=2.0, value=350.0, step=5.0)
if v_max <= v_min:
    st.sidebar.error("Maximum velocity must be greater than minimum velocity.")
    st.stop()
if not densities:
    st.warning("Select or enter at least one air density in the sidebar.")
    st.stop()
if any(r <= 0 for r in densities):
    st.error("Air density values must be greater than zero.")
    st.stop()

K = 1.0 / (np.pi * e * AR)
T_A_sea_level = num_engines * thrust_per_engine
velocity = np.linspace(v_min, v_max, 500)

# ----------------------------- COMMON HELPERS -------------------------------
def thrust_required(rho, v):
    return 0.5 * rho * v**2 * S * CD0 + (2 * K * W**2) / (rho * v**2 * S)

def altitude_from_density(rho):
    """Approximate tropospheric altitude from density using the source's ISA relation."""
    rho0, T0, lapse, g0, R_air = 1.225, 288.15, 0.0065, 9.80665, 287.05
    exponent = (g0 / (R_air * lapse)) - 1.0
    temp_ratio = (rho / rho0) ** (1.0 / exponent)
    return (T0 / lapse) * (1.0 - temp_ratio) / 1000.0

def make_fig():
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.grid(True, linestyle="--", alpha=0.5)
    return fig, ax

# ----------------------------- NAVIGATION ------------------------------------
pages = [
    "Overview", "Thrust Required", "Power Required", "Rate of Climb",
    "V–n Diagram", "Gliding Flight", "Takeoff Performance"
]
page = st.sidebar.radio("Select Performance Module", pages)

if page == "Overview":
    st.subheader("Application overview")
    st.markdown("""
    Use the sidebar to change aircraft parameters, atmospheric density and velocity range.
    Select a module to view its graph and calculated results.

    **Modules converted from the supplied code:**
    - Thrust required and thrust available
    - Power required and power available
    - Rate of climb
    - V–n diagram
    - Gliding flight
    - Takeoff performance

    **Not included in the supplied source code:** Hodograph and Range & Endurance.
    These require additional equations/model assumptions and have therefore not been invented here.
    """)
    c1, c2, c3 = st.columns(3)
    c1.metric("Wing area", f"{S:.2f} m²")
    c2.metric("Aircraft weight", f"{W:,.0f} N")
    c3.metric("Total sea-level thrust", f"{T_A_sea_level/1000:.2f} kN")
    st.info("Educational calculation tool. Verify assumptions and results before using them for design or operational decisions.")

elif page == "Thrust Required":
    st.subheader("Thrust Required and Thrust Available vs Velocity")
    fig, ax = make_fig()
    rows = []
    tr_min = 2 * W * np.sqrt(K * CD0)
    for rho in densities:
        ta = T_A_sea_level * (rho / rho_sl)
        tr = thrust_required(rho, velocity)
        v_tr_min = np.sqrt((2 * W) / (rho * S) * np.sqrt(K / CD0))
        ax.plot(velocity, tr / 1000, linewidth=2, label=f"TR, ρ={rho:.3f}")
        ax.scatter([v_tr_min], [tr_min / 1000], marker="o", s=55,
                   label=f"Min TR: {v_tr_min:.1f} m/s")
        ax.plot(velocity, np.full_like(velocity, ta / 1000), "--", linewidth=2,
                label=f"TA, ρ={rho:.3f} ({ta/1000:.2f} kN)")
        rows.append({"Density (kg/m³)": rho, "Minimum TR (kN)": tr_min/1000,
                     "Velocity at minimum TR (m/s)": v_tr_min,
                     "Thrust available (kN)": ta/1000})
    ax.set_xlabel("Velocity (m/s)")
    ax.set_ylabel("Thrust (kN)")
    ax.set_title("Thrust Required and Thrust Available")
    ax.legend()
    st.pyplot(fig)
    st.dataframe(pd.DataFrame(rows).round(2), use_container_width=True)

elif page == "Power Required":
    st.subheader("Power Required and Power Available vs Velocity")
    fig, ax = make_fig()
    rows = []
    for rho in densities:
        ta = T_A_sea_level * (rho / rho_sl)
        tr = thrust_required(rho, velocity)
        pr = tr * velocity
        pa = ta * velocity
        v_pr_min = ((2 * K * W**2) / (1.5 * rho**2 * S**2 * CD0))**0.25
        pr_min = thrust_required(rho, v_pr_min) * v_pr_min
        ax.plot(velocity, pr/1000, linewidth=2, label=f"PR, ρ={rho:.3f}")
        ax.plot(velocity, pa/1000, "--", linewidth=2, label=f"PA, ρ={rho:.3f}")
        ax.scatter([v_pr_min], [pr_min/1000], marker="x", s=70,
                   label=f"Min PR: {v_pr_min:.1f} m/s")
        rows.append({"Density (kg/m³)": rho, "Minimum PR (kW)": pr_min/1000,
                     "Velocity at minimum PR (m/s)": v_pr_min})
    ax.set_xlabel("Velocity (m/s)")
    ax.set_ylabel("Power (kW)")
    ax.set_title("Power Required and Power Available")
    ax.legend()
    st.pyplot(fig)
    st.dataframe(pd.DataFrame(rows).round(2), use_container_width=True)

elif page == "Rate of Climb":
    st.subheader("Rate of Climb vs Velocity")
    fig, ax = make_fig()
    rows = []
    for rho in densities:
        ta = T_A_sea_level * (rho / rho_sl)
        tr = thrust_required(rho, velocity)
        roc = ((ta * velocity) - (tr * velocity)) / W
        idx = int(np.argmax(roc))
        max_roc, v_max_roc = roc[idx], velocity[idx]
        ax.plot(velocity, roc, linewidth=2, label=f"RoC, ρ={rho:.3f}")
        ax.scatter([v_max_roc], [max_roc], marker="s", s=55,
                   label=f"Maximum: {max_roc:.2f} m/s at {v_max_roc:.1f} m/s")
        rows.append({"Density (kg/m³)": rho, "Maximum RoC (m/s)": max_roc,
                     "Velocity at maximum RoC (m/s)": v_max_roc})
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Velocity (m/s)")
    ax.set_ylabel("Rate of climb (m/s)")
    ax.set_title("Rate of Climb")
    ax.legend()
    st.pyplot(fig)
    st.dataframe(pd.DataFrame(rows).round(2), use_container_width=True)
    st.caption("This follows the supplied source model: RoC = (Power Available − Power Required) / Weight.")

elif page == "V–n Diagram":
    st.subheader("V–n Diagram Comparison")
    st.write("Change the aerodynamic and structural limits below.")
    c1, c2, c3, c4 = st.columns(4)
    cl_pos = c1.number_input("Maximum positive CL", min_value=0.1, value=1.5, step=0.1)
    cl_neg = c2.number_input("Maximum negative CL (magnitude)", min_value=0.1, value=0.8, step=0.1)
    n_pos = c3.number_input("Positive limit load factor (g)", min_value=0.1, value=5.0, step=0.5)
    n_neg = c4.number_input("Negative limit load factor (g)", min_value=0.1, value=3.0, step=0.5)
    fig, ax = make_fig()
    ax.axhline(n_pos, color="red", linestyle="-", label=f"Positive structural limit +{n_pos:g}g")
    ax.axhline(-n_neg, color="red", linestyle="--", label=f"Negative structural limit -{n_neg:g}g")
    ax.axhline(1, color="gray", linestyle=":", label="1g level flight")
    rows = []
    vmax_plot = 0
    for rho in densities:
        vs_pos = np.sqrt((2*W)/(rho*S*cl_pos))
        vs_neg = np.sqrt((2*W)/(rho*S*cl_neg))
        va = vs_pos * np.sqrt(n_pos)
        vne = 1.2 * (1.5 * va)
        vmax_plot = max(vmax_plot, vne)
        vp = np.linspace(0, va, 200)
        vn = np.linspace(0, vs_neg*np.sqrt(n_neg), 200)
        ax.plot(vp, 0.5*rho*vp**2*S*cl_pos/W, linewidth=2, label=f"Positive stall, ρ={rho:.3f}")
        ax.plot(vn, -(0.5*rho*vn**2*S*cl_neg/W), "--", linewidth=2, label=f"Negative stall, ρ={rho:.3f}")
        ax.plot([va, vne], [n_pos, n_pos], ":", linewidth=1.5)
        ax.plot([vne, vne], [-n_neg, n_pos], "-.", linewidth=1.5, label=f"Vne={vne:.1f} m/s, ρ={rho:.3f}")
        rows.append({"Density (kg/m³)": rho, "Positive stall speed (m/s)": vs_pos,
                     "Negative stall speed (m/s)": vs_neg, "Corner speed Va (m/s)": va,
                     "Vne (m/s)": vne})
    ax.set_xlim(0, vmax_plot*1.08)
    ax.set_ylim(-n_neg-0.5, n_pos+0.5)
    ax.set_xlabel("Velocity (m/s)")
    ax.set_ylabel("Load factor, n (g)")
    ax.set_title("V–n Diagram")
    ax.legend(loc="best", fontsize=8)
    st.pyplot(fig)
    st.dataframe(pd.DataFrame(rows).round(2), use_container_width=True)
    st.caption("The Vc/Vne construction shown follows the supplied code's assumed multipliers; it is not a certified aircraft flight envelope.")

elif page == "Gliding Flight":
    st.subheader("Gliding Flight")
    cd0_glide = st.number_input("Zero-lift drag coefficient, CD₀", min_value=0.001, value=float(CD0), step=0.001, format="%.3f", key="glide_cd0")
    k_glide = st.number_input("Induced drag factor, K", min_value=0.0001, value=float(K), step=0.001, format="%.4f")
    st.caption("The source code calculates approximate altitude from air density using a tropospheric standard-atmosphere relation.")
    rows = []
    for rho in densities:
        h_km = altitude_from_density(rho)
        ld_max = 1/(2*math.sqrt(cd0_glide*k_glide))
        glide_angle = math.degrees(math.atan(1/ld_max))
        max_range = h_km*ld_max
        rows.append({"Density (kg/m³)": rho, "Approx. altitude (km)": h_km,
                     "Maximum L/D": ld_max, "Minimum glide angle (deg)": glide_angle,
                     "Maximum glide range (km)": max_range})
    st.dataframe(pd.DataFrame(rows).round(3), use_container_width=True)
    st.metric("Maximum lift-to-drag ratio (L/D)", f"{1/(2*math.sqrt(cd0_glide*k_glide)):.2f}")

elif page == "Takeoff Performance":
    st.subheader("Takeoff Performance Comparison")
    st.warning("The supplied code uses baseline distances and density-scaling assumptions. These are retained here; this is not a first-principles takeoff-performance model.")
    c1, c2 = st.columns(2)
    cl_to = c1.number_input("Maximum lift coefficient for takeoff", min_value=0.1, value=2.8, step=0.1)
    baseline_rho = c2.number_input("Baseline density (kg/m³)", min_value=0.1, value=0.819, step=0.001, format="%.3f")
    sg_base = st.number_input("Baseline ground roll (m)", min_value=1.0, value=789.32, step=10.0)
    r_base = st.number_input("Baseline transition radius (m)", min_value=1.0, value=1356.64, step=10.0)
    sa_base = st.number_input("Baseline airborne distance (m)", min_value=1.0, value=364.92, step=10.0)
    rows = []
    for rho in densities:
        v_stall = math.sqrt((2*W)/(rho*S*cl_to))
        sg = sg_base*(baseline_rho/rho)
        radius = r_base*(baseline_rho/rho)
        sa = sa_base*(baseline_rho/rho)
        rows.append({"Density (kg/m³)": rho, "Stall velocity (m/s)": v_stall,
                     "Ground roll (m)": sg, "Transition radius (m)": radius,
                     "Airborne distance (m)": sa, "Total takeoff distance (m)": sg+sa})
    df = pd.DataFrame(rows)
    st.dataframe(df.round(2), use_container_width=True)
    fig, ax = make_fig()
    x = np.arange(len(df))
    ax.bar(x-0.18, df["Ground roll (m)"], width=0.36, label="Ground roll")
    ax.bar(x+0.18, df["Airborne distance (m)"], width=0.36, label="Airborne distance")
    ax.set_xticks(x, [f"ρ={r:.3f}" for r in df["Density (kg/m³)"]])
    ax.set_ylabel("Distance (m)")
    ax.set_title("Takeoff Distance Components")
    ax.legend()
    st.pyplot(fig)

st.divider()
st.caption("Model note: Results depend on the equations and assumptions in the supplied source. Check units, assumptions and aircraft-specific data before relying on the outputs.")
