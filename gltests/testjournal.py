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
from datetime import date, datetime
import logging
import json
from sqlalchemy.exc import DatabaseError
import gledger
import glviews.postingviews as postviews
import glmodels.glposting as posts
import glmodels.glaccount as accmodel

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
        
class TestFullJournal(unittest.TestCase) :
    def setUp(self) :
        acc3 = accmodel.Accounts(name = 'verkopen', role = 'E')
        acc3.add()
        acc4 = accmodel.Accounts(name = 'kas', role = 'A')
        acc4.add()
        acc5 = accmodel.Accounts(name = 'btw (ontvangen)', role = 'E')
        acc5.add()
        journ2 = posts.Journals(journalstat = posts.Journals.UNPROCESSED, extkey='PP99')
        journ2.add()
        gledger.db.session.flush()
        self.journ2id = journ2.id
    
    def tearDown(self) :
        self.journ2id = None
        gledger.db.session.rollback()

    def test_get_journal_by_extkey(self):
        """ Get a journal from its extkey """

        journ9 = posts.Journals.get_by_id(self.journ2id)
        journ9 = posts.Journals.get_by_key(journ9.extkey)
        self.assertEqual(journ9.id, self.journ2id, 'Not the same id from read by key') 
        
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
        return posting_to_journal(journ2)
    
class TestListPostings(unittest.TestCase):
    
    def setUp(self):
        
        create_accounts(self)
        journ5 = posts.Journals(journalstat = posts.Journals.UNPROCESSED,\
                                extkey='NR501')
        journ5.add()
        journ6 = posts.Journals(journalstat = posts.Journals.UNPROCESSED,\
                                extkey='NR503')
        journ6.add()
        gledger.db.session.flush()
        self.journ5id = journ5.id
        self.journ5extkey = journ5.extkey
        self.journ6id = journ6.id
        self.journ6extkey = journ6.extkey
        posting_to_journal(journ5)
        post9 = posts.Postings(accounts_id = accmodel.Accounts.get_by_name("verkopen").id,  
                                journals_id = journ6.id, postmonth = 201609, 
                                value_date = datetime.now(), amount=20, debcred='Cr')
        post9.add()
        post10 = posts.Postings(accounts_id = accmodel.Accounts.get_by_name("kas").id,  
                                journals_id = journ6.id, postmonth = 201609, 
                                value_date = datetime.now(), amount=20, debcred='Db')
        post10.add()
        
        
    def tearDown(self):
        
        self.journ5id = None
        gledger.db.session.rollback()
        
    def test_read_journal(self):
        """ We can read the postings just added """
        journal_postings = posts.Journals.postings_for_id(self.journ5id)
        self.assertEqual(len(journal_postings), 3, 'Incorrect no. of postings in journal')
        
    def test_read_non_existing(self):
        """ Reading a non-existing journal returns an error """
        with self.assertRaises(posts.NoJournalError):
            journal_postings = posts.Journals.postings_for_id(1)
        
    def test_read_by_extkey(self):
        """ We can read the postings by external key """
        journal_postings = posts.Journals.postings_for_key(self.journ5extkey)
        self.assertEqual(len(journal_postings), 3, 'Incorrect no. of postings by extkey')
        
    def test_non_existing_extkey(self):
        """ We get an error trying to read postings for false extkey """
        with self.assertRaises(posts.NoJournalError):
            journal_postings = posts.Journals.postings_for_key('V301')
        
    def test_read_by_account(self):
        """ Read postings by account """
        verkopen = accmodel.Accounts.get_by_name("verkopen")
        account_postings = posts.Postings.postings_for_account(verkopen)
        self.assertEqual(len(account_postings), 2, 'Incorrect no. of posts for account')
        
    def test_read_by_account_month(self):
        """ Read postings by account and postmonth """
        post9 = posts.Postings(accounts_id = accmodel.Accounts.get_by_name("verkopen").id,  
                                journals_id = self.journ5id, postmonth = 201608, 
                                value_date = datetime.now(), amount=20, debcred='Cr')
        post9.add()
        gledger.db.session.flush()
        acc10 = accmodel.Accounts.get_by_name("verkopen")
        account_postings = \
            posts.Postings.postings_for_account(acc10, month='09-2016')
        self.assertEqual(len(account_postings), 2, 'Incorrect no. of posts for account')
        
    def test_no_postings_for_account(self):
        """ If an account has no postings, an empty list is returned """
        acc9 = accmodel.Accounts(name = 'inkoop', role = 'A')
        acc9.add()
        gledger.db.session.flush()
        account_postings = posts.Postings.postings_for_account(acc9)
        self.assertEqual(len(account_postings), 0, 'Postings for new account?!')

    def test_list_has_pageinfo(self):
        """ The posting list has page info """

        acc11 = accmodel.Accounts.get_by_name("verkopen")
        account_postings = posts.Postings.postings_for_account(acc11)
        self.assertEqual(account_postings.page, 1, 'Not on page 1 or not available')
        self.assertEqual(account_postings.pagelength, 25, 'Pagelength incorrect')


