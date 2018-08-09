from . import app, db
import glmodels.glaccount as accmodel
from flask import render_template, flash, request, redirect, url_for, abort
from glviews.accountviews import AccountView, AccountListView, BalanceView
from glviews.forms import AccountForm, NewAccountForm
import logging


@app.route('/')
def index():
    """This is the index page of the application. It shows
    a list of accounts
    """
    return redirect(url_for('accountList'))

@app.route('/accounts/new', methods=['GET', 'POST'])
def createaccount():
    """ This page creates a new account in the system
    
    The GET method shows the empty form, when filled out and
    submitted, POST will do the validation and update.
    """
    
    newAccountForm = NewAccountForm()
    if newAccountForm.validate_on_submit():
        accmodel.Accounts.create_account(name=newAccountForm.name.data,
                          parent_name=newAccountForm.parent.data,
                          role=newAccountForm.role.data).add()
        db.session.commit()
        flash('Account '+ newAccountForm.name.data + ' added')
        if newAccountForm.update.data:
            return redirect(url_for('accountList'))
        if newAccountForm.addmore.data:
            return redirect(url_for('createaccount'))
    return render_template('account.html',form=newAccountForm,
                           accountview=AccountView(), localTitle='New account')

@app.route('/accountlist/<searchfor>', methods=['GET'], strict_slashes=False)
@app.route('/accountlist', methods=['GET'], strict_slashes=False)
def accountList(searchfor=None):
    """accountList lists accounts from the system.
    
    The accounts shown may be constrained by a search argument.
    The search argument is checked against the account name and
    the account description.
    """
    
    try:
        account_list = accmodel.AccountList(search_string=searchfor)
    except accmodel.ShortSearchStringError as e:
        abort(400, str(e))
    return render_template('accountlist.html', 
                           accountlist=AccountListView(account_list))

@app.route('/accounts/<accountName>', methods=['GET', 'POST'], strict_slashes=False)
def accounts(accountName=None):
    """ This is the accounts page of the application
    
    If an account name is given, it shows the information for that account
    """    
    if accountName is None or accountName == '':
        logging.debug('Aborting: account name is missing')
        abort(500)
    logging.debug('Get account from database')
    try:
        account = accmodel.Accounts.get_by_name(accountName)
    except accmodel.NoAccountError as e:
        abort(404, str(e))
    logging.debug('Account gelezen: ' + account.name + '(id '+ str(account.id) + ')')
    accountForm = AccountForm(obj=account)
    # logging.debug('request name '+ request.form.name)
    if accountForm.validate_on_submit():  #TODO validation of existence for parent
        logging.debug('Validated as correct')
        if accountForm.role.data:
            new_role = accountForm.role.data
        else:
            new_role = None
        if accountForm.parent.data:
            new_parent = accountForm.parent.data
        else:
            new_parent = None
        account.update_role_or_parent(new_role=new_role, new_parent=new_parent)
        db.session.commit()
        flash('Account '+ accountName + ' changed')
        logging.debug('Account '+ accountName + ' changed')
        return redirect(url_for('accountList'))
    if len(accountForm.errors):
        for k, v in accountForm.errors.items():
            for message in v:
                flash('Field ' + k + ': ' + str(message))
    accountview = AccountView.createView(name=accountName).asDictionary()
    return render_template('account.html', accountview=accountview,
                           form=accountForm,
                           localtitle='Account ' +
                           accountview['account']['name'])

@app.route('/balance/<accountName>/month/<postmonth>', strict_slashes=False)
@app.route('/balance/<accountName>', strict_slashes=False)
def balance(accountName, postmonth=None):
    """ This route shows the balance of an account
    
    The accountname is the account to show the balance for.
    If no month is given, it shows the current account balance.
    Else it shows the balance for the requested month.
    """
    
    if accountName is None:
        abort(404, 'An account name is mandatory')
    if postmonth is None:
        for_month = accmodel.postmonth_today()
    else:
        for_month = accmodel.Postmonths.internal(postmonth)
    try:
        balance_view = BalanceView.create_view(name=accountName, 
                                               postmonth=for_month)
    except accmodel.NoAccountError as e:
        abort(400, str(e))
    return render_template('balance.html', balanceview=balance_view.as_dictionary()) 

@app.route('/posts/<accountName>/month/<postmonth>', strict_slashes=False)
@app.route('/posts/<accountName>', strict_slashes=False)
def posts(accountName, postmonth=None):
    """ 
    Show postings by account.
    
    The postings for the account and the month given
    are returned. If no month is requested, it defaults to
    use the current month.
    """
    if postmonth is None:
        for_month = accmodel.postmonth_today()
    else:
        for_month = accmodel.Postmonths.internal(postmonth)
    return 'Boekingen voor rekening ' + str(accountName) + ', maand ' + str(for_month)

@app.route('/journal/<journalkey>', methods=['GET'])
def journal(journalkey):
    """ Show a journal for  browsing.
    
    The journalkey is the number of the journal requested
    """
    return 'Boekingen in journaal ' + str(journalkey)
