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

app = Flask('gledger')
db = SQLAlchemy(app)
# CsrfProtect(app)

from .postingapi import postingapi as api
app.register_blueprint(api, url_prefix='/api')
app.config.from_pyfile('localgledger.cfg')


logging.basicConfig(filename='gledger.log', level=logging.INFO) 
logging.debug('Debug logging')

from glmodels.glaccount import Accounts
from glmodels.glaccount import Balances
from glmodels.glposting import Postings
from glmodels.glposting import Journals
from . import views
