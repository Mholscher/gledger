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
    def createView(cls,  id=None, name=None) :
        """ Creates a view for the id (preferred) or
        name passed as an argument. If the account does
        not exist, caller will receive the exception. It is
        not caught...
        """
        
        if (id is None) and (name is None) :
            raise ValueError('An id or name for an account must be given')
        # prefer id to name for fetching an account:
        accountView = cls()
        if (id is not None) :
            accountView.account = model.Accounts.get_by_id(id)
        else :
            accountView.account = model.Accounts.get_by_name(name)
        if accountView.account :
            accountView.parent = accountView.account.parentaccount()
            accountView.children = accountView.account.children
        else :
            accountView.parent = None
            accountView.children = []
        return accountView
        
    def _account_dictionary(self) :
        if (not hasattr(self, 'account')) or (self.account is None) :
            raise(AttributeError, 'Account should exist and be populated')
        # Dispatch on columns in account, default use value 
        return {'id': self.account.id, 'name': self.account.name, 'role' : self.account.role }
    
    def _parent_name_and_id(self) :
        # The check should not be necessary. The contract is: call ONLY if parent exists
        if (not hasattr(self, 'parent')) or (self.parent is None) :
            return None
        return {'id' : self.parent.id, 'name' : self.parent.name}
    
    def _dictionary_from_childlist(self) :
        childlist = []
        for child in self.account.children :
            childlist.append({'id' : child.id, 'name': child.name})
        return childlist
            
    def asDictionary(self) :
        """
        Return the accountview as a dictionary.
        
        This is primarily thought of as a halfway house
        to create the views, be it json or html. 
        """
        asDictionary = {"account" : self._account_dictionary(), "children" : self._dictionary_from_childlist() }
        if self.parent is not None :
            asDictionary["parent"] = self._parent_name_and_id()
        asDictionary["localtitle"] = 'Account ' + self.account.name
        return asDictionary
    

