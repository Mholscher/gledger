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
import gledger
import glmodels.glposting as posts
import glmodels.glaccount as accmodel
from datetime import date, datetime
import logging

class testPostCreation(unittest.TestCase) :
    def setUp(self) :
        acc1 = accmodel.Accounts(name = 'verkopen', role = 'I')
        acc1.add()
        acc2 = accmodel.Accounts(name = 'voorraad', role = 'A')
        acc2.add()
        
    def tearDown(self) :
        gledger.db.session.rollback()
        
    def test_insert_journal(self) :
        journ1 = posts.Journals(journalstat = posts.Journals.UNPROCESSED)
        journ1.add()
        q = gledger.db.session.query(posts.Journals)
        self.assertNotEqual(q.count(), 0, 'Journal not inserted') 
        
    def test_post_one_posting(self) :
        post1 = posts.Postings(account_id = accmodel.Accounts.get_by_name("verkopen").id, postmonth = 201608,
                               value_date = datetime.now())
        post1.add()
        q = gledger.db.session.query(posts.Postings)
        self.assertNotEqual(q.count(), 0, 'Posting not inserted')  
        
class testFullJournal(unittest.TestCase) :
    def setUp(self) :
        acc3 = accmodel.Accounts(name = 'verkopen', role = 'I')
        acc3.add()
        acc4 = accmodel.Accounts(name = 'voorraad', role = 'A')
        acc4.add()
        journ2 = posts.Journals(journalstat = posts.Journals.UNPROCESSED)
        journ2.add()
        
    
    def tearDown(self) :
        gledger.db.session.rollback()
                    
if __name__ == '__main__':
    unittest.main()
