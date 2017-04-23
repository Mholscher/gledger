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
import json

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
        post1 = posts.Postings(accounts_id = accmodel.Accounts.get_by_name("verkopen").id, 
                               postmonth = 201608, value_date = datetime.now(), 
                               amount=250, debcred='Cr')
        journ3 = posts.Journals(journalstat = posts.Journals.UNPROCESSED)
        journ3.add()
        journ3.journalpostings.append(post1)
        post1.add()
        q = gledger.db.session.query(posts.Postings)
        self.assertNotEqual(q.count(), 0, 'Posting not inserted')  
        
    def test_no_post_wo_journal(self) :
        """Inserting posting w/o journal fails """
        post2 = posts.Postings(accounts_id = accmodel.Accounts.get_by_name("verkopen").id, 
                               postmonth = 201608, value_date = datetime.now(), 
                               amount=250, debcred='Cr')
        post2.add()
        with self.assertRaises(DatabaseError) :
            gledger.db.session.flush()
            
    def test_post_debcred_invalid(self):
        """ Posting with invalid debit/credit indicator must be refused """
        journ4 = posts.Journals(journalstat = posts.Journals.UNPROCESSED)
        journ4.add()
        gledger.db.session.flush()
        with self.assertRaises(posts.InvalidDebitCreditError):
            post3 = posts.Postings(accounts_id = accmodel.Accounts.get_by_name("verkopen").id,  
                                   journals_id = journ4.id, postmonth = 201609, 
                                   value_date = datetime.now(), amount=230, debcred='Ct')
            gledger.db.session.flush()
        
