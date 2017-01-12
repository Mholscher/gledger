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
from sqlalchemy.orm.exc import NoResultFound
from datetime import date, datetime
from .glaccount import Accounts

class PostingWOJournal(ValueError):
    """Exception thrown when a posting without journal is being made.
    """
    
    pass

class NoJournalError(ValueError):
    """ There is no journal for the requested id """
    pass

class JournalBalanceError(Exception):
    """ The postings in a journal do not balance """
    pass

class Journals(db.Model) :
    __tablename__ = 'journals'
    id = db.Column(db.Integer, db.Sequence('journal_id_seq'),primary_key=True)
    journalpostings = db.relationship('Postings', backref='journal')
    journalstat = db.Column(db.String(1), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    
    UNPROCESSED = 'U'
    PROCESSED = 'P'
    
    @classmethod
    def get_by_id(cls, requested_id):
        """ Return the journal row for requested_id """
        try:
            journal = db.session.query(Journals).filter_by(id=requested_id).first()
            if not journal:
                raise NoJournalError('No journal for id ' + str(requested_id))
            return journal
        except NoResultFound:
            raise NoJournalError('No journal for id ' + str(requested_id))
        
    def add(self) :
        """ Add this journal to the session 
        
        Make sure it is timestamped"""
        
        self.updated_at = datetime.today()
        db.session.add(self)
        
    def post_journal(self):
        """ Post the posting of this journal to the accounts.
        
        The journal is first checked to balance. If it doesn't
        balance, it is marked for being unprocessable. The 
        transaction is committed, but after that an exception
        is raised."""
        journal_balance = 0
        if self.journalpostings:
            firstpostingccy = self.journalpostings[0].currency
        for posting in self.journalpostings:
            if not posting.currency == firstpostingccy:
                continue
            account_role = Accounts.get_by_id(posting.account_id).role
            if account_role in ['I', 'A']:
                journal_balance += posting.amount
            else:
                journal_balance -= posting.amount
        if not journal_balance == 0:
            raise JournalBalanceError
        

class Postings(db.Model) :
    __tablename__ = 'postings'
    id = db.Column(db.Integer, db.Sequence('posting_id_seq'),primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    journals_id = db.Column(db.Integer, db.ForeignKey('journals.id'), nullable=False)
    postmonth = db.Column(db.Numeric(precision=6))
    currency = db.Column(db.String(3), nullable=False, default='EUR')
    amount = db.Column(db.Numeric(precision = 14), nullable=False)
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

