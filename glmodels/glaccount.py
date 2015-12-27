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
from datetime import date

class Accounts(db.Model) :
    """ Accounts models the "immutable" properties of an account
    
    Accounts have the following fields:
    id - a sequence number
    name - the accounts account "number" as the user wants to see it
    role - asset, liability, income, expense
    parent - its place in the hierarchy, like an adjacency list
    children - the list of dependents
    balances - the balances for the account
    """
    global VALID_ROLES
    VALID_ROLES = ['I', 'E', 'A', 'L']
    """ The list of valid roles.
    
    I = Income
    E = Expense
    A = Asset
    L = Liability 
    """
    
    __tablename__ = 'accounts'
    id = db.Column(db.Integer, db.Sequence('account_id_seq'),primary_key=True)
    name = db.Column(db.String(15), nullable=False, index = True, unique = True)
    role = db.Column(db.String(1))
    parent = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    children = db.relationship('Accounts')
    balances = db.relationship('Balances', backref = 'accounts')
    updated_at = db.Column(db.DateTime) 
    
    @validates('role') 
    def validate_role(self, id, role) :
        if role not in VALID_ROLES :
            raise ValueError('Account role invalid')
        return role
            
    @classmethod
    def get_by_id(cls, requested_id) :
        """ Get an account form the database by id """
        return db.session.query(Accounts).filter_by(id=requested_id).one()

    @classmethod
    def get_by_name(cls, requested_name) :
        """ Get an account form the database by name
        
        The name of an account is pointing to a single account row."""
        acc = db.session.query(Accounts).filter_by(name=requested_name).one()
        return acc

    def _balance_for(self) :
        """ Set up a query for the balance(s) of this account """
        return db.session.query(Balances).filter_by(accounts=self)
    
    def parentaccount(self) :
        """ Get the parent of this account as an account """
        if hasattr(self, 'parent_account') :
            return self.parent_account
        else :
            parent_accounts = db.session.query(Accounts).filter_by(id=self.parent).all()
            if len(parent_accounts) > 0 :
                self.parentaccount = parent_accounts[0]
                return parent_accounts[0]
            else :
                return None
    
    def __repr__(self) :
        return 'Account {} id {}'.format(self.name, self.id)
    
    def add(self) :
        """ Add this account to the session """
        db.session.add(self)
        
    def current_balance(self) :
        """ Return the last known balance of the account """
        balance_last_known = self._balance_for().order_by(Balances.postmonth.desc()).all()
        if balance_last_known == [] :
            return 0
        else :
            return balance_last_known[0].amount
        
    def balance_ultimo(self, postmonth, balance_so_far = 0) :
        """ Return the balance of the account at the end of the postmonth """
        balance_requested = self._balance_for().filter(Balances.postmonth <= postmonth).order_by(Balances.postmonth.desc()).all()
        if balance_requested != [] :
 ###           print('Adding balance ' + format(balance_requested[0].amount) + ' for ' + self.name)
            balance_so_far += balance_requested[0].amount
        for child in self.children :
            balance_so_far = child.balance_ultimo(postmonth, balance_so_far)
        return balance_so_far
        
    
class Balances(db.Model) :
    """Balances model the balances at different moments of time
    
    A balance is created for each accounting period of a month.
    After the end of the month it retains the ultimo balance
    for further reference. During the accounting month it contains the 
    current balance.
    
    A balance is made upon receiving the first posting of the accounting
    month. If a record for an older month is returned, that is the current
    balance; no postings for the current month have been received.
    
    Balances have the following fields:
    id - a sequence number
    account_id - the sequence number of the account this is the balance of
    postmonth - the postmonth in the format yyyymm
    currency - the currency code (preferably : use ISO)
    amount - the amount 
    """
    
    __tablename__ = 'balances'
    id = db.Column(db.Integer, db.Sequence('balance_id_seq'),primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'))
    postmonth = db.Column(db.Numeric(precision = 6))
    value_date = db.Column(db.DateTime, nullable=False)
    amount = db.Column(db.Numeric(precision = 14))
    updated_at = db.Column(db.DateTime) 
    db.Index('bymonth', 'account_id', 'postmonth')
    
    @validates('postmonth')
    def validate_postmonth(self, id, postmonth) :
        """ the post month can only be the current or an existing, active month"""
        months_db = db.session.query(Postmonths).filter_by(postmonth=postmonth).all()
        if (months_db != []) :
            if (months_db[0].monthstat == ACTIVE) :
                return postmonth
            else :
                raise ValueError('Postmonth not active')       
        current_postmonth  = postmonth_for(date.today())
        if postmonth != current_postmonth :
            raise ValueError('Post month must exist or be current month')
        return postmonth
    
    def add(self) :
        db.session.add(self)
        
    def update(self) :
        db.session.update(self)

    def __repr__(self) :
        return 'Account balance {} account {} id {}'.format(self.amount, self.account_id, self.id)
    
class Postmonths(db.Model) :
    
    __tablename__ = 'postmnths'
    postmonth = db.Column(db.Integer, primary_key=True)
    monthstat = db.Column(db.String(1), nullable=False)
    
    global ACTIVE, CLOSED
    ACTIVE = 'a'
    CLOSED = 'c'
    
    def add(self) :
        """ Add this postmonth to the session """
        db.session.add(self)
    
    @validates('monthstat')
    def validate_monthstat(self, id, monthstat) :
        if (monthstat != ACTIVE) and (monthstat != CLOSED) :
            raise ValueError('Invalid status in postmonth')
        return monthstat
        
def postmonth_for(postdate) :
    """ Return the postmonth from a postdate
    
    This is a function which determines for a date in which
    postmonth it is. It is used for getting the correct balance of an account
    as well as determining in which post month a posting belongs.
    """
    return (postdate.year * 100 + postdate.month)