class TestPostingView(unittest.TestCase):
    
    def setUp(self):
        
        create_accounts(self)
        journ7 = posts.Journals(journalstat = posts.Journals.UNPROCESSED,\
                                extkey='NR723')
        journ7.add()
        posting_to_journal(journ7)
        gledger.db.session.flush()
        self.journ7id = journ7.id
        self.journ7extkey = journ7.extkey

    def tearDown(self):

        gledger.db.session.rollback()

    def test_createview(self):
        """ Create a view for one posting """

        post11 = posts.Postings(accounts_id = accmodel.Accounts.get_by_name("verkopen").id,  
                                journals_id = self.journ7id, postmonth = 201609, 
                                value_date = datetime.now(), amount=120, debcred='Cr')
        post11.add()
        gledger.db.session.flush()
        post11view = postviews.PostingView(post11.id)
        self.assertEqual(post11view.posting.amount, 120, 'Amount in view incorrect')

    def test_posting_no_id_fails(self):
        """ Making a view for a posting with no id fails """

        post12 = posts.Postings(accounts_id = accmodel.Accounts.get_by_name("verkopen").id,  
                                journals_id = self.journ7id, postmonth = 201609, 
                                value_date = datetime.now(), amount=12, debcred='Cr')
        post12.add()
        with self.assertRaises(ValueError):
            post12view = postviews.PostingView(post12.id)

    def test_view_needs_posting(self):
        """ A postingview needs to be supplied with a posting """

        with self.assertRaises(ValueError):
            post13view = postviews.PostingView()

    def test_postingview_as_dict(self):
        """ A postingview can be returned as a dictionary """

        post13 = posts.Postings(accounts_id = accmodel.Accounts.get_by_name("verkopen").id,  
                                journals_id = self.journ7id, postmonth = 201609, 
                                value_date = datetime.now(), amount=6500, debcred='Cr')
        post13.add()
        gledger.db.session.flush()
        post13view = postviews.PostingView(post13.id)
        post13viewdict = post13view.as_dict()
        self.assertIn("id", post13viewdict, 'No id in posting dictionary')
        self.assertEqual(post13viewdict['amount'], '65.00', 'Amount incorrect')
        
    def test_posting_account(self):
        """ A postingview contains the account name """

        post14 = posts.Postings(accounts_id = accmodel.Accounts.get_by_name("kas").id,  
                                journals_id = self.journ7id, postmonth = 201608, 
                                value_date = datetime.now(), amount=5500, debcred='Db')
        post14.add()
        gledger.db.session.flush()
        post14view = postviews.PostingView(post14.id)
        post14viewdict = post14view.as_dict()
        self.assertEqual(post14viewdict['account'], 'kas', 'Wrong account in postview')

    def test_extkey_in_view(self):
        """ The posting should show the journalkey as the external key """

        one_journal7_posting = gledger.db.session.query(posts.Journals).\
            filter_by(id=self.journ7id).first().journalpostings[0]
        post15view = postviews.PostingView(one_journal7_posting.id)
        post15viewdict = post15view.as_dict()
        self.assertEqual(post15viewdict['extkey'], self.journ7extkey, 'Wrong extkey')


