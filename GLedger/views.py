from . import app

@app.route('/')
def index() :
    '''This is the index page of the application. It shows
    a list of accounts '''
    return 'Index pagina'

@app.route('/accounts/new', methods=['GET', 'POST'])
def createaccount() :
    ''' This page creates a new account in the system '''
    return 'Maak een nieuwe rekening'

@app.route('/accounts/<accountName>', methods=['GET', 'POST'], strict_slashes=False)
@app.route('/accounts', methods=['GET'], strict_slashes=False)
def accounts(accountName=None) :
    '''This is the accounts page of the application. It shows
    a list of accounts if no account is given, if an account
    name is given, it shows the information for that account'''    
    if accountName is None :
        return 'Rekeningen lijst'
    return 'Rekening ' + accountName

@app.route('/balance/<accountName>/month/<postmonth>', strict_slashes=False)
@app.route('/balance/<accountName>', strict_slashes=False)
def balance(accountName, postmonth=None) :
    if accountName is None :
        abort(404)
    if postmonth is None :
        postmonth = '04-2015'
    return 'Saldo voor rekening ' + str(accountName) +  ', maand ' + str(postmonth)

@app.route('/posts/<accountName>/month/<postmonth>', strict_slashes= False)
@app.route('/posts/<accountName>', strict_slashes= False)
def posts(accountName, postmonth=None) :
    if postmonth is None :
        postmonth = '04-2015'
    return 'Boekingen voor rekening ' + str(accountName) + ', maand ' + str(postmonth)

@app.route('/journal/new', methods=['GET', 'POST'])
def createJournal() :
    return 'Maak en vul een nieuw journaal ' 

@app.route('/journal/<journalkey>', methods=['GET', 'POST'])
def journal(journalkey) :
    return 'Boekingen in journaal ' + str(journalkey)