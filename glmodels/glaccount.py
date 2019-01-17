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
from sqlalchemy.orm import validates
from sqlalchemy.orm.exc import NoResultFound
from datetime import date, datetime
import logging

    
class NoAccountError(ValueError):
    """ This is thrown when an account requested does not exist.
    
    The exception is thrown to be caught  by methods and  functions
    that are expecting to find an account with the key provided.
    """
    
    pass

class ShortSearchStringError(ValueError):
    """ A search string that is very short is bound to return
    many hits. To prevent a long list to appear, we error if
    the search string is short.
    """
    
    pass


class InvalidPostmonthError(ValueError):
    """ An edited postmonth was passed in that can not be converted
    into a valid internal postmonth.
    """ 
    
    pass


class AccountAlreadyExistsError(ValueError) :
    """ This is thrown when an account created already exists.
    """
    
    pass

class Accounts(db.Model):
    """ Accounts models the "immutable" properties of an account
    
    Accounts have the following fields:
        :id: a sequence number
        :name: the accounts account "number" as the user wants to see it
        :role: asset, liability, income, expense
        :parent_id: its place in the hierarchy, like an adjacency list
        :children: the list of dependents
        :balances: the balances for the account
    """
    
    VALID_ROLES = ['I', 'E', 'A', 'L']
    
    """ The list of valid roles.
    
        :I: Income
        :E: Expense
        :A: Asset
        :L: Liability 
    """
    
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, db.Sequence('account_id_seq'),primary_key=True)
    name = db.Column(db.String(15), nullable=False, unique=True)
    role = db.Column(db.String(1))
    parent_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    children = db.relationship('Accounts')
    balances = db.relationship('Balances', backref='accounts')
    updated_at = db.Column(db.DateTime) 
    #db.Index('byparent', 'parent_id', 'id')
    
    @validates('role') 
    def validate_role(self, id, role):
        if role not in self.VALID_ROLES:
            raise ValueError('Account role invalid')
        return role
            
    @classmethod
    def get_by_id(cls, requested_id):
        """ Get an account form the database by id """
        try:
            account = db.session.query(Accounts).filter_by(id=requested_id).first()
            if not account:
                raise NoAccountError('No account for id ' + str(requested_id))
            return account
        except NoResultFound:
            raise NoAccountError('No account for id ' + str(requested_id))

    @classmethod
    def get_by_name(cls, requested_name):
        """ Get an account from the database by name
        
        The name of an account is pointing to a single account row."""
        
        try:
            account = db.session.query(Accounts).filter_by(name=requested_name).first()
            if not account:
                raise NoAccountError('No account for ' + str(requested_name))
            return account
        except NoResultFound:
            raise NoAccountError('No account for ' + str(requested_name))
    
    @classmethod
    def create_account(cls, name=None, role=None, parent_name=None,
                       parent_id=None):
        """Create an account and add it as a child.
        
        This scripts all things to be done for adding an account
        while also attaching it in the structure. If either
        parent_id or parent_name is filled, the method adds the 
        account created to the children.
        
        Checks are made:
        
            1.   the account to be added doesn't exist
            2.   the parent account does exist; if not, an exception will be thrown
        
        """
        if not name:
            raise ValueError('name cannot be None')
        if cls.account_exists(requested_name=name):
            raise AccountAlreadyExistsError('Account with name ' + str(name) + ' already exists') 
        account = cls(name=name, role=role)
        parent = None
        if parent_id:
            parent = cls.get_by_id(parent_id)
        if parent_name and not parent_id:
            parent = cls.get_by_name(parent_name)
        if parent:
            parent.children.append(account)
        account.add()
        return account
    
    @classmethod
    def account_exists(cls, requested_id=None, requested_name=None):
        """ Return if an account exists, presented with an ID or 
        an account name 
        """
        if requested_id:
            return not (db.session.query(Accounts).filter_by(id=requested_id).all() == [])
        if requested_name:
            return not (db.session.query(Accounts).filter_by(name=requested_name).all() == [])
        raise NoAccountError('An account id or name is mandatory')

    def _balance_for(self):
        """ Set up a query for the balance(s) of this account """
        return db.session.query(Balances).filter_by(accounts=self)
    
    def parentaccount(self):
        """ Get the parent of this account as an account """
        if hasattr(self, 'parent_account'):
            return self.parent_account
        else:
            parent_accounts = db.session.query(Accounts).filter_by(id=self.parent_id).all()
            if len(parent_accounts) > 0:
                self.parentaccount = parent_accounts[0]
                return parent_accounts[0]
            else:
                return None
    
    def __repr__(self):
        displayStr = 'Account(name = {}'.format(self.name, )
        if self.role:
            displayStr = displayStr + ', role = {}'.format(self.role) + ')'
        return displayStr
    
    def add(self):
        """ Add this account to the session """
        self.updated_at = datetime.today()
        db.session.add(self)
        
    def update_role_or_parent(self, new_role=None, new_parent=None):
        """ Update the parent and or role attribute.
        
        These are the only attributes that may be updated. """
        if new_parent:
            parent = Accounts.get_by_name(new_parent)
            if parent:
                self.parent_id = parent.id
                self.updated_at = datetime.today()
            else:
                raise ValueError('Account ' + repr(new_parent) + ' (new parent) does not exist')
        if new_role:
            self.role = new_role
            self.updated_at = datetime.today()
        
    def current_balance(self):
        """ Return the last known balance of the account """
        balance_last_known = self._balance_for().order_by(Balances.postmonth.desc()).all()
        if balance_last_known == []:
            return 0
        else:
            return balance_last_known[0].amount
        
    def balance_ultimo(self, postmonth, balance_so_far=0):
        """ Return the balance of the account at the end of the postmonth """
        balance_requested = self._balance_for().filter(Balances.postmonth <= postmonth).order_by(Balances.postmonth.desc()).all()
        if balance_requested != []:
 ###           print('Adding balance ' + format(balance_requested[0].amount) + ' for ' + self.name)
            balance_so_far += balance_requested[0].amount
        for child in self.children:
            balance_so_far = child.balance_ultimo(postmonth, balance_so_far)
        return balance_so_far
    
    def debit_credit(self):
        """ Return a debit/credit indicator for the account.
        
        The indicator is returned from the role."""
        if self.role == 'A' or self.role == 'E':
            return 'Db'
        if self.role == 'L' or self.role == 'I':
            return 'Cr'
        # Come here, unknown role: crash
        raise ValueError('Unknown role ' + role + ' in account ' + self.name)
    
    def is_debit(self):
        """ Is this account a debit account? """
        return (self.debit_credit() == 'Db')
    
    def is_credit(self):
        """ Is this account a credit account? """
        return (self.debit_credit() == 'Cr')
        
    def post_amount(self, debit_credit, post_amount, value_date):
        """Post an amount to this account. 
        
        This is a transaction script. The script runs as follows:
        1. Get the balance row for the postmonth
        2. apply the amount (using a function) to this row
        3. return the new balance 
        """
        postmonth = postmonth_for(value_date)
        balance_requested = self._balance_for().filter_by(postmonth = postmonth).order_by(Balances.postmonth.desc()).first()
        if balance_requested is None:
            balance_requested = Balances(account_id=self.id, 
                                         postmonth=postmonth, amount=0,
                                         value_date=datetime.today())
            balance_requested.add()
        balance_requested.update_with(debit_credit, post_amount)
        return balance_requested.amount
    
class Balances(db.Model):
    """Balances model the balances at different moments in time
    
    A balance is created for each accounting period of a month.
    After the end of the month it retains the ultimo balance
    for further reference. During the accounting month it contains the 
    current balance.
    
    A balance is made upon receiving the first posting of the accounting
    month. If a record for an older month is returned, that is the current
    balance; no postings for the current month have been received.
    
    Balances have the following fields:
        :id: a sequence number
        :account_id: the sequence number of the account this is the balance of
        :postmonth: the postmonth in the format yyyymm
        :currency: the currency code (preferably : use ISO)
        :amount: the amount 
    """
    
    __tablename__ = 'balances'
    id = db.Column(db.Integer, db.Sequence('balance_id_seq'),primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    postmonth = db.Column(db.Numeric(precision = 6))
    value_date = db.Column(db.DateTime, nullable=False)
    amount = db.Column(db.Numeric(precision = 14))
    updated_at = db.Column(db.DateTime) 
    db.Index('bymonth', 'account_id', 'postmonth')
    
    @validates('postmonth')
    def validate_postmonth(self, id, postmonth):
        """ the post month can only be the current or an existing, active month
        """
        
        months_db = db.session.query(Postmonths).filter_by(postmonth=postmonth).all()
        if (months_db != []):
            if (months_db[0].status_can_post()):
                return postmonth
            else:
                raise ValueError('Postmonth not active')       
        current_postmonth  = postmonth_for(date.today())
        if postmonth != current_postmonth:
            raise ValueError('Post month must exist or be current month')
        return postmonth
    
    def add(self):
        self.updated_at = datetime.today()
        db.session.add(self)
        
    def update(self):
        self.updated_at = datetime.today()
        db.session.update(self)
        
    def update_with(self, debit_credit, post_amount):
        """ Update the balance with the amount to be applied. """
        account = Accounts.get_by_id(self.account_id)
        if account.debit_credit() == debit_credit:
            self.amount += post_amount
        else:
            self.amount -= post_amount

    def __repr__(self):
        return 'Balances(amount = {}, postmonth = {}, account {})'.format(self.amount, self.postmonth, self.account_id)

class AccountList():
    """ A list of accounts is returned for showing 
    
    The search string must be at least 3 characters, to  prevent an overly
    long result list. If the search string is none, collect the accounts last added. If no account exists where the name contains the 
    search string, return an empty list.
    """
    
    def __init__(self, search_string=None, pagelength=10,page=1):
        """Initialize the list, using search_string as a selection """
        q = db.session.query(Accounts).order_by(Accounts.updated_at.desc())
        if search_string:
            if len(search_string) < 3:
                raise ShortSearchStringError('Search string must be at least 3 characters') 
            q = q.filter(Accounts.name.like('%'+search_string+'%'))
        skip_records = (page - 1) * pagelength
        if skip_records < 0:
            skip_records = 0
        logging.debug('Skip records: ' + str(skip_records))
        if skip_records:
            q = q.offset(skip_records)
        q = q.limit(pagelength)
        logging.debug('SQL is ' + str(q))
        self.account_list = q.all()
        
    def as_list(self):
        """ Return the embedded list 
        """
        
        return self.account_list
    
    def as_dict(self):
        """ Return the embedded list as a dictionary.
        
        The dictionary has a key of account name and the list entry as value """
        account_dictionary = {} 
        for account in self.account_list:
            account_dictionary[account.name] = account
        return account_dictionary
        
class Postmonths(db.Model):
    
    __tablename__ = 'postmnths'
    postmonth = db.Column(db.Integer, primary_key=True)
    monthstat = db.Column(db.String(1), nullable=False)
    
    ACTIVE = 'a'
    CLOSED = 'c'
    
    def add(self):
        """ Add this postmonth to the session 
        """
        
        self.updated_at = datetime.today()
        db.session.add(self)
    
    @validates('monthstat')
    def validate_monthstat(self, id, monthstat):
        if (monthstat != self.ACTIVE) and (monthstat != self.CLOSED):
            raise ValueError('Invalid status in postmonth')
        return monthstat
    
    @staticmethod
    def internal(month_string):
        """ Return an internally formatted postmonth for the passed in
        edited month string.
        
        The edited string has the format mm-yyyy.
        """
        
        # Check the format
        if (not month_string[0:2].isdigit() or not month_string[3:7].isdigit()
            or month_string[2:3] != '-' or len(month_string) != 7):
            raise InvalidPostmonthError('The postmonth could not be converted')
        month = int(month_string[0:2])
        year = int(month_string[3:7])
        return 100 * year + month
    
    @staticmethod
    def external(postmonth):
        """ Return a string for a 6 digit postmonth integer
        """
        
        return "{0:02}-{1}".format(postmonth % 100, int(postmonth / 100))
    
    def status_can_post(self):
        """ Returns True is the status of this postmonth
        is active, i.e. posting in it is permitted.
        """
        
        return self.monthstat == self.ACTIVE
    
    def str():
        """ Returns the postmonth key as a formatted string
        """
        
        return "{0:02}-{1}".format(self.postmonth % 100, int(self.postmonth / 100))
        
def postmonth_for(postdate):
    """ Return the postmonth from a postdate
    
    This is a function which determines for a date in which
    postmonth it is. It is used for getting the correct balance of an account
    as well as determining in which post month a posting belongs.
    """
    return (postdate.year * 100 + postdate.month)

def postmonth_today():
    """ Return the postmonth for today's date
    """
    
    return postmonth_for(date.today())