class TestJournalView(unittest.TestCase):
    
    def setUp(self):
        create_accounts(self)
        journ8 = posts.Journals(journalstat = posts.Journals.UNPROCESSED,\
                                extkey='Rs837')
        journ8.add()
        posting_to_journal(journ8)
        gledger.db.session.flush()
        self.journ8id = journ8.id
        self.journ8extkey = journ8.extkey

    def tearDown(self):

        gledger.db.session.rollback()

    def test_create_journal_view(self):
        """ We can set up a view which holds the journal """

        journal_view1 = postviews.JournalView(self.journ8id)
        self.assertEqual(journal_view1.journal.id, self.journ8id, 'No view created')

    def test_journal_view_has_postings(self):
        """ The journal view has a list of postings """

        journal_view2 = postviews.JournalView(self.journ8id)
        self.assertEqual(len(journal_view2.postingviews), 3, 'Incorrect number of postings')

    def test_journalview_as_dict(self):
        """ A journalview can return itself as a dictionary """

        journal_view3 = postviews.JournalView(self.journ8id)
        self.assertIn('extkey', journal_view3.as_dict(), 'No extkey in journalview')
        self.assertEqual(journal_view3.as_dict()['extkey'], self.journ8extkey, 'Incorrect extkey')

    def test_journalview_has_postingviews(self):
        """ A journalview contains postingviews for the postings """

        journal_view4 = postviews.JournalView(self.journ8id)
        self.assertEqual(len(journal_view4.as_dict()['postings']), 3, 'Incorrect number of postingviews')
        
class TestViewJournal(unittest.TestCase):

    def setUp(self):

        create_accounts(self)
        self.journ10 = posts.Journals(journalstat = posts.Journals.UNPROCESSED,\
                                extkey='RK7098')
        self.journ10.add()
        posting_to_journal(self.journ10)
        gledger.db.session.flush()
        self.app = gledger.app.test_client()
        self.app.testing = True

    def tearDown(self):
        
        gledger.db.session.rollback()

    def test_lookup_journal(self):
        """ a journal can be retrieved by external key """

        rv = self.app.get('/journal/RK7098')
        self.assertIn(b'RK7098', rv.data, 'Key not in response')

    def test_invalid_key(self):
        """ Request a journal with an invalid key """

        rv = self.app.get('/journal/TT345')
        self.assertIn(b'No journal', rv.data, 'Non-existing key in response')
        self.assertNotIn(b'status', rv.data, 'Journal data returned, must be left out')

    def test_posting_data_in_journal(self):
        """ The data of the postings must be on the journal page """

        rv = self.app.get('/journal/RK7098')
        self.assertIn(b'verkopen', rv.data, '"verkopen" not in response')
        self.assertIn(b'kas', rv.data, '"kas" not in response')
        self.assertIn(b'btw (ontvangen)', rv.data, '"btw" not in response')

