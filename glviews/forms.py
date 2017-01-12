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

from flask_wtf import Form
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, ValidationError, Length
from glmodels.glaccount import Accounts

class AccountMustExist(ValueError):
    """WTForms validator for an account that must exist.
    
    The accounts existence is validated against the database.
    """
    def __init__(self, message='Account must exist'):
        if message:
            message='Account must exist'
        self.message=message
        
    def __call__(self, form, field):
        if (field.data) and (not Accounts.account_exists(field.data)):
            raise ValidationError(self.message)

class AccountForm(Form) :
    """ The form for updating accounts.
    
    All fields of the account can be updated. For now the role is
    hardcoded in the form. #TODO Should be refactored to come from the model. """
    name = StringField('Account', validators = [DataRequired()])
    parent = StringField('Parent', validators = [AccountMustExist()])
    role = SelectField('Type', choices = [('A', 'Assets'), ('L', 'Liabilities'), ('I', 'Income'), ('E', 'Expense')])
    update = SubmitField('Update account')
    
class NewAccountForm(AccountForm) :
    """ The form for creating a new account.
    """
    update = SubmitField('Save and list')
    addmore = SubmitField('Save, add more')
    
