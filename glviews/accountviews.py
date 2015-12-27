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
    viewed on the accounts maintenance screen. The way
    the collection is produced is as a dictionary with
    embedded data, for the account itself as strings,
    for the dependents as dictionaries. """
    
    def __init__(self, id=None, name=None) :
        self.id = id
        self.name = name
        if (id is None) and (name is None) :
            raise ValueError('An id or name for an account must be given')
        # prefer id to name for fetching an account:
        if (self.id is not None) :
            self.account = model.Accounts.get_by_id(self.id)
        else :
            self.account = model.Accounts.get_by_name(self.name)
        self.parent = self.account.parentaccount()
        self.children = self.account.children
        
    def _account_dictionary(self) :
        if (not hasattr(self, 'account')) or (self.account is None) :
            raise(AttributeError, 'Account should exist and be populated')
        return dict((col, getattr(self.account, col)) for col in self.account.__table__.columns.keys())
    
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
        """Return the accountview as a dictionary.
        
        This is primarily thought of as a halfway house
        to create the views, be it json or htnl. """
        asDictionary = {"account" : self._account_dictionary(), "children" : self._dictionary_from_childlist() }
        if self.parent is not None :
            asDictionary["parent"] = self._parent_name_and_id()
        asDictionary["localtitle"] = 'Account ' + self.account.name
        return asDictionary
