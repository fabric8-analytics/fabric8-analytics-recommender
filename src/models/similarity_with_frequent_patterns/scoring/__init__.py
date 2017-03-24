from flask import Flask
from server import app

app = Flask(__name__)
app.config.from_object('server.config')
