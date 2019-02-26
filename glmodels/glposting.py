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

""" The module contains the postings. After postings are made these
should never be changed, corrections will be undertaken by creating
new correcting postings. This is because postings are part of a journal,
a composite of postings that belong together and always need to balance.
"""

from gledger import db
from sqlalchemy.orm import validates
from sqlalchemy.orm.exc import NoResultFound
from datetime import date, datetime
from .glaccount import Accounts, postmonth_for, NoAccountError, Postmonths


class InvalidJournalError(Exception):
    """ The base exception for failing journals 
    """
    
    pass

class PostingWOJournal(InvalidJournalError):
    """Exception thrown when a posting without journal is being made.
    """
    
    pass

class NoJournalError(ValueError):
    """ There is no journal for the requested id 
    """
    
    pass

class JournalBalanceError(InvalidJournalError):
    """ The postings in a journal do not balance 
    """
    
    pass

class InvalidDebitCreditError(InvalidJournalError):
    """A posting contains an invalid debit/credit indicator 
    """
    
    pass

class NoPostingInJournal(InvalidJournalError):
    """ A journal was submitted without postings 
    """
    
    pass

class Journals(db.Model):
    """ The journal is the way postings are delivered by clients.
    
    The journal consists of an unknown number of postings. It must be at least
    two, because the total balance (debit +, credit -) must be zero.
    The journal controls the way the postings are grouped, all postings
    or none are posted by the system. To that purpose the Journals
    have a flag journalstat that tells the system its status.
    
    Journals have the following fields :
        :id: the system generated sequence number
        :extkey: the key to the callings systems object, this is optional
        :journalstat: the status of the journal
        :updated_at: The timestamp of the last update
    """
    
    __tablename__ = 'journals'
    id = db.Column(db.Integer, db.Sequence('journal_id_seq'), primary_key=True)
    extkey = db.Column(db.String(150), nullable=True)
    journalpostings = db.relationship('Postings', backref='journal')
    journalstat = db.Column(db.String(1), nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
    
    UNPROCESSED = 'U'
    PROCESSED = 'P'
    FAILED = 'F'
    
    @classmethod
    def get_by_id(cls, requested_id):
        """ Return the journal row for requested_id 
        """
        
        try:
            journal = db.session.query(Journals).filter_by(id=requested_id).\
                first()
            if not journal:
                raise NoJournalError('No journal for id ' + str(requested_id))
            return journal
        except NoResultFound:
            raise NoJournalError('No journal for id ' + str(requested_id))
        
    @classmethod
    def create_from_dict(cls, journdict):
        """Creates a new journal including posting from
        a dictionary created from json 
        """
        
        if 'postings' not in journdict['journal']\
            or journdict['journal']['postings'] is None:
            raise NoPostingInJournal('Empty journal')
        newjournal = cls(journalstat=cls.UNPROCESSED,\
                         extkey=journdict['journal']['extkey'])
        newjournal.add()
        for posting in journdict["journal"]["postings"]:
            try:
                Postings.create_from_dict(posting,newjournal)
            except NoAccountError as exc:
                raise InvalidJournalError(str(exc)) from exc
        return newjournal
    
    @classmethod
    def postings_for_id(cls, journal_id):
        """ Assemble the postings in journal with id journal_id 
        """
        
        posts = db.session.query(Postings).filter_by(journals_id=journal_id).\
                    all()
        if posts == []:
            raise NoJournalError('Journal ' + str(journal_id) + ' does not exist')
        return posts
    
    @classmethod
    def get_by_key(self, extkey=None):
        """ Get the journal data without postings by the supplied extkey
        """

        if extkey is None:
            raise NoJournalError('An external key is required')
        journal = db.session.query(Journals).\
            filter_by(extkey=extkey).first()
        if not journal:
            raise NoJournalError('No journal with key ' + extkey)
        return journal

    @classmethod
    def postings_for_key(self, journal_key):
        """ Assemble the posting in the journal by the external key 
        """
        
        journal = db.session.query(Journals).\
            filter_by(extkey=journal_key).first()
        if not journal:
            raise NoJournalError('No journal for key ' + str(journal_key))
        return journal.journalpostings
        
    @validates('journalstat')
    def validate_status(self, id, journalstat):
        """ Check if the status is valid 
        """
        
        if not journalstat in [self.UNPROCESSED, self.PROCESSED, self.FAILED]:
            raise InvalidJournalStatus('Status '+ str(journalstat) + \
                                        ' is invalid')
        return journalstat
    
    def add(self) :
        """ Add this journal to the session 
        
        Make sure it is timestamped
        """
        
        self.updated_at = datetime.today()
        db.session.add(self)
        
    def post_journal(self):
        """ Post the posting of this journal to the accounts.
        
        The journal is first checked to balance. If it doesn't
        balance, it is marked for being unprocessable. 
        """
        
        journal_balance = 0
        if self.journalpostings:
            firstpostingccy = self.journalpostings[0].currency
        for posting in self.journalpostings:
            if not posting.currency == firstpostingccy:
                continue
            if posting.is_debit():
                journal_balance += posting.amount
            else:
                journal_balance -= posting.amount
        if not journal_balance == 0:
            raise JournalBalanceError('Journal balance = ' + str(journal_balance))
        for posting in self.journalpostings:
            try:
                posting.apply()
            except NoAccountError as exc:
                raise InvalidJournalError(str(exc)) from exc
        self.journalstat = self.PROCESSED
        

class Postings(db.Model) :
    """ The individual postings. 
    
    Postings have the following fields :
        :id: the system generated sequence number
        :account_id: the account the posting is to be applied to
        :journals_id: the sequence number of the journal the posting is in
        :postmonth: The accounting month the posting was posted in
        :currency: The currency of the posting
        :amount: the posted amount in the smallest unit
        :debcred: if the account is to be debited or credited
        :value_date: the date the posting should take effect
        :updated_at: The timestamp of the last update
    
    """
    
    __tablename__ = 'postings'
    id = db.Column(db.Integer, db.Sequence('posting_id_seq'),primary_key=True)
    accounts_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    journals_id = db.Column(db.Integer, db.ForeignKey('journals.id'), nullable=False)
    postmonth = db.Column(db.Numeric(precision=6))
    currency = db.Column(db.String(3), nullable=False, default='EUR')
    amount = db.Column(db.Numeric(precision = 14), nullable=False)
    debcred = db.Column(db.String(2),nullable=False)
    db.CheckConstraint("debcred in ('Db', 'Cr')", name='debcredval'), 
    value_date = db.Column(db.DateTime, nullable=False)
    updated_at = db.Column(db.DateTime, nullable=False)
        
    @classmethod
    def create_from_dict(cls, posting, for_journal):
        """Create a posting from a dictionary with the applicable fields. 
        
        TODO This routine leaks info of the json to the model. Wants
        refactoring!
        """
        
        value_date = datetime(int(posting["valuedate"][0:4]), 
                              int(posting["valuedate"][5:7]),
                              int(posting["valuedate"][8:10]))
        newposting = cls(postmonth=postmonth_for(value_date), 
                         value_date=value_date,
                         currency=posting["currency"],
                         amount=posting["amount"],
                         debcred=posting["debitcredit"])
        newposting.accounts_id = newposting._id_for_account(posting["account"])
        newposting.journal = for_journal
        newposting.add()
        for_journal.journalpostings.append(newposting)
        return newposting
    
    @classmethod
    def postings_for_account(cls, account, post_limit=50, month=None):
        """ This method gets a list of postings for the account passed.
        
        It has a post_limit for the number of postings. -1 is unlimited (warning:
        That may return very many postings! 
        """
        
        posts = db.session.query(Postings).filter_by(accounts_id=account.id)
        if month:
            posts = posts.filter_by(postmonth=Postmonths.internal(month))
        if not post_limit == -1:
            posts = posts.limit(post_limit)
        return posts.all()
        
    def _id_for_account(self, from_name) :
        """ Get an ID for an account for which we only have the name 
        """
        
        account = Accounts.get_by_name(from_name)
        return account.id
    
    def add(self) :
        """ Add this posting to the session 
        
        Make sure it is timestamped
        """
        
        self.updated_at = datetime.today()
        db.session.add(self)
        
    @validates('debcred')
    def validate_debcred(self, id, debitcredit):
        """ Check if debit/credit indicator has a valid value 
        """
        
        if not debitcredit in ['Db', 'Cr']:
            raise InvalidDebitCreditError('Debit credit indicator ' + debitcredit + 
                                          'is invalid')
        return debitcredit
        
    def is_debit(self):
        
        return (self.debcred == 'Db')
    
    def is_credit(self):
        
        return (self.debcred == 'Cr')
    
    def apply(self):
        """ Apply this posting to its account.
        
        Applying means adjusting the balance with the amount of
        the posting 
        """
        
        account = Accounts.get_by_id(self.accounts_id)
        account.post_amount(self.debcred, self.amount, self.value_date)
        