class testFullJournal(unittest.TestCase) :
    def setUp(self) :
        acc3 = accmodel.Accounts(name = 'verkopen', role = 'E')
        acc3.add()
        acc4 = accmodel.Accounts(name = 'kas', role = 'A')
        acc4.add()
        acc5 = accmodel.Accounts(name = 'btw (ontvangen)', role = 'E')
        acc5.add()
        journ2 = posts.Journals(journalstat = posts.Journals.UNPROCESSED)
        journ2.add()
        gledger.db.session.flush()
        self.journ2id = journ2.id
    
    def tearDown(self) :
        self.journ2id = None
        gledger.db.session.rollback()
        
    def test_create_journal(self):
        """ Create a journal with its postings """
        journ2 = posts.Journals.get_by_id(self.journ2id)
        post3 = posts.Postings(accounts_id = accmodel.Accounts.get_by_name("verkopen").id,  
                               journals_id = journ2.id, postmonth = 201609, 
                               value_date = datetime.now(), amount=230, debcred='Cr')
        post3.add()
        post4 = posts.Postings(accounts_id=accmodel.Accounts.get_by_name("kas").id, 
                               journals_id = journ2.id, postmonth = 201609, 
                               value_date = datetime.now(), amount=250, debcred='Db')
        post4.add()
        post5 = posts.Postings(accounts_id = accmodel.Accounts.get_by_name("btw (ontvangen)").id, 
                               journals_id = journ2.id, postmonth = 201609, 
                               value_date = datetime.now(), amount=20, debcred='Cr')
        post5.add()
        gledger.db.session.flush()
        q = gledger.db.session.query(posts.Postings).join(posts.Journals).\
            filter(posts.Journals.id==journ2.id)
        self.assertEqual(q.count(), 3, "Too little postings in journal")
        
    def test_unbalanced_journal_fails(self):
        """ When a debit and credit amount is not the same,
        the journal must be refused! """
        journ2 = posts.Journals.get_by_id(self.journ2id)
        post6 = posts.Postings(accounts_id = accmodel.Accounts.get_by_name("verkopen").id,  
                               journals_id = journ2.id, postmonth = 201609, 
                               value_date = datetime.now(), amount=230, debcred='Cr')
        post6.add()
        post7 = posts.Postings(accounts_id=accmodel.Accounts.get_by_name("kas").id, 
                               journals_id = journ2.id, postmonth = 201609, 
                               value_date = datetime.now(), amount=230, debcred='Db')
        post7.add()
        post8 = posts.Postings(accounts_id = accmodel.Accounts.get_by_name("btw (ontvangen)").id, 
                               journals_id = journ2.id, postmonth = 201609, 
                               value_date = datetime.now(), amount=20, debcred='Cr')
        post8.add()
        gledger.db.session.flush()          
        with self.assertRaises(posts.JournalBalanceError) :
            journ2.post_journal()
            
    def test_post_journal(self):
        """ Post a balancing journal and check balances """
        journ2 = posts.Journals.get_by_id(self.journ2id)
        self.add_postings_to(journ2)
        gledger.db.session.flush
        journ2.post_journal()
        self.assertEqual(accmodel.Accounts.get_by_name("verkopen").current_balance(),
                         -250, 'Account not correctly updated (verkopen)')
        self.assertEqual(accmodel.Accounts.get_by_name("kas").current_balance(),
                         230, 'Account not correctly updated (kas)')
        self.assertEqual(accmodel.Accounts.get_by_name("btw (ontvangen)").current_balance(),
                         20, 'Account not correctly updated (btw)')
        
    def test_a_posted_journal_changes_status(self):
        """ Once a journal is posted, its status should be set to "posted" """
        journ2 = posts.Journals.get_by_id(self.journ2id)
        self.add_postings_to(journ2)
        gledger.db.session.flush
        journ2.post_journal()
        self.assertEqual(journ2.journalstat, 'P', 'Status journal not changed after posting')
        
    def test_decode_json(self):
        """ Test decoding an example json to add to the database 
        
        This requires the external file jrn.json"""
        with open('jrn.json', 'r') as f:
            dictjourn1 = json.load(f)
        self.assertEqual(dictjourn1['journal']['function'], 'insert', 'Function not decoded')
        postings = dictjourn1['journal']['postings']
        self.assertEqual(postings[1]['account'], 'kas', 'Posting does not contain correct account')
        self.assertEqual(postings[1]['amount'], '25000', 'Posting does not contain correct amount')
        
    def test_journal_from_input(self):
        """ Creating a journal from input 
        
        This requires the external file jrn.json"""
        with open('jrn.json', 'r') as f:
            dictjourn1 = json.load(f)
        journ2 = posts.Journals.create_from_dict(dictjourn1)
        q = gledger.db.session.query(posts.Postings).join(posts.Journals).\
            filter(posts.Journals.id==journ2.id)
        self.assertEqual(q.count(), 3, "Too little/many postings in journal")
        
    def test_json_incomplete(self):
        """ An incomplete json leads to failure """
        with self.assertRaises(ValueError):
            with open('jrnerr1.json', 'r') as f:
                dictjourn2 = json.load(f)
                
    def test_json_no_posting(self):
        """ A journal with no postings fails """
        with self.assertRaises(posts.NoPostingInJournal):
            with open('jrnerr2.json', 'r') as f:
                dictjourn3 = json.load(f)
            posts.Journals.create_from_dict(dictjourn3)
                    
    def test_translate_no_account(self):
        """ A posting to a non existing account leads to invalid json error"""
        with self.assertRaises(posts.InvalidJournalError):
            with open('jrnerr3.json', 'r') as f:
                dictjourn4 = json.load(f)
            posts.Journals.create_from_dict(dictjourn4)
        
    def add_postings_to(self, journ2):
        post3 = posts.Postings(accounts_id = accmodel.Accounts.get_by_name("verkopen").id,  
                               journals_id = journ2.id, postmonth = 201609, 
                               value_date = datetime.now(), amount=250, debcred='Cr')
        post3.add()
        post4 = posts.Postings(accounts_id=accmodel.Accounts.get_by_name("kas").id, 
                               journals_id = journ2.id, postmonth = 201609, 
                               value_date = datetime.now(), amount=230, debcred='Db')
        post4.add()
        post5 = posts.Postings(accounts_id = accmodel.Accounts.get_by_name("btw (ontvangen)").id, 
                               journals_id = journ2.id, postmonth = 201609, 
                               value_date = datetime.now(), amount=20, debcred='Db')
        post5.add()
        return journ2

if __name__ == '__main__':
    unittest.main()
