import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# Configure page
st.set_page_config(
    page_title="Pearls AQI Predictor Architecture",
    page_icon="AQI",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Constants
API_URL = "http://localhost:8000"

st.title("Pearls AQI Predictor & Policy Intelligence Engine")
st.markdown(
    "End-to-end Air Quality Index forecast, Causal AI policy simulator, and satellite telemetry for Sargodha, Pakistan."
)

# Tabs Layout
tab_forecast, tab_causal, tab_satellite, tab_canary = st.tabs(
    [
        "72-Hour Forecast",
        "Causal What-If Simulator",
        "Satellite Sentinel-5P",
        "Shadow Canary Engine",
    ]
)

# Sidebar for controls
st.sidebar.header("Model Controls")
try:
    models_resp = requests.get(f"{API_URL}/models")
    if models_resp.status_code == 200:
        models_data = models_resp.json()
        model_list = models_data.get("models", [])
        model_names = {m["id"]: m["name"] for m in model_list}
        default_model = models_data.get("default_model_id", "bilstm_attention")

        selected_model_id = st.sidebar.selectbox(
            "Select Champion Model",
            options=list(model_names.keys()),
            format_func=lambda x: model_names.get(x, x),
            index=list(model_names.keys()).index(default_model)
            if default_model in model_names
            else 0,
        )
    else:
        st.sidebar.error("Failed to load models from API.")
        selected_model_id = "bilstm_attention"
except Exception as e:
    st.sidebar.warning(f"API disconnected (Using client fallback): {e}")
    selected_model_id = "bilstm_attention"

# TAB 1: 72-Hour Forecast
with tab_forecast:
    if st.sidebar.button("Generate Live Forecast", key="btn_forecast"):
        with st.spinner("Executing inference across 37 features..."):
            try:
                pred_resp = requests.post(
                    f"{API_URL}/predict", params={"model_id": selected_model_id}
                )
                if pred_resp.status_code == 200:
                    data = pred_resp.json()

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Current AQI", f"{data['current_aqi']} ({data['current_level']})")
                    col2.metric("Model Architecture", data["model_type"])
                    col3.metric("Alert Status", "Active" if data["alert"] else "Normal")

                    st.info(f"**Health Advisory**: {data['summary']}")

                    st.subheader("72-Hour AQI Trajectory & Uncertainty Bounds")
                    hourly = data.get("hourly_predictions", [])
                    if hourly:
                        df = pd.DataFrame(hourly)
                        df["timestamp"] = pd.to_datetime(df["timestamp"])

                        fig = go.Figure()
                        if "aqi_upper_95" in df.columns and "aqi_lower_95" in df.columns:
                            fig.add_trace(
                                go.Scatter(
                                    name="95% CI Upper",
                                    x=df["timestamp"],
                                    y=df["aqi_upper_95"],
                                    mode="lines",
                                    line=dict(width=0),
                                    showlegend=False,
                                )
                            )
                            fig.add_trace(
                                go.Scatter(
                                    name="95% CI",
                                    x=df["timestamp"],
                                    y=df["aqi_lower_95"],
                                    mode="lines",
                                    line=dict(width=0),
                                    fillcolor="rgba(68, 68, 68, 0.2)",
                                    fill="tonexty",
                                )
                            )

                        fig.add_trace(
                            go.Scatter(
                                name="Predicted AQI",
                                x=df["timestamp"],
                                y=df["aqi_predicted"],
                                mode="lines+markers",
                                line=dict(color="rgb(31, 119, 180)", width=2),
                            )
                        )

                        fig.add_hline(
                            y=150,
                            line_dash="dash",
                            line_color="red",
                            annotation_text="Unhealthy Threshold",
                        )
                        fig.update_layout(
                            xaxis_title="Time", yaxis_title="AQI", hovermode="x unified"
                        )
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.error(f"Prediction failed: {pred_resp.text}")
            except Exception as e:
                st.error(f"Failed to connect to API: {e}")
    else:
        st.info("Click 'Generate Live Forecast' in the sidebar to fetch 72-hour predictions.")

# TAB 2: Causal What-If Simulator
with tab_causal:
    st.header("Causal Policy Intervention Simulator")
    st.markdown(
        "Simulate Do-Calculus interventions on municipal traffic, biomass burning, and wind dispersion."
    )

    c1, c2, c3 = st.columns(3)
    traffic = c1.slider("Peak Traffic Cut (%)", 0, 100, 25)
    biomass = c2.slider("Biomass / Crop Burning Shift (%)", 0, 100, 10)
    wind_delta = c3.slider("Wind Vector Delta (m/s)", -5.0, 10.0, 1.5)

    if st.button("Run Causal Counterfactual Simulation"):
        try:
            res = requests.post(
                f"{API_URL}/simulate",
                json={
                    "traffic_reduction_pct": traffic,
                    "crop_burning_increase_pct": biomass,
                    "wind_speed_delta_ms": wind_delta,
                },
            )
            if res.status_code == 200:
                sim_data = res.json()
                m1, m2, m3 = st.columns(3)
                m1.metric("Baseline AQI", sim_data["baseline_mean_aqi"])
                m2.metric("Simulated Policy AQI", sim_data["simulated_mean_aqi"])
                m3.metric("Net AQI Impact", f"{sim_data['net_aqi_change']} points")

                st.success(sim_data["policy_recommendation"])

                chart_df = pd.DataFrame(
                    {
                        "Hour": list(range(72)),
                        "Baseline": sim_data["baseline_curve"],
                        "Simulated Policy": sim_data["simulated_curve"],
                    }
                )
                st.line_chart(chart_df.set_index("Hour"))
        except Exception as e:
            st.error(f"Simulation service offline: {e}")

# TAB 3: Satellite Sentinel-5P
with tab_satellite:
    st.header("Copernicus Sentinel-5P TROPOMI Earth Observation")
    st.markdown(
        "Real-time tropospheric NO2 and Aerosol Optical Depth (AOD) column density mesh across Sargodha basin."
    )

    if st.button("Fetch Satellite Swath Data"):
        try:
            sat_resp = requests.get(f"{API_URL}/satellite/sentinel5p")
            if sat_resp.status_code == 200:
                sat_data = sat_resp.json()
                grid_df = pd.DataFrame(sat_data["grid_points"])

                col_a, col_b = st.columns(2)
                with col_a:
                    st.subheader("NO2 Tropospheric Column")
                    fig_no2 = px.scatter_mapbox(
                        grid_df,
                        lat="latitude",
                        lon="longitude",
                        color="no2_column_density",
                        size="no2_column_density",
                        color_continuous_scale="Reds",
                        zoom=9,
                        mapbox_style="carto-darkmatter",
                    )
                    st.plotly_chart(fig_no2, use_container_width=True)
                with col_b:
                    st.subheader("Aerosol Optical Depth (AOD)")
                    fig_aod = px.scatter_mapbox(
                        grid_df,
                        lat="latitude",
                        lon="longitude",
                        color="aerosol_optical_depth",
                        size="aerosol_optical_depth",
                        color_continuous_scale="Purples",
                        zoom=9,
                        mapbox_style="carto-darkmatter",
                    )
                    st.plotly_chart(fig_aod, use_container_width=True)
        except Exception as e:
            st.error(f"Satellite telemetry API offline: {e}")

# TAB 4: Shadow Canary Engine
with tab_canary:
    st.header("Champion vs. Challenger Shadow Router")
    st.markdown(
        "Real-time production shadow execution metrics evaluating 7 candidate models concurrently."
    )

    if st.button("Refresh Shadow Metrics"):
        try:
            shadow_resp = requests.get(f"{API_URL}/shadow/metrics")
            if shadow_resp.status_code == 200:
                shadow_data = shadow_resp.json()
                st.json(shadow_data)
        except Exception as e:
            st.error(f"Shadow router offline: {e}")

st.divider()
st.subheader("System Health")
if st.button("Check API Readiness"):
    try:
        health_resp = requests.get(f"{API_URL}/health")
        if health_resp.status_code == 200:
            st.json(health_resp.json())
        else:
            st.error("Health check failed")
    except Exception as e:
        st.error(f"Failed to connect to API: {e}")
