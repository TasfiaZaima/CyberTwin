"""Streamlit dashboard backed by the live CyberTwin API."""
from __future__ import annotations
import json, os
from urllib.error import URLError
from urllib.request import Request, urlopen
import pandas as pd
import plotly.express as px
import streamlit as st

API = os.getenv("CYBERTWIN_API", "http://localhost:8000")

def call(path: str, method: str = "GET", body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    request = Request(API + path, data=data, method=method, headers={"Content-Type":"application/json"})
    with urlopen(request, timeout=60) as response: return json.load(response)

st.set_page_config(page_title="CyberTwin", page_icon="🛡️", layout="wide")
st.title("🛡️ CyberTwin")
st.caption("IoT/edge behavioral digital twin — potential compromise indicators, not definitive attribution")
try:
    devices = call("/devices"); alerts = call("/alerts")
except (URLError, TimeoutError) as error:
    st.error(f"CyberTwin API is unavailable at {API}: {error}"); st.stop()

c1,c2,c3,c4 = st.columns(4)
c1.metric("Total devices", len(devices)); c2.metric("Healthy", sum(d["status"]=="NORMAL" for d in devices))
c3.metric("Anomalous", sum(d["status"]=="ANOMALOUS" for d in devices)); c4.metric("Active alerts", sum(a["status"]=="ACTIVE" for a in alerts))

st.subheader("Demonstration workflow")
b1,b2,b3 = st.columns(3)
if b1.button("1 · Generate normal data", use_container_width=True):
    call("/simulation/start", "POST", {"windows": 12}); st.success("Normal telemetry and features generated"); st.rerun()
if b2.button("2 · Train baselines", use_container_width=True):
    call("/baseline/train", "POST", {}); st.success("Baselines trained"); st.rerun()
selected = st.selectbox("Device", [d["device_id"] for d in devices])
if b3.button("3 · Simulate anomaly", use_container_width=True):
    try: call(f"/simulation/anomaly/{selected}", "POST", {}); st.warning("Safe anomaly generated and evaluated"); st.rerun()
    except Exception as error: st.error(str(error))

st.subheader("Topology")
st.code("Internet Simulation\n        │\n  Edge Gateway\n   /    │     \\\nCamera  Plug  Sensor")
state = call(f"/devices/{selected}/state")
device = state["device"]
color = {"NORMAL":"green","DEGRADED":"orange","ANOMALOUS":"red"}[device["status"]]
st.markdown(f"### {device['name']} · :{color}[{device['status']}] · score {device['anomaly_score']:.2f}")

features = call(f"/devices/{selected}/features")
if features:
    frame = pd.DataFrame(features).sort_values("window_end")
    for column, title in [("bytes_per_second","Traffic"),("connections_per_minute","Connections"),
                          ("unique_destinations","Destinations"),("anomaly_score","Anomaly score")]:
        st.plotly_chart(px.line(frame, x="window_end", y=column, title=title, markers=True), use_container_width=True)
if state["baseline"] and state["observed"]:
    base = pd.DataFrame(state["baseline"])[["feature_name","mean","percentile_05","percentile_95"]]
    base["observed"] = base["feature_name"].map(state["observed"])
    st.subheader("Expected vs observed"); st.dataframe(base, use_container_width=True)
st.subheader("Alerts")
st.dataframe(pd.DataFrame(alerts), use_container_width=True) if alerts else st.info("No alerts")

