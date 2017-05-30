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

class InvalidJsonError(Exception):
    """ This is thrown when a journal does not comply. """
    status_code = 400
    
    def __init__(self, message, status_code=None, payload=None):
        postings.InvalidJournalError.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
        
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@postingapi.errorhandler(InvalidJsonError)
def handle_invalid_json(error):
    """ Create a response for an invalid json journal """
    response_dict = error.to_dict()
    response_dict["status"] = "Not correct"
    response = jsonify(response_dict)
    response.status_code = error.status_code
    return response


def create_success_response(app_message=None):
    """ Build the response for successfuly adding/changing a journal """
    success_response = {"status" : "OK"}
    if not app_message is None :
        success_response['message'] = app_message
    return success_response

@postingapi.route('/journal/new', methods=['POST'])
def addjournal():
    """Receive a new journal from an application.
    
    The journal and its entries are delivered as
    a JSON file. It is decoded and the journal
    and its postings are added to the database. """
    try:
        journal = request.get_json()
        postings.Journals.create_from_dict(journal)
    except postings.InvalidJournalError as e:
        raise InvalidJsonError(str(e))
    return jsonify(create_success_response(app_message='Journal '+ extkey + ' added'))

