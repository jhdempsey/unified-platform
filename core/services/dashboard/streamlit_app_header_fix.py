import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional
import json

# Import environment-aware configuration
from config import (
    ENVIRONMENT, VERTICAL,
    KAFKA_BOOTSTRAP_SERVERS, SCHEMA_REGISTRY_URL,
    MLFLOW_TRACKING_URI, MLFLOW_UI_URL,
    MODEL_INFERENCE_URL, RAG_SERVICE_URL,
    PROMETHEUS_URL, DISCOVERY_AGENT_URL,
    REQUEST_TIMEOUT, KAFKA_CONSUMER_TIMEOUT,
    show_config
)

# Import vertical configuration
from verticals import (
    get_vertical_config, get_vertical_name, get_vertical_icon,
    get_vertical_description, get_vertical_topics, get_vertical_models,
    get_rag_examples, get_vertical_kpis, list_available_verticals
)

# Page configuration
vertical_config = get_vertical_config(VERTICAL)
st.set_page_config(
    page_title=get_vertical_name(VERTICAL),
    page_icon=get_vertical_icon(VERTICAL),
    layout="wide"
)
