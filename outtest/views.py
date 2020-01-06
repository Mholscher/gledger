from . import app
from flask import request

@app.route('/journal/new', methods=['POST'])
def addjournal():
    """Receive a new journal from an application.
    
    The journal and its entries are delivered as
    a JSON file. It is decoded and the journal
    and its postings are added to the database. """
    
    
    journal = request.get_json()
    print(journal)
    return 'OK', 200
