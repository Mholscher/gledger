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

""" The module contains the interface for journal producers. The batches
with postings are delivered to the /journal/new route. As this is the only
route, it is clear you can not update a journal after delivery.

TODO Create "insert" function to add postings to existing journal
"""

from flask import Blueprint, jsonify, request
import glmodels.glposting as postings
from . import db

postingapi = Blueprint('api', __name__)

class InvalidJsonError(Exception):
    """ This is thrown when a journal does not comply. """
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):

        super().__init__(self, message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):

        return_value = dict(self.payload or ())
        return_value['message'] = self.message
        return return_value

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
    if not app_message is None:
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
        db.session.commit()
    except postings.InvalidJournalError as ije:
        raise InvalidJsonError(str(ije))
    return jsonify(create_success_response(app_message='Journal '+ extkey + ' added'))
