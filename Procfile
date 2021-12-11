heroku ps:scale worker=1
worker: python test.py
web: hypercorn -b 0.0.0.0:$PORT test:app