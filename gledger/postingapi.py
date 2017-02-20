#    Copyright 2015 Menno Hölscher
#
#    This file is part of gledger.

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

from flask import Blueprint, jsonify, abort, request
import glmodels.glposting as postings

postingapi = Blueprint('api', __name__)

class InvalidJsonError(ValueError):
    """ This is thrown when a journal does not comply. """
    pass

@postingapi.errorhandler(InvalidJsonError)
def json_error(error):
    return jsonify({'status' : 'The data passed was invalid'})
    

@postingapi.route('/journal/new', methods=['POST'])
def addjournal():
    """Receive a new journal from an application.
    
    The journal and its entries are delivered as
    a JSON file. It is decoded and the journal
    and its postings are added to the database. """
    journal = request.get_json()
    return jsonify({'status':'done'})

@postingapi.route('/journal/addto/<journalno>', methods=['POST'])
def addtojournal(journalno):
    """ Receive updates to an existing journal.
    
    The journal entries are delivered as
    a JSON file. It is decoded and the postings
    are added to the journal in the database. """
    return jsonify({'status':'done'})
