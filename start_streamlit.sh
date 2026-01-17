#!/bin/bash
cd /www/wwwroot/cmis_app
exec /www/server/pyporject_evn/cmis_app_venv/bin/streamlit run /www/wwwroot/cmis_app/app.py --server.port=8501 --server.address=0.0.0.0
