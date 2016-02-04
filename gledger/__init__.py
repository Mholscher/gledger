#    Copyright 2015 Menno Hölscher
#
#    This file is part of gledger.

#    gledger is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    gledger is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.

#    You should have received a copy of the GNU Lesser General Public License
#    along with gledger.  If not, see <http://www.gnu.org/licenses/>.

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import configparser
from flask_wtf.csrf import CsrfProtect
import logging

app = Flask(__name__)
config = configparser.ConfigParser()
config.read('localgledger.cfg')
app.config['SQLALCHEMY_DATABASE_URI'] = config['DATABASE']['SQLALCHEMY_DATABASE_URI']
db = SQLAlchemy(app)
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
app.config['SECRET_KEY'] = config['KEYS']['SECRET_KEY']
CsrfProtect(app)
logging.basicConfig(filename='gledger.log', level=logging.DEBUG) 
logging.debug('Debug logging')

from glmodels.glaccount import Accounts
from glmodels.glaccount import Balances
from glmodels.glposting import Postings
from glmodels.glposting import Journals
from . import views