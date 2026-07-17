import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configure page
st.set_page_config(
    page_title="AQI Predictor",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_URL = "http://localhost:8000"

st.title("🌍 AQI Predictor Dashboard")
st.markdown("Air Quality Index forecast and analytics for Sargodha, Pakistan.")

# Sidebar for controls
st.sidebar.header("Controls")
try:
    # Fetch available models
    models_resp = requests.get(f"{API_URL}/models")
    if models_resp.status_code == 200:
        models_data = models_resp.json()
        model_list = models_data.get("models", [])
        model_names = {m["id"]: m["name"] for m in model_list}
        default_model = models_data.get("default_model_id", "bilstm_attention_tf")
        
        selected_model_id = st.sidebar.selectbox(
            "Select Model",
            options=list(model_names.keys()),
            format_func=lambda x: model_names.get(x, x),
            index=list(model_names.keys()).index(default_model) if default_model in model_names else 0
        )
    else:
        st.sidebar.error("Failed to load models from API.")
        selected_model_id = "bilstm_attention_tf"
except Exception as e:
    st.sidebar.warning(f"API not available: {e}")
    selected_model_id = "bilstm_attention_tf"

if st.sidebar.button("Generate Forecast"):
    with st.spinner("Generating prediction..."):
        try:
            pred_resp = requests.post(f"{API_URL}/predict", params={"model_id": selected_model_id})
            if pred_resp.status_code == 200:
                data = pred_resp.json()
                
                # Top metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("Current AQI", f"{data['current_aqi']} ({data['current_level']})")
                col2.metric("Model Used", data['model_type'])
                col3.metric("Alert Status", "Active ⚠️" if data['alert'] else "Normal ✅")
                
                st.info(f"**Health Advisory**: {data['summary']}")
                
                # Forecast Chart
                st.subheader("72-Hour AQI Forecast")
                hourly = data.get("hourly_predictions", [])
                if hourly:
                    df = pd.DataFrame(hourly)
                    df['timestamp'] = pd.to_datetime(df['timestamp'])
                    
                    fig = go.Figure()
                    
                    # 95% Confidence Interval
                    if 'aqi_upper_95' in df.columns and 'aqi_lower_95' in df.columns:
                        fig.add_trace(go.Scatter(
                            name='95% CI Upper',
                            x=df['timestamp'],
                            y=df['aqi_upper_95'],
                            mode='lines',
                            line=dict(width=0),
                            showlegend=False
                        ))
                        fig.add_trace(go.Scatter(
                            name='95% CI',
                            x=df['timestamp'],
                            y=df['aqi_lower_95'],
                            mode='lines',
                            line=dict(width=0),
                            fillcolor='rgba(68, 68, 68, 0.2)',
                            fill='tonexty'
                        ))
                        
                    # Predicted AQI
                    fig.add_trace(go.Scatter(
                        name='Predicted AQI',
                        x=df['timestamp'],
                        y=df['aqi_predicted'],
                        mode='lines+markers',
                        line=dict(color='rgb(31, 119, 180)', width=2)
                    ))
                    
                    # Alert Threshold Line
                    fig.add_hline(y=150, line_dash="dash", line_color="red", annotation_text="Unhealthy Threshold")
                    
                    fig.update_layout(
                        xaxis_title="Time",
                        yaxis_title="AQI",
                        hovermode="x unified"
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.error(f"Prediction failed: {pred_resp.text}")
        except Exception as e:
            st.error(f"Failed to connect to API: {e}")

st.divider()

st.subheader("System Health")
if st.button("Check API Health"):
    try:
        health_resp = requests.get(f"{API_URL}/health")
        if health_resp.status_code == 200:
            st.json(health_resp.json())
        else:
            st.error("Health check failed")
    except Exception as e:
        st.error(f"Failed to connect to API: {e}")
