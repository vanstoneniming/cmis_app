#!/bin/bash
cd /www/wwwroot/cmis_app
source py-project-env cmis_app
export STREAMLIT_SERVER_FOLDER_PATH=/tmp/.streamlit
mkdir -p /tmp/.streamlit
sudo mkdir -p /root/.streamlit 2>/dev/null || true
streamlit run app.py --server.port=8501 --server.address=0.0.0.0 --browser.gatherUsageStats=false
