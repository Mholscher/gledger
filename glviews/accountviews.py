#    gledger is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#   
#    gledger is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.

#    You should have received a copy of the GNU Lesser General Public License
#    along with gledger.  If not, see <http://www.gnu.org/licenses/>.

""" This module contains the view items associated with accounts.

Of course there is the account itself and the balances, but also
a list view to support a list screen of accounts, based on a list 
of model instances.
"""

from glmodels import PaginatorMixin
import glmodels.glaccount as model

class AccountView() :
    """ This class collects the data for displaying an existing account
    
    The view is a data collection which concerns everything
    viewed on the accounts maintenance screen. 
    
..  note:: 
        
        The way the collection is produced is as a dictionary with
        embedded data, for the account itself as strings,
        for the dependents as dictionaries. 
    
    """
    
    def __init__(self) :
        self.id = 0
        self.name = ''
        self.account = None
        
    @classmethod
    def create_view(cls,  id=None, name=None) :
        """ Creates a view for the id (preferred) or
        name passed as an argument. If the account does
        not exist, caller will receive the exception. It is
        not caught...
        """
        
        if (id is None) and (name is None) :
            raise model.NoAccountError('An id or name for an account must be given')
        # prefer id to name for fetching an account:
        accountView = cls()
        if (id is not None) :
            accountView.account = model.Accounts.get_by_id(id)
        else :
            accountView.account = model.Accounts.get_by_name(name)
        if accountView.account :
            accountView.name = accountView.account.name
            if accountView.account.parent_id:
                accountView.parent = \
                    model.Accounts.get_by_id(accountView.account.parent_id)
            else:
                accountView.parent = None
            accountView.children = accountView.account.children
        else :
            accountView.name = ''
            accountView.parent = None
            accountView.children = []
        return accountView
        
    def _account_dictionary(self) :
        if (not hasattr(self, 'account')) or (self.account is None) :
            raiseAttributeError('Account should exist and be populated')
        # Dispatch on columns in account, default use value 
        return {'id': self.account.id, 'name': self.account.name, 'role' : model.Accounts.ROLE_NAME[self.account.role] }
    
    def _parent_name_and_id(self) :
        # The check should not be necessary. The contract: call ONLY if parent exists
        if (not hasattr(self, 'parent')) or (self.parent is None) :
            return None
        return {'id' : self.parent.id, 'name' : self.parent.name}
    
    def _dictionary_from_childlist(self) :
        childlist = []
        for child in self.account.children :
            childlist.append({'id' : child.id, 'name': child.name})
        return childlist
            
    def as_dictionary(self) :
        """
        Return the accountview as a dictionary.
        
        This is primarily thought of as a halfway house
        to create the views, be it json or html. 
        """
        
        as_dictionary = {"account" : self._account_dictionary(), "children" : self._dictionary_from_childlist() }
        as_dictionary["parent"] = self._parent_name_and_id()
        as_dictionary["localtitle"] = 'Account ' + self.account.name
        return as_dictionary

class BalanceView():
    """ This class collects the data for displaying balance info for
    an account.

    The view is a data collection which concerns everything
    viewed on the accounts maintenance screen.
    """

    def __init__(self):

        self.id = None
        self.account_name = None
        self.postmonth = None
        self.balance = None

    @classmethod
    def create_view(cls, id=None, postmonth=None, name=None):
        """ Create a view for the balance of an account

        We prefer the id, which is the primary key. Name is acceptable,
        as it must be unique.

        The postmonth determines which balance we need, None means latest.
        """

        if id:
            account = model.Accounts.get_by_id(id)
        elif name:
            account = model.Accounts.get_by_name(name)
        else:
            raise model.NoAccountError('An id or name for an account must be given')
        view = cls()
        view.id = account.id
        view.account_name = account.name
        if postmonth:
            view.balance = account.balance_ultimo(postmonth)
            view.postmonth = postmonth
        else:
            view.balance = account.current_balance()
            view.postmonth = model.postmonth_today()
        return view

    def as_dictionary(self):
        """ Return this view as a dictionary
        """

        as_dictionary = {'id': self.id, 'name': self.account_name}
        as_dictionary['balance'] = "{0:.2f}".format(self.balance/100)
        as_dictionary['postmonth'] = model.Postmonths.external(self.postmonth)
        return as_dictionary


class AccountListView(PaginatorMixin, list):
    """ Gathers the information to display a list of accounts.

    The accounts are in a dictionary keyed by the account name, the accounts
    are also in a dictionary, with a key/value pair for each field.

    The view also holds page information. The length of a page, the page
    number and the total number of pages are in the view for use on the
    list page.
    """

    def __init__(self, search_string=None, page=1, pagelength=10):

        super().__init__(page=page, pagelength=pagelength)
        account_list = model.AccountList(search_string=search_string,\
            page=page, pagelength=pagelength)
        super().__init__(page=account_list.page,\
            pagelength=account_list.pagelength)
        for account in account_list:
            self.append({"id":account.id, "name":account.name,\
                "role":model.Accounts.ROLE_NAME[account.role],\
                "updated_at":account.updated_at.strftime("%d-%m-%Y %H:%M:%S"),\
                "parent":account.parent_id})
        self.num_records = account_list.num_records
        self.total_pages = self.num_pages()
        
    def num_recs(self):
        
        return self.num_records


class PostmonthListView(PaginatorMixin, list):
    """ This (temporary) view is used to experiment with raw 
    form generation, without wtforms
    """
    
    def __init__(self, postmonths=None, from_month=None, page=1,
                 pagelength=12):

        if postmonths is None:
            postmonths = model.PostmonthList(page=page, pagelength=pagelength,
                                         from_month=from_month)
        for postmonth in postmonths:
            self.append((model.Postmonths.external(postmonth.postmonth),\
                str(postmonth.postmonth), postmonth.monthstat))
        self.pagelength = postmonths.pagelength
        self.page = postmonths.page
        self.total_pages, rem = divmod(postmonths.num_recs(), self.pagelength)
        if rem > 0:
            self.total_pages += 1