class TestAccountPostingViewing(unittest.TestCase):

    def setUp(self):

        create_accounts(self)
        self.journ11 = posts.Journals(journalstat = posts.Journals.UNPROCESSED,\
                                extkey='VC1312')
        self.journ11.add()
        gledger.db.session.flush()
        posting_amount = 0
        for i in range(50):
            posting_amount += 1213
            if i > 16:
                postmonth = 201608
            else:
                postmonth = 201609
            create_posting_to_kas(self, posting_amount, postmonth, self.journ11.id)
        gledger.db.session.flush()
        self.kas_account = accmodel.Accounts.get_by_name('kas')

    def tearDown(self):

        gledger.db.session.rollback()

    def test_can_retrieve_postings(self):
        """ Retrieve the default number of postings -> 25 """

        post_list1 = posts.Postings.postings_for_account(self.kas_account)
        self.assertEqual(len(post_list1), 25, 'Wrong number of postings')

    def test_can_set_pagelength(self):
        """ We can set the pagelength to something diofferent than 25 """

        post_list2 = posts.Postings.postings_for_account(self.kas_account, pagelength=12)
        self.assertEqual(len(post_list2), 12, 'Wrong number of postings')

    def test_page_start_can_differ(self):
        """ We can start at any page """

        post_list3 = posts.Postings.postings_for_account(self.kas_account, page=2, pagelength=4)
        self.assertEqual(post_list3[0].amount, 6065, 'Wrong amount 1st posting page 2')

    def test_limit_postings_by_month(self):
        """ We can limit the postings returned to a month """

        post_list4 = posts.Postings.postings_for_account(self.kas_account, month='09-2016')
        self.assertEqual(len(post_list4), 17, 'Wrong number of postings')


class TestPostingsByAccountView(unittest.TestCase):

    def setUp(self):

        create_accounts(self)
        self.journ12 = posts.Journals(journalstat = posts.Journals.UNPROCESSED,\
                                extkey='DR990')
        self.journ12.add()
        gledger.db.session.flush()
        posting_amount = 0
        for i in range(50):
            posting_amount += 988
            if i > 16:
                postmonth = 201608
            else:
                postmonth = 201609
            create_posting_to_kas(self, posting_amount, postmonth, self.journ12.id)
        gledger.db.session.flush()
        self.kas_account = accmodel.Accounts.get_by_name('kas')
        
    def tearDown(self):

        gledger.db.session.rollback()

    def test_can_create_view(self):
        """ We can create a posting by account view """

        posting_view1 = postviews.PostingByAccountView(self.kas_account)
        self.assertEqual(posting_view1.account, self.kas_account, 'No account in view')

    def test_postings_in_view(self):
        """ Postings are added to a view """

        posting_view2 = postviews.PostingByAccountView(self.kas_account)
        self.assertEqual(len(posting_view2.postings), 25, 'Wrong number of postings')        

    def test_as_dict_has_account_info(self):
        """ The created dictionary from the view holds account info """

        posting_view3 = postviews.PostingByAccountView(self.kas_account)
        self.assertIn('name', posting_view3.as_dict(), 'No account name')

    def test_view_has_posting_info(self):
        """ The view dict contains the info for postings """

        posting_view4 = postviews.PostingByAccountView(self.kas_account)
        self.assertIn('amount', posting_view4.as_dict()['postings'][0], 'No posting info')
        self.assertIn('debcred', posting_view4.as_dict()['postings'][0], 'No debit/credit')
        self.assertIn('postmonth', posting_view4.as_dict()['postings'][0], 'No posting month')

    def test_view_has_page_info(self):
        """ The posting by account view should have page info """

        posting_view5 = postviews.PostingByAccountView(self.kas_account)
        self.assertEqual(posting_view5.page, 1, 'Wrong or no view page')
        self.assertEqual(posting_view5.pagelength, 25, 'Wrong or no view pagelength')
        self.assertEqual(posting_view5.total_pages, 2, 'Wrong or no number of pages')

    def test_view_has_page_2(self):
        """ We can access the second page of postings """
        
        posting_view6 = postviews.PostingByAccountView(self.kas_account, page=2)
        self.assertEqual(posting_view6.page, 2, 'Wrong or no view page')        


