web: alembic upgrade head && streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true
worker: alembic upgrade head && python -m ingestion
