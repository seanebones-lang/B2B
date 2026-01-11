"""Health check API endpoint for Streamlit"""

import streamlit as st
import json
from utils.health import get_health_checker


def health_endpoint():
    """Streamlit page for health check"""
    st.set_page_config(page_title="Health Check", page_icon="🏥", layout="centered")
    
    st.title("🏥 System Health Check")
    
    checker = get_health_checker()
    
    # Perform health check
    if st.button("🔄 Refresh Health Status"):
        st.rerun()
    
    health_status = checker.check_health()
    
    # Display overall status
    status = health_status["status"]
    if status == "healthy":
        st.success(f"✅ System Status: {status.upper()}")
    elif status == "degraded":
        st.warning(f"⚠️ System Status: {status.upper()}")
    else:
        st.error(f"❌ System Status: {status.upper()}")
    
    st.write(f"**Last Check:** {health_status['timestamp']}")
    
    # Display individual checks
    st.subheader("Component Status")
    for component, check in health_status["checks"].items():
        with st.expander(f"{component.upper()} - {check['status'].upper()}"):
            st.write(f"**Status:** {check['status']}")
            st.write(f"**Message:** {check.get('message', 'N/A')}")
            if "details" in check:
                st.json(check["details"])
    
    # Display metrics
    st.subheader("System Metrics")
    metrics = checker.get_metrics()
    st.json(metrics)
    
    # Raw JSON export
    st.subheader("Raw Health Data")
    with st.expander("View Raw JSON"):
        st.code(json.dumps(health_status, indent=2, default=str))
