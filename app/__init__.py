from flask import Flask, render_template,redirect,url_for,request,session,flash
from functools import wraps
from flask.ext.socketio import SocketIO,emit
from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

app.config.from_object('config')


db = SQLAlchemy(app)

print 'db object successfully created'
socketio = SocketIO(app)

from app import views,models
