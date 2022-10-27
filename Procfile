heroku ps:scale worker=1
worker: python main.py
web: uvicorn app:app --host 0.0.0.0 --port 80
