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
from sqlalchemy.exc import DatabaseError
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
        """A journal can be inserted """
        journ1 = posts.Journals(journalstat = posts.Journals.UNPROCESSED)
        journ1.add()
        q = gledger.db.session.query(posts.Journals)
        self.assertNotEqual(q.count(), 0, 'Journal not inserted') 
        
    def test_post_one_posting(self) :
        """ A posting can be inserted """
        post1 = posts.Postings(account_id = accmodel.Accounts.get_by_name("verkopen").id, 
                               postmonth = 201608, value_date = datetime.now(), amount=250)
        journ3 = posts.Journals(journalstat = posts.Journals.UNPROCESSED)
        journ3.add()
        journ3.journalpostings.append(post1)
        post1.add()
        q = gledger.db.session.query(posts.Postings)
        self.assertNotEqual(q.count(), 0, 'Posting not inserted')  
        
    def test_no_post_wo_journal(self) :
        """Inserting posting w/o journal fails """
        post2 = posts.Postings(account_id = accmodel.Accounts.get_by_name("verkopen").id, 
                               postmonth = 201608, value_date = datetime.now(), amount=250)
        post2.add()
        with self.assertRaises(DatabaseError) :
            gledger.db.session.flush()
        
class testFullJournal(unittest.TestCase) :
    def setUp(self) :
        acc3 = accmodel.Accounts(name = 'verkopen', role = 'I')
        acc3.add()
        acc4 = accmodel.Accounts(name = 'kas', role = 'A')
        acc4.add()
        acc5 = accmodel.Accounts(name = 'btw (ontvangen)', role = 'I')
        acc5.add()
        journ2 = posts.Journals(journalstat = posts.Journals.UNPROCESSED)
        journ2.add()
        gledger.db.session.flush()
        self.journ2id = journ2.id
    
    def tearDown(self) :
        gledger.db.session.rollback()
        
    def test_create_journal(self):
        """ Create a journal with its postings """
        journ2 = posts.Journals.get_by_id(self.journ2id)
        post3 = posts.Postings(account_id = accmodel.Accounts.get_by_name("verkopen").id,  
                               journals_id = journ2.id, postmonth = 201609, 
                               value_date = datetime.now(), amount=250)
        post3.add()
        post4 = posts.Postings(account_id=accmodel.Accounts.get_by_name("kas").id, 
                               journals_id = journ2.id, postmonth = 201609, 
                               value_date = datetime.now(), amount=230)
        post4.add()
        post5 = posts.Postings(account_id = accmodel.Accounts.get_by_name("btw (ontvangen)").id, 
                               journals_id = journ2.id, postmonth = 201609, 
                               value_date = datetime.now(), amount=20)
        post5.add()
        journ2.journalpostings.append(post3)
        journ2.journalpostings.append(post4)
        journ2.journalpostings.append(post5)
        gledger.db.session.flush()
        q = gledger.db.session.query(posts.Postings).join(posts.Journals).\
            filter(posts.Journals.id==journ2.id)
        self.assertEqual(q.count(), 3, "Too little postings in journal")
        
    def test_unbalanced_journal_fails(self):
        """ When a debit and credit amount is not the same,
        the journal must be refused! """
        journ2 = posts.Journals.get_by_id(self.journ2id)
        post6 = posts.Postings(account_id = accmodel.Accounts.get_by_name("verkopen").id,  
                               journals_id = journ2.id, postmonth = 201609, 
                               value_date = datetime.now(), amount=230)
        post6.add()
        post7 = posts.Postings(account_id=accmodel.Accounts.get_by_name("kas").id, 
                               journals_id = journ2.id, postmonth = 201609, 
                               value_date = datetime.now(), amount=230)
        post7.add()
        post8 = posts.Postings(account_id = accmodel.Accounts.get_by_name("btw (ontvangen)").id, 
                               journals_id = journ2.id, postmonth = 201609, 
                               value_date = datetime.now(), amount=20)
        post8.add()
        journ2.journalpostings.append(post6)
        journ2.journalpostings.append(post7)
        journ2.journalpostings.append(post8)
        gledger.db.session.flush()          
        with self.assertRaises(posts.JournalBalanceError) :
            journ2.post_journal()

if __name__ == '__main__':
    unittest.main()
