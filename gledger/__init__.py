from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'firebird+fdb://sysdba:2demacht512@localhost:3050/gldb.fdb'
db = SQLAlchemy(app)

from glmodels.glaccount import Accounts
from glmodels.glaccount import Balances
from . import views