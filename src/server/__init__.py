"""Server module providing entry point to this service."""

from flask import Flask

app = Flask(__name__)
app.config.from_object('server.config')
