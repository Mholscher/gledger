""" This module contains the routes that can be visited using the browser.
Each route has a clear purpose, geared to different uses.

TODO transaction to close the postmonth
"""

import logging
from flask import render_template, flash, request, redirect, url_for, abort
import glmodels.glaccount as accmodel
import glmodels.glposting as journalmodel
from glviews.accountviews import AccountView, AccountListView, BalanceView
from glviews.postingviews import JournalView, PostingView,\
    PostingByAccountView, JournalListView
from glviews.forms import AccountForm, NewAccountForm, SearchForm, JournalSearch
from . import app, db


@app.route('/')
def index():
    """This is the index page of the application. It shows
    a list of accounts
    """
    return redirect(url_for('accountlist'))

@app.route('/accounts/new', methods=['GET', 'POST'])
def createaccount():
    """ This page creates a new account in the system

    The GET method shows the empty form, when filled out and
    submitted, POST will do the validation and update.
    """

    search_form = SearchForm()
    new_account_form = NewAccountForm()
    if new_account_form.validate_on_submit():
        accmodel.Accounts.create_account(name=new_account_form.name.data,
                                         parent_name=new_account_form.parent_name.data,
                                         role=new_account_form.role.data).add()
        db.session.commit()
        flash('Account '+ new_account_form.name.data + ' added')
        if new_account_form.update.data:
            return redirect(url_for('accountlist'))
        if new_account_form.addmore.data:
            return redirect(url_for('createaccount'))
    return render_template('account.html', form=new_account_form,
                           search_form=search_form,
                           accountview=AccountView(), localTitle='New account')

@app.route('/accountlist', methods=['GET'], strict_slashes=False)
def accountlist():
    """accountlist lists accounts from the system.

    The accounts shown may be constrained by a search argument.
    The search argument is checked against the account name and
    the account description. Accounts are shown by change date,
    youngest first.
    """

    search_for = request.args.get('search_for')
    search_form = SearchForm()
    page_nr = request.args.get('page')
    if page_nr is None:
        page_nr = 1
    else:
        page_nr = int(page_nr)

    try:
        account_list = AccountListView(search_string=search_for, page=page_nr)
    except accmodel.ShortSearchStringError as sse:
        flash(str(sse))
        search_form.search_for.data = search_for
        return render_template('accountlist.html', search_form=search_form,
                               accountlist=dict())
    if search_for:
        search_form.search_for.data = search_for
    return render_template('accountlist.html', search_form=search_form,
                           accountlist=account_list)

@app.route('/accounts/<account_name>', methods=['GET', 'POST'], strict_slashes=False)
def accounts(account_name=None):
    """ This is the accounts page of the application

    If an account name is given, it shows the information for that account
    """

    if account_name is None or account_name == '':
        logging.debug('Aborting: account name is missing')
        abort(500)
    search_form = SearchForm()
    logging.debug('Get account from database')
    try:
        account = accmodel.Accounts.get_by_name(account_name)
    except accmodel.NoAccountError as nae:
        abort(404, str(nae))
    logging.debug('Account gelezen: ' + account.name + '(id '+ str(account.id) + ')')
    account_form = AccountForm(obj=account)
    if account.parent_id:
        parent = accmodel.Accounts.get_by_id(account.parent_id)
        account_form.parent_name.data = parent.name
    # logging.debug('request name '+ request.form.name)
    if account_form.validate_on_submit():
        logging.debug('Validated as correct')
        if account_form.role.data:
            new_role = account_form.role.data
        else:
            new_role = None
        if account_form.parent_name.data:
            new_parent = account_form.parent_name.data
        else:
            new_parent = None
        account.update_role_or_parent(new_role=new_role, new_parent=new_parent)
        db.session.commit()
        flash('Account {0} changed'.format(account_name))
        logging.debug('Account {0}  changed'.format(account_name))
        return redirect(url_for('accountlist'))
    for error_key, error_value in account_form.errors.items():
        for message in error_value:
            flash('Field ' + error_key + ': ' + str(message))
    accountview = AccountView.createView(name=account_name).asDictionary()
    return render_template('account.html', accountview=accountview,
                           form=account_form, search_form=search_form,
                           localtitle='Account ' +
                           accountview['account']['name'])

@app.route('/balance/<account_name>/month/<postmonth>', strict_slashes=False)
@app.route('/balance/<account_name>', strict_slashes=False)
def balance(account_name, postmonth=None):
    """ This route shows the balance of an account

    The accountname is the account to show the balance for.
    If no month is given, it shows the current account balance.
    Else it shows the balance for the requested month.
    """

    if account_name is None:
        abort(404, 'An account name is mandatory')
    search_form = SearchForm()
    if postmonth is None:
        for_month = accmodel.postmonth_today()
    else:
        for_month = accmodel.Postmonths.internal(postmonth)
    try:
        balance_view = BalanceView.create_view(name=account_name,
                                               postmonth=for_month)
    except (accmodel.NoAccountError, accmodel.InvalidPostmonthError) as content_error:
        abort(400, str(content_error))
    return render_template('balance.html', balanceview=balance_view.as_dictionary(),
                           search_form=search_form)

@app.route('/posts/<account_name>', strict_slashes=False)
@app.route('/posts/<account_name>/month/<postmonth>', strict_slashes=False)
def posts(account_name, postmonth=None):
    """
    Show postings by account.

    The postings for the account and the month given
    are returned. If no month is requested, it defaults to
    use the current month, but also shows postings of previous
    months.
    """

    search_form = SearchForm()
    try:
        account = accmodel.Accounts.get_by_name(account_name)
    except accmodel.NoAccountError as content_error:
        abort(400, str(content_error))
    try:
        by_account_view = PostingByAccountView(account, month=postmonth).as_dict()
    except accmodel.InvalidPostmonthError as content_error:
        flash(str(content_error))
        by_account_view = None
    return render_template('accountpostings.html', search_form=search_form,
                           posting_list=by_account_view)

@app.route('/journal/<journalkey>', methods=['GET'])
def journal(journalkey):
    """ Show a journal for  browsing.

    The journalkey is the external key of the journal requested
    TODO create a journal search facility here
    """

    search_form = SearchForm()
    if journalkey:
        try:
            journal_view = JournalView(journal_key=journalkey).as_dict()
        except journalmodel.NoJournalError as nje:
            flash(str(nje))
            journal_view = None
    else:
        flash('An existing journal key is required')
        journal_view = None
    return render_template('journalpostings.html', search_form=search_form,
                           journal_view=journal_view)

@app.route('/journallist', methods=['GET'])
def journallist():
    """ Show a list of journal keys, limited by a search search_string
    """

    journal_search = JournalSearch()
    page = request.args.get('page')
    search_string = request.args.get('search_for')
    try:
        if page:
            journal_list =\
                journalmodel.Journals.journals_for_search(search_string=search_string,\
                    page=int(page))
        else:
            journal_list =\
                journalmodel.Journals.journals_for_search(search_string=search_string)
        list_view = JournalListView(journal_list)
    except accmodel.ShortSearchStringError as sse:
        flash(str(sse))
        list_view = JournalListView(journalmodel.JournalList([], page=1,\
            pagelength=25, num_records=0))
    if search_string:
        journal_search.search_for.data = search_string
    return render_template('journallist.html', journallist=list_view,\
        search_form=SearchForm(), journal_search=journal_search)

