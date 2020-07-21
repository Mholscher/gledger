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

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, PasswordField, SubmitField, SelectField,\
    HiddenField, Form
from wtforms.validators import DataRequired, ValidationError, Length
from glviews.formfields import SelectPostMonthStatusField
from glmodels.glaccount import Accounts, Postmonths

class AccountMustExist(ValueError):
    """WTForms validator for an account that must exist.
    
    The accounts existence is validated against the database.
    """
    
    message='Account must exist'
    
    def __init__(self, message=None):
        if message:
            self.message=message
        
    def __call__(self, form, field):
        
        if (field.data) and (not Accounts.account_exists(requested_name=field.data)):
            raise ValidationError(self.message)

class AccountForm(FlaskForm) :
    """ The form for updating accounts.
    
    All fields of the account can be updated.  
    """

    # Create the list of choices (account roles)
    local_choices = []
    for k, v in Accounts.ROLE_NAME.items():
        item = k, v
        local_choices.append(item)
    name = StringField('Account', validators=[DataRequired()])
    csrf_token = HiddenField('csrf_token')
    parent_name = StringField('Parent', validators = [AccountMustExist()])
    role = SelectField('Type', choices = local_choices)
    update = SubmitField('Update account')
    
class NewAccountForm(AccountForm) :
    """ The form for creating a new account.
    """
    update = SubmitField('Save and list')
    addmore = SubmitField('Save, add more')
    
class AccountBalanceForm(FlaskForm):
    """ This is the form that shows the balance.
    
    It has a form because you can enter the accounting period for which
    you want to see the balance. Default: current.
    """
    
    accounting_period = SelectField('Period')
    change_period = SubmitField('Show selected period')
    
class SearchForm(FlaskForm):
    """ The searchform allows entry of the search terms for an account
    
    The form is quite simple.
    """
    
    search_for = StringField('Search account')
    start_search = SubmitField('Find...')

class JournalSearch(FlaskForm):
    """ This form allows searching for a journal with a search term.

    The form is simple.
    """

    search_for = StringField('Journal (part of key)')
    start_search = SubmitField('Find..')