class TestViewPostingsAccount(unittest.TestCase):

    def setUp(self):

        create_accounts(self)
        self.journ12 = posts.Journals(journalstat = posts.Journals.UNPROCESSED,\
                                extkey='XV9903')
        self.journ12.add()
        gledger.db.session.flush()
        posting_amount = 0
        for i in range(50):
            posting_amount += 1088
            if i > 16:
                postmonth = 201708
            else:
                postmonth = 201709
            create_posting_to_kas(self, posting_amount, postmonth, self.journ12.id)
        gledger.db.session.flush()
        self.kas_account = accmodel.Accounts.get_by_name('kas')

        self.app = gledger.app.test_client()
        self.app.testing = True

    def tearDown(self):

        gledger.db.session.rollback()

    def test_kas_in_screen(self):
        """ The name of the account must be on screen """
        rv = self.app.get("/posts/kas", follow_redirects=True)
        self.assertIn(b'kas', rv.data, 'Account name not found...')
        self.assertIn('A'.encode('utf-8'), rv.data, 'Role not found')

    def test_amount_in_list(self):
        """ The amounts are in the list """

        rv = self.app.get("/posts/kas?page=2", follow_redirects=True)
        self.assertIn(b'21.76', rv.data, 'No amount in list')
        self.assertIn(b'Db', rv.data, 'No debit/credit in list')

    def test_post_list_per_month(self):
        """ We can select the postings by month """

        rv = self.app.get("/posts/kas/month/09-2017", follow_redirects=True)
        self.assertIn(b'21.76', rv.data, 'Amount for 09-2017 not in list')
        self.assertNotIn(b'195.84', rv.data, 'Amount for 08-2017 in list')


class TestJournalSearchList(unittest.TestCase):

    def setUp(self):

        create_accounts(self)
        self.journ13 = posts.Journals(journalstat = posts.Journals.UNPROCESSED,\
                                extkey='DD956')
        self.journ13.add()
        gledger.db.session.flush()
        posting_to_journal(self.journ13)
        self.journ14 = posts.Journals(journalstat = posts.Journals.UNPROCESSED,\
                                extkey='XD952')
        self.journ14.add()
        gledger.db.session.flush()
        posting_to_journal(self.journ14)
        gledger.db.session.flush()

    def tearDown(self):

        gledger.db.session.rollback()

    def test_can_search_list(self):
        """ We can create a search list for journals """

        search_list = posts.Journals.journals_for_search(search_string='DD9')
        self.assertEqual(len(search_list), 1, 'Wrong number of journals found')

    def test_refuse_short_search_string(self):
        """ A short search string for journals throws an error """

        with self.assertRaises(ValueError):
            search_list = posts.Journals.journals_for_search(search_string='X')
        with self.assertRaises(ValueError):
            search_list = posts.Journals.journals_for_search(search_string='XD')


class TestJournalSearchPaging(unittest.TestCase):

    def setUp(self):

        for i in range(250, 304):
            journal = posts.Journals(journalstat=posts.Journals.UNPROCESSED,\
                            extkey='MLD'+str(i), updated_at=datetime.now())
            journal.add()
        gledger.db.session.flush()

    def tearDown(self):

        gledger.db.session.rollback()

    def test_page_has_25(self):
        """ A page should have 25 journal keys """

        search_list = posts.Journals.journals_for_search(search_string='MLD')
        self.assertEqual(len(search_list), 25, 'Incorrect number of keys on page')

    def test_can_get_page_3(self):
        """ We can get the third page with journals """

        search_list = posts.Journals.journals_for_search(search_string='MLD', page=3)
        self.assertEqual(len(search_list), 4, 'Wrong (' +str(len(search_list))+ ') number of records')

    def test_page_with_subset(self):
        """ We can get a subset correctly """

        search_list = posts.Journals.journals_for_search(search_string='MLD27')
        self.assertEqual(len(search_list), 10, 'Incorrect number of keys on page')

    def test_can_see_no_of_pages(self):
        """ We know how many lines are available """

        search_list = posts.Journals.journals_for_search(search_string='MLD')
        self.assertEqual( search_list.num_records, 54, 'Number of records not equal attibute')

