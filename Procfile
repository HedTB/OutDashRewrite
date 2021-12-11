heroku ps:scale worker=1
worker: python main.py
web: hypercorn -b 0.0.0.0:8080 app:app