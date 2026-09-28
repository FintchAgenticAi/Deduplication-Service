from uvicorn.middleware.wsgi import WSGIMiddleware

from app import app as flask_app


app = WSGIMiddleware(flask_app)