class TestJournalListView(unittest.TestCase):

    def setUp(self):

        for i in range(120, 205):
            journal = posts.Journals(journalstat=posts.Journals.UNPROCESSED,\
                            extkey='TLV'+str(i), updated_at=datetime.now())
            journal.add()
        gledger.db.session.flush()
        self.search_list = posts.Journals.journals_for_search(search_string='TLV')

    def tearDown(self):

        gledger.db.session.rollback()

    def test_can_make_view(self):
        """ We can create a view from a search list """

        list_view1 = postviews.JournalListView(self.search_list)
        self.assertEqual(len(list_view1), 25, 'Wrong number of journals in list view')

    def test_can_create_view_for_second_page(self):
        """ We can create a view for the second page """

        search_list = posts.Journals.journals_for_search(search_string='TLV', page=2)
        list_view2 = postviews.JournalListView(search_list)
        self.assertIn('extkey', list_view2[12], 'extkey missing')

    def test_last_page_correct_no(self):
        """ The last page should have the correct no of records """

        search_list = posts.Journals.journals_for_search(search_string='TLV', page=4)
        list_view3 = postviews.JournalListView(search_list)        
        self.assertEqual(len(list_view3), 10, 'Wrong no of journals on last page')

    def test_view_for_page_info(self):
        """ The view has page info """

        list_view4 = postviews.JournalListView(self.search_list)
        self.assertEqual(list_view4.page, 1, 'Wrong or no page number in view')
        self.assertEqual(list_view4.pagelength, 25, 'Wrong or no page length in view')
        self.assertEqual(list_view4.total_pages, 4, 'Wrong or no no of pages in view')


class TestJournalListFunctions(unittest.TestCase):

    def setUp(self):

        for i in range(301, 364):
            journal = posts.Journals(journalstat=posts.Journals.UNPROCESSED,\
                            extkey='BRH'+str(i), updated_at=datetime.now())
            journal.add()
        gledger.db.session.flush()

        self.app = gledger.app.test_client()
        self.app.testing = True

    def tearDown(self):

        gledger.db.session.rollback()

    def test_select_list_of_journals(self):
        """ We can select a small list of journals """

        rv = self.app.get('/journallist?search_for=RH31')
        self.assertIn(b'BRH311', rv.data, 'Journal not in selection')

    def test_empty_search_empty_list(self):
        """ An empty search_string returns an empty list """

        rv = self.app.get('/journallist')
        self.assertNotIn(b'BRH3', rv.data, 'Journals in empty list?')

    def test_short_search_flashes_message(self):
        """ Entering a short search string flashes a message """

        rv = self.app.get('/journallist?search_for=RH')
        self.assertIn(b'Search string', rv.data, 'No or incorrect flashed message')

    def test_extkey_is_link(self):
        """ The extkey is a link to the journal """

        rv = self.app.get('/journallist?search_for=RH31')
        self.assertIn(b'href=/journal/BRH311', rv.data, 'Journal key not a link')

    def test_can_go_first_page(self):
        """ We see a link to the first page """

        rv = self.app.get('/journallist?search_for=BRH&page=2')
        self.assertIn(b'page=1', rv.data, 'No link to first page')

    def test_can_go_prev_page(self):
        """ We can go to the previous page """

        rv = self.app.get('/journallist?search_for=BRH&page=2')
        self.assertIn(b'\xe2\x8f\xb4', rv.data, 'No link to previous page')


        
def create_posting_to_kas(instance, posting_amount, postmonth, journal_id):
    """ Post an amount to kas for test purposes """

    postn = posts.Postings(accounts_id=accmodel.Accounts.get_by_name("kas").id, 
                            journals_id = journal_id, postmonth = postmonth, 
                            value_date = datetime.now(), amount=posting_amount, 
                            debcred='Db')
    postn.add()    
    
def create_accounts(instance):

    instance.acc6 = accmodel.Accounts(name = 'verkopen', role = 'E')
    instance.acc6.add()
    instance.acc7 = accmodel.Accounts(name = 'kas', role = 'A')
    instance.acc7.add()
    instance.acc8 = accmodel.Accounts(name = 'btw (ontvangen)', role = 'E')
    instance.acc8.add()


def posting_to_journal(journ2):
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
