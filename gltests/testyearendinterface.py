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

import unittest
from datetime import datetime
from testyearend import create_standard_accountlist_testset
from gledger import db
from glmodels.glyearend import YearEndJournal
import requests

class TestInterface(unittest.TestCase):

    def setUp(self):

        create_standard_accountlist_testset(self)
        db.session.flush()
        self.start_next_year = datetime(2016, 1, 1)

    def tearDown(self):

        db.session.rollback()

    #def test_send_interface(self):
        #""" When out test is running, we can send an interface """

        #jrn1 = YearEndJournal(start_next_year=self.start_next_year)
        #r = requests.post('http://127.0.0.1:5051/journal/new', json=jrn1)
        #self.assertEqual(r.status_code, 200)


if __name__ == '__main__':
    unittest.main()
