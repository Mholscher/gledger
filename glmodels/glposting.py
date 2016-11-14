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

from gledger import db
import flask_sqlalchemy
from sqlalchemy.orm import validates
from datetime import date, datetime
from .glaccount import Accounts

class Postings(db.Model) :
    __tablename__ = 'postings'
    id = db.Column(db.Integer, db.Sequence('posting_id_seq'),primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    journals_id = db.Column(db.Integer, db.ForeignKey('journals.id'))
    postmonth = db.Column(db.Numeric(precision=6))
    value_date = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    
    def _id_for_account(from_name) :
        """ Get an ID for an account for which we only have the name """
        account = Accounts.get_by_name(from_name)
        return account.id
    
    def add(self) :
        """ Add this posting to the session 
        
        Make sure it is timestamped"""
        
        self.updated_at = datetime.today()
        db.session.add(self)

class Journals(db.Model) :
    __tablename__ = 'journals'
    id = db.Column(db.Integer, db.Sequence('journal_id_seq'),primary_key=True)
    journalpostings = db.relationship('Postings', backref='journal')
    journalstat = db.Column(db.String(1), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    
    UNPROCESSED = 'U'
    PROCESSED = 'P'
    
    def add(self) :
        """ Add this journal to the session 
        
        Make sure it is timestamped"""
        
        self.updated_at = datetime.today()
        db.session.add(self)
