from . import app, db
import glmodels.glaccount as accmodel
from flask import render_template, flash, request, redirect, url_for
from glviews.accountviews import AccountView
from glviews.forms import AccountForm
import logging

@app.route('/')
def index() :
    """This is the index page of the application. It shows
    a list of accounts """
    return 'De index pagina'

@app.route('/accounts/new', methods=['GET', 'POST'])
def createaccount() :
    """ This page creates a new account in the system """
    return 'Maak een nieuwe rekening'

@app.route('/accounts', methods=['GET'], strict_slashes=False)
def accountList() :
    """accountList lists accounts from the system.
    
    The accounts shown may be constrained by a search argument.
    The search argument is checked against the account name and
    the account descritpion.
    """
    return 'Toon een lijst met rekeningen'

@app.route('/accounts/<accountName>', methods=['GET', 'POST'], strict_slashes=False)
def accounts(accountName=None) :
    """This is the accounts page of the application
    
    If an account name is given, it shows the information for that account
    """    
    if accountName is None :
        logging.debug('Aborting: account name is None')
        abort(500)
    logging.debug('Get account from database')
    account = accmodel.Accounts.get_by_name(accountName)
    logging.debug('Account gelezen: ' + account.name + '(id '+ str(account.id) + ')')
    accountForm = AccountForm(formdata = request.form, obj = account)
    logging.debug('accountForm name '+ accountForm.name.data)
    if accountForm.validate_on_submit() :
        logging.debug('Validated as correct')
        account.role = accountForm.role.data
        if accountForm.parent.data :
            parent = accmodel.Accounts.get_by_name(accountForm.parent.data)
            account.parent = parent.id
        else :
            parent = None
        account.add()
        logging.debug('Added account ' + account.name + ' to session')
        db.session.commit()
        flash('Account '+ accountName + ' changed')
        logging.debug('Account '+ accountName + ' changed')
        return redirect(url_for('accountList'))
    accountview = AccountView(name=accountName).asDictionary()
    return render_template('account.html', accountview=accountview, form = accountForm)

@app.route('/balance/<accountName>/month/<postmonth>', strict_slashes=False)
@app.route('/balance/<accountName>', strict_slashes=False)
def balance(accountName, postmonth=None) :
    """This route shows the balance of an account
    
    The accountname is the account to show the balance for.
    If no month is given, it shows the current account balance.
    Else it shows the balance for the requested month.
    """
    if accountName is None :
        abort(404)
    if postmonth is None :
        postmonth = '04-2015'
    return 'Saldo voor rekening ' + str(accountName) +  ', maand ' + str(postmonth)

@app.route('/posts/<accountName>/month/<postmonth>', strict_slashes= False)
@app.route('/posts/<accountName>', strict_slashes= False)
def posts(accountName, postmonth=None) :
    """ Show postings by account.
    
    The postings for the account and the month given
    are returned. If no month is requested, it defaults to
    use the current month.
    """
    if postmonth is None :
        postmonth = '04-2015'
    return 'Boekingen voor rekening ' + str(accountName) + ', maand ' + str(postmonth)

@app.route('/journal/new', methods=['GET', 'POST'])
def createJournal() :
    """ Create a new journal. 
    
    On post it returns the next page or processes the postings
    that were entered by the user. Get returns a fresh journal,
    showing a journal with no postings.
    """
    return 'Maak en vul een nieuw journaal ' 

@app.route('/journal/<journalkey>', methods=['GET', 'POST'])
def journal(journalkey) :
    """ Show a journal for update or browsing.
    
    The journalkey is the number of the journal requested
    On POST the journal is processed if it is unprocessed.
    """
    return 'Boekingen in journaal ' + str(journalkey)