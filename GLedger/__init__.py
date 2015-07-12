from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'firebird+fdb://pygl:T12iiu@localhost:3050/home/mennoh/python/GLedger/GLedger/gldb.fdb'
db = SQLAlchemy(app)

from . import views