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
import glviews.accountviews as accviews
import glmodels.glaccount as accmodel
from sqlalchemy.exc import DatabaseError
from sqlalchemy.orm.exc import NoResultFound
from datetime import date,datetime
import logging

class TestDBCreation(unittest.TestCase) :

    def setUp(self) :
        pass
    
    def tearDown(self) :
        gledger.db.session.rollback() 
    
    def test_insert(self) :
        """ We can insert an account"""
        acc1 = accmodel.Accounts(name = 'proefbalans', role = 'I')
        acc1.add()
        q = gledger.db.session.query(accmodel.Accounts).filter(accmodel.Accounts.name == 'proefbalans')
        self.assertNotEqual(q.count(), 0, 'No account updated')
    
    def test_insert_duplicate(self) :
        """ We cannot insert an account twice """
        acc1 = accmodel.Accounts(name = 'proefbalans', role = 'I')
        acc1.add()
        acc2 = accmodel.Accounts(name = 'proefbalans', role = 'I')
        acc2.add()
        with self.assertRaises(DatabaseError) :       
            gledger.db.session.flush()
            
    def test_accounts_related(self) :
        """ We can insert related accounts (parent child)
        """
        
        acc4 =  accmodel.Accounts(name = 'parent', role = 'I')
        acc4.add()
        acc5 =  accmodel.Accounts(name = 'child', role = 'I')
        acc5.add()
        acc4.children.append(acc5)
        self.assertIn(acc5, acc4.children)
        gledger.db.session.flush()
        self.assertEqual(acc5.parent_id, acc4.id)
        
    def test_insert_with_parent(self) :
        """We insert an account with a parent """
        acc28 = accmodel.Accounts.create_account(name='parent2', role='I')
        acc28.add()
        acc29 = accmodel.Accounts.create_account(name='child2', role='I', parent_name='parent2')
        acc29.add()
        gledger.db.session.flush()
        acc30 =  accmodel.Accounts.create_account(name='child3', role='I', parent_id=acc28.id)
        self.assertIn(acc29, acc28.children, 'parent not added by name')
        self.assertIn(acc30, acc28.children, 'parent not added by id')

    def test_check_account_existence(self) :
        """ We check an account exists """
        acc27 = accmodel.Accounts(name = 'checkfor', role = 'I')
        acc27.add()
        self.assertTrue(accmodel.Accounts.account_exists(requested_name = 'checkfor'))
        self.assertFalse(accmodel.Accounts.account_exists(requested_name = 'anyname'))
        
    def test_inv_accountid(self):
        """ If an invalid id is passed, an appropriate exception is thrown """
        with self.assertRaises(accmodel.NoAccountError):
            acc31 = accmodel.Accounts.get_by_id(1)
        
    def test_inv_accountname(self):
        """ If an invalid name is passed, an appropriate  exception is thrown """
        with self.assertRaises(accmodel.NoAccountError):
            acc32 = accmodel.Accounts.get_by_name('anyname')
        
    def test_can_add_balance(self) :
        """We can add a balance to an account """
        try :
            acc6 = accmodel.Accounts.get_by_name('creditors')
        except  accmodel.NoAccountError :
            acc6 = accmodel.Accounts(name='creditors', role='L')
            acc6.add()
        bal1 = accmodel.Balances(postmonth=accmodel.postmonth_for(date.today()), amount=1215, value_date='2015-07-21')
        acc6.balances.append(bal1)
        bal1.add()
        gledger.db.session.flush()
        self.assertEqual(bal1.account_id, acc6.id, 
                         'Balance not attached to account')
        
                    
class TestDomainProcesses(unittest.TestCase) :
    
    def tearDown(self) :
        gledger.db.session.rollback() 

    def test_refuse_accttype(self) :
        """ We refuse an invalid account type """        
        with self.assertRaises(ValueError) :       
            acc3 = accmodel.Accounts(name = 'rekening', role = 'C')  
            
    def test_refuse_future_postmonth(self) :
        """ A balance cannot be created for a future postmonth """
        current_postmonth  = accmodel.postmonth_today()
        with self.assertRaises(ValueError) :
            bal2 = accmodel.Balances(postmonth=current_postmonth + 2, 
                                     amount=1215, value_date='2015-07-21')
            
    def test_convert_date_to_postmonth(self) :
        """ If we get the correct postmonth from a date """
        postdate = date(2015, 1, 26)
        self.assertEqual(201501, accmodel.postmonth_for(postdate), 
                         'Incorrect postmonth from date')
        
    def test_change_account(self) :
        """ Changing account data. """
        acc27 = accmodel.Accounts(role='L', name='creditparent')
        acc27.add()
        gledger.db.session.flush()
        acc7 = accmodel.Accounts(role='L', name='creditors')
        acc7.add()
        gledger.db.session.flush()
        acc8 = accmodel.Accounts.get_by_name('creditors')
        acc8.role = 'A'
        gledger.db.session.flush()
        acc8 = gledger.db.session.query(accmodel.Accounts).filter(accmodel.Accounts.name == 'creditors').one()
        self.assertEqual('A', acc8.role, 'Role not updated after flush')
        acc8.update_role_or_parent(new_parent=acc27.name)
        self.assertEqual(acc27.id, acc8.parent_id, 'Failed to set parent')
        
    def test_account_by_id(self) :
        """Getting an account by its sequence """
        acc9 = accmodel.Accounts(role='E', name='salaris')
        acc9.add()
        gledger.db.session.flush()
        accn = gledger.db.session.query(accmodel.Accounts).filter(accmodel.Accounts.name=='salaris').one()
        acci = accmodel.Accounts.get_by_id(accn.id)
        self.assertEqual(accn.id, acci.id, 'id unequal after read') 

    def test_account_by_name(self) :
        """Getting an account by its name """
        acc10 = accmodel.Accounts(role='E', name='bonus')
        acc10.add()
        gledger.db.session.flush()
        accn = gledger.db.session.query(accmodel.Accounts).filter(accmodel.Accounts.name=='bonus').one()
        acci = accmodel.Accounts.get_by_name(accn.name)
        self.assertEqual(accn.name, acci.name, 'name unequal after read') 
        
    def test_current_balance(self) :
        acc11 =  accmodel.Accounts(role='L', name='bankloans')
        acc11.add()
        bal3 = accmodel.Balances(postmonth=accmodel.postmonth_for(date.today()), amount=12.17, value_date='2015-07-21')
        acc11.balances.append(bal3)
        self.assertEqual(acc11.current_balance(), 12.17, 'Balance not correctly read back')
        
    def test_history_balance(self) :
        acc12 =  accmodel.Accounts(role='E', name='officestuff')
        acc12.add()
        add_postmonths([201504, 201506, 201507])
        bal4 = accmodel.Balances(postmonth=201506, amount=1712, value_date='2015-06-29')
        acc12.balances.append(bal4)
        bal5 = accmodel.Balances(postmonth=201504, amount=1718, value_date='2015-04-30')
        acc12.balances.append(bal5)
        bal6 = accmodel.Balances(postmonth=201507, amount=1726, value_date='2015-07-10')
        acc12.balances.append(bal6)
        acc13 =  accmodel.Accounts(role='E', name='purchases')
        acc13.add()
        bal7 = accmodel.Balances(postmonth=201506, amount=1712, value_date='2015-06-29')
        acc13.balances.append(bal7)
        self.assertEqual(acc12.balance_ultimo(201507), 1726, 'Balance july not correct')
        self.assertEqual(acc12.balance_ultimo(201506), 1712, 'Balance june not correct')
        self.assertEqual(acc12.balance_ultimo(201505), 1718, 'Balance may not correct')       
        self.assertEqual(acc12.balance_ultimo(201502), 0, 'Balance february not correct') 
        
    def test_branch_balance(self) :
        add_postmonths([201504, 201507, 201508])
        acc19 = accmodel.Accounts(role='E', name='officeutils')
        acc19.add()
        acc20 = accmodel.Accounts(role='E', name='nietjes')
        acc20.add()
        acc19.children.append(acc20)
        acc21 = accmodel.Accounts(role='E', name='schrijfblokken')
        acc21.add()
        acc19.children.append(acc21)
        acc22 = accmodel.Accounts(role='E', name='A4blokken')
        acc22.add()
        acc21.children.append(acc22)
        bal8 = accmodel.Balances(postmonth=201507, amount=1726, value_date='2015-07-10')
        acc19.balances.append(bal8)
        bal9 = accmodel.Balances(postmonth=201508, amount=1814, value_date='2015-08-10')
        acc22.balances.append(bal9)
        bal10 = accmodel.Balances(postmonth=201507, amount=740, value_date='2015-07-01')
        acc22.balances.append(bal10)
        gledger.db.session.flush()
        self.assertEqual(acc19.balance_ultimo(201506, 0), 0, 'Balance before 1st record not zero')
        self.assertEqual(acc22.balance_ultimo(201507, 0), 740, 'BalanceA4blokken not found')
        self.assertEqual(acc19.balance_ultimo(201507, 0), 2466, 'Balance officeutils 201507 not found')        
        self.assertEqual(acc19.balance_ultimo(201508, 0), 3540, 'Balance officeutils 201508 not found')
        
    def test_debit_credit_for_account(self):
        """ Return debit credit indicator for account"""
        acc33 = accmodel.Accounts(role='A', name='an Asset account')
        acc33.add()
        acc34 = accmodel.Accounts(role='L', name='a Liability account')
        acc34.add()
        acc35 = accmodel.Accounts(role='I', name='an Income account')
        acc35.add()
        acc36 = accmodel.Accounts(role='E', name='an Expense account')
        acc36.add()
        self.assertEqual(acc33.debit_credit(), 'Db', acc33.name + ' should be debit')
        self.assertEqual(acc34.debit_credit(), 'Cr', acc34.name + ' should be credit')
        self.assertEqual(acc35.debit_credit(), 'Cr', acc35.name + ' should be credit')
        self.assertEqual(acc36.debit_credit(), 'Db', acc36.name + ' should be debit')
        
    def test_is_debit_credit(self):
        """ Return from functions for debit/credit account """
        acc37 = accmodel.Accounts(role='A', name='an Asset account')
        acc37.add()
        acc38 = accmodel.Accounts(role='L', name='a Liability account')
        acc38.add()
        self.assertEqual(acc37.is_debit(), True, acc37.name + 'is not a debit account')
        self.assertEqual(acc37.is_credit(), False, acc37.name + 'is a credit account')
        self.assertEqual(acc38.is_debit(), False, acc38.name + 'is a debit account')
        self.assertEqual(acc38.is_credit(), True, acc38.name + 'is not a credit account')
        
    def test_post_to_balance(self):
        """ Post an amount to the proper balance record."""
        acc39 = accmodel.Accounts(role='I', name='Verkopen')
        acc39.add()
        self.assertEqual(acc39.current_balance(), 0, 'Account does not open with zero balance?')
        acc39.post_amount('Db', 12.50, datetime.today())
        self.assertEqual(acc39.current_balance(), -12.50, 'Account balance not correct')

class TestAccountStructures(unittest.TestCase) :
    
    def setUp(self) :
        self.parent = accmodel.Accounts(role='I', name='topaccount')
        self.parent.add()
        self.ch1 = accmodel.Accounts(role='I', name='child1')
        self.ch1.add()
        self.parent.children.append(self.ch1)
        self.ch2 = accmodel.Accounts(role='I', name='child2')
        self.ch2.add()
        self.parent.children.append(self.ch2)
        self.ch3 = accmodel.Accounts(role='I', name='child3')
        self.ch3.add()
        self.parent.children.append(self.ch3)
        gledger.db.session.flush()

    def tearDown(self) :
        gledger.db.session.rollback() 
        
    def test_return_childlist(self) :
        """Returning a list of children"""
        self.assertEqual(len(self.parent.children), 3, 'Exactly 3 children should be in list')
        
    def test_get_parent(self) :
        self.assertEqual(self.ch1.parentaccount().name, self.parent.name, 'Parentaccount returned should be the parent')
        
class TestPostmonthActions(unittest.TestCase):
    
    def tearDown(self):
        gledger.db.session.rollback()
        
    def test_insert_postmonth(self) :
        """ We can create a postmonth """
        pm1 = accmodel.Postmonths(postmonth=201507, monthstat = 'a')
        pm1.add()
        gledger.db.session.flush()
        self.assertEqual(pm1.postmonth, 201507, 'Postmonth set incorrect')
        
    def test_invalid_monthstat(self) :
        """ We cannot create a postmonth with invalid status """
        with self.assertRaises(ValueError) :
            pm2 = accmodel.Postmonths(postmonth=201507, monthstat = 'z')

    def test_postmonth_no_state(self) :
        """ We can create a postmonth """
        pm3 = accmodel.Postmonths(postmonth=201507)
        pm3.add()
        with self.assertRaises(DatabaseError) :
            gledger.db.session.flush()    
            
    def test_convert_ext_to_postmonth(self):
        """ We can convert an postmonth from string to internal """
        
        month_for = accmodel.Postmonths.internal('01-2018')
        self.assertEqual(month_for, 201801, 'Post month not converted correctly')
        
    def test_invalid_month_format(self):
        """ An invalid postmonth format is refused """
        
        with self.assertRaises(accmodel.InvalidPostmonthError):
            month_for = accmodel.Postmonths.internal('022017')

    def test_month_wrong_length(self):
        """ A postmonth is to short or to long """
        
        with self.assertRaises(accmodel.InvalidPostmonthError):
            month_for = accmodel.Postmonths.internal('02-201')
        with self.assertRaises(accmodel.InvalidPostmonthError):
            month_for = accmodel.Postmonths.internal('012-2018')

        
class TestAccountviews(unittest.TestCase) :
    
    def tearDown(self) :
        gledger.db.session.rollback() 
    
    def test_accountview_load_fail(self) :
        """ Trying to load an accountview for a non-existent account
            should return an error """
        with self.assertRaises(accmodel.NoAccountError) :       
            accountsView = accviews.AccountView.createView(id=1)
            
    def test_accountview_load(self) :
        """ creating an accountsview for an account should retain fields """
        acc13 = accmodel.Accounts(name = 'proefbalans', role = 'I')
        acc13.add()
        gledger.db.session.flush()
        accountsView1 = accviews.AccountView.createView(id=acc13.id)
        self.assertEqual(accountsView1.account.name, acc13.name, 'Accountsview for wrong account')
        self.assertEqual(accountsView1.account.role, acc13.role, 'Accountsview did not retain field')
    
    def test_accountview_as_dict(self) :
        """ You can return an accountview as a nested dictionary """
        
        acc14 = accmodel.Accounts(name = 'voorziening251', role = 'A')
        acc14.add()
        gledger.db.session.flush()
        accountsView2 = accviews.AccountView.createView(id=acc14.id)
        asDictionary = accountsView2.asDictionary()
        self.assertEqual(accountsView2.asDictionary()["account"]["name"], acc14.name, 'Name should be key in accountsview')
        
    def test_accountview_has_parent(self) :
        """ The accountview contains the parent account """
        acc15 = accmodel.Accounts(name = 'parent', role = 'I')
        acc15.add()
        acc16 =  accmodel.Accounts(name = 'this', role = 'I')
        acc16.add()
        gledger.db.session.flush()
        acc16.parent_id = acc15.id
        gledger.db.session.flush()
        accountsView3 = accviews.AccountView.createView(name = acc16.name)
        self.assertEqual(accountsView3.asDictionary()["parent"]["name"],acc15. name, 'Parent not set properly in Accountsview') 
    
    def test_accountview_null_parent(self) :
        """ An account with a null parent can be in an accountview """
        acc17 = accmodel.Accounts(name = 'parent', role = 'I')
        acc17.add()
        acc18 =  accmodel.Accounts(name = 'this', role = 'I')
        acc18.add()
        gledger.db.session.flush()
        acc18.parent_id = acc17.id
        gledger.db.session.flush()
        accountsView4 = accviews.AccountView.createView(name = acc17.name)
        self.assertEqual(accountsView4.parent, None, 'An accountview of an account with no parent should have None as parent')
        asDictionary = accountsView4.asDictionary()
        self.assertTrue("parent_id" not in asDictionary)
        
    def test_accountview_children(self) :
        """ The children of an account appear correctly in the view """
        self.parent = accmodel.Accounts(role='I', name='topaccount')
        self.parent.add()
        self.ch1 = accmodel.Accounts(role='I', name='child1')
        self.ch1.add()
        self.parent.children.append(self.ch1)
        self.ch2 = accmodel.Accounts(role='I', name='child2')
        self.ch2.add()
        self.parent.children.append(self.ch2)
        self.ch3 = accmodel.Accounts(role='I', name='child3')
        self.ch3.add()
        self.parent.children.append(self.ch3)
        gledger.db.session.flush()
        accountsView5 = accviews.AccountView.createView(name=self.parent.name)
        asDictionary = accountsView5.asDictionary()
        self.assertIn(asDictionary['children'][0]['name'], [self.ch1.name, self.ch2.name, self.ch3.name],
                                                               'Name in child list should be one of the children')
        
class TestAccountViewFunction(unittest.TestCase) :
    
    def setUp(self) :
        self.app = gledger.app.test_client()
        self.app.testing = True
        acc23 = accmodel.Accounts(name='wonky', role='L')
        acc23.add()
        acc24 = accmodel.Accounts(name='wonkyparent', role='L')
        acc24.add()
        acc24.children.append(acc23)
        acc26 = accmodel.Accounts(name='wonkygranny', role='L')
        acc26.add()
        gledger.db.session.commit()
        
    def tearDown(self) :
        try :
            acc24 = accmodel.Accounts.get_by_name('wonkyparent')
            if acc24 :
                gledger.db.session.delete(acc24)
        except SQLAlchemyError :
            pass
        try :
            acc23 = accmodel.Accounts.get_by_name('wonky')
            if acc23 :
                gledger.db.session.delete(acc23)
        except SQLAlchemyError :
            pass
        try :
            acc26 = accmodel.Accounts.get_by_name('wonkygranny')
            if acc26:
                gledger.db.session.delete(acc26)
        except SQLAlchemyError :
            pass
        gledger.db.session.commit() 
        
        
    def test_account_view(self) :
        """ Test if the account page returns the account and parent name """
        logging.debug('Test getting account view') 
        rv = self.app.get('/accounts/wonky')
        assert b'wonky' in rv.data
        assert b'wonkyparent' in rv.data        
        
    def test_account_post(self) :
        """ Test if account role can be changed """
        logging.debug('before posting')
        rv = self.app.post('/accounts/wonky', data = dict(name = "wonky", role = "A"),
            follow_redirects=True)
        logging.debug('Posting change of role done')
        acc25 = accmodel.Accounts.get_by_name("wonky")
        logging.debug('acc25: ' + acc25.name + ', ' + acc25.role)
        self.assertEqual(acc25.role, 'A', 'wonky account should be changed to asset')
    
    def test_set_parent(self) :
        """ Test if account parentage can be set """
        
        logging.debug('Before setting parent')
        gledger.db.session.commit()
        logging.debug('Granny added to database; now the transaction')
        rv = self.app.post('/accounts/wonkyparent', data = dict(name = "wonkyparent", 
                                                            parent_name = 'wonkygranny', Type = "A"),
            follow_redirects=True)
        logging.debug('Transaction done, now re-read accounts...')
        parent = accmodel.Accounts.get_by_name('wonkyparent')
        acc26 = accmodel.Accounts.get_by_name('wonkygranny')
        self.assertEqual(acc26.id, parent.parent_id, 'Not able to set parent property') 

class TestAccountList(unittest.TestCase):
    
    def setUp(self):
        create_standard_accountlist_testset(self)
        
    def tearDown(self):
        gledger.db.session.rollback()
        
    def test_return_accountlist(self):
        """ An accountlist can be returned """
        al = accmodel.AccountList().as_list()
        self.assertEqual(len(al), 7, 'Not all items in accountlist')
        
    def test_accountlist_keyed_name(self):
        """An accountlist can be returned with names as keys """
        ad = accmodel.AccountList().as_dict()
        self.assertTrue('bank'in ad, 'Key bank not in accountlist') 
        self.assertTrue('salaris'in ad, 'Key salaris not in accountlist')
        
    def test_set_pagelength(self):
        """ We can set a page length on AccountList """
        al = accmodel.AccountList(pagelength=3).as_list()
        self.assertEqual(len(al), 3, 'Cannot limit pagelength in accountlist')
        
    def test_page(self):
        """ We can ask for a page """
        al = accmodel.AccountList(pagelength=3, page=2)
        self.assertEqual(al.as_list()[0].name, 'debiteuren', 'Page 2 not correctly shown')
        
    def test_incomplete_page(self):
        """ We can retrieve an incomplete page """
        al = accmodel.AccountList(pagelength=3, page=3)
        self.assertEqual(len(al.as_list()), 1, 'Page with rest not correctly shown')        
        
    def test_accountlist_order(self):
        """ The accountlist is in reversed date/time order """
        al = accmodel.AccountList().as_list()
        for ind, account in enumerate(al):
            if ind > 0:
                self.assertTrue(al[ind].updated_at <= al[ind - 1].updated_at, 'Found out of order: ' + account.name)
                
    def test_limit_accountlist(self):
        """Limit the accountlist with a search string """
        al = accmodel.AccountList(search_string='iteur').as_list()
        self.assertEqual(len(al), 2, 'Wrong number of accounts selected')
        
    def test_accountlist_selection_empty(self):
        """ A search string that is not in the db, leads to empty list """
        al = accmodel.AccountList(search_string='n2fq').as_list()
        self.assertFalse(al, 'Accountlist not empty')
        
    def test_searchstring_minimum(self):
        """ A search string must be at least 3 characters """
        with self.assertRaises(ValueError) :       
            al = accmodel.AccountList(search_string='dg').as_list()
            
class TestAccountListView(unittest.TestCase):
    
    def setUp(self):
        create_standard_accountlist_testset(self)
        self.al = accmodel.AccountList()
        
    def tearDown(self):
        gledger.db.session.rollback()
        
    def test_create_account_list_view(self):
        """ We can create a view from an account list """
        alv = accviews.AccountListView(self.al)
        self.assertTrue(alv['inkopen'], 'Cannot find account in view')
        
    def test_num_accounts_in_list(self):
        alv = accviews.AccountListView(self.al)
        self.assertEqual(len(alv), 7, 'Not all accounts in list view')
        
class TestAccountListViewFunction(unittest.TestCase):
    
    def setUp(self):
        create_standard_accountlist_testset(self)
        self.app = gledger.app.test_client()
        self.app.testing = True
        
    def tearDown(self):
        gledger.db.session.rollback()
        
    def test_does_return_a_list(self):
        """ requesting a list without parameters returns the full list """
        logging.debug('Test getting account list view') 
        rv = self.app.get('/accountlist')
        assert b'inkopen' in rv.data
        assert b'bank' in rv.data
        assert b'salaris' in rv.data
        
    def test_return_list_with_search(self):
        """ requesting a list with parameter returns a smaller list """
        rv = self.app.get('/accountlist/teur')
        assert not b'inkopen' in rv.data
        assert b'crediteuren' in rv.data


class TestBalanceViews(unittest.TestCase):
    
    def setUp(self):
        create_standard_accountlist_testset(self)
        
    def tearDown(self):
        gledger.db.session.rollback()
        
    def test_create_balanceview(self):
        """ We can create a view for an account balance """
        
        balance_view = accviews.BalanceView.create_view(id=self.acc45.id)
        self.assertEqual(balance_view.balance, 2611, 'Amount not in view')
        
    def test_invalid_account(self):
        """ An unknown account raises the appropriate error """
        
        with self.assertRaises(accmodel.NoAccountError):
            balance_view = accviews.BalanceView.create_view(name='blaffy')
            
    def test_balance_view_dict(self):
        """ Test a balance view can return a dictionary """
        balance_view = accviews.BalanceView.create_view(id=self.acc45.id)
        bal_as_dict = balance_view.as_dictionary()
        self.assertIn('balance', bal_as_dict, 'Balance not in dictionary for balance view')
        self.assertEqual(bal_as_dict['balance'], '26.11', 'Balance incorrect in dictionary for balance view')
        
        

class TestAccountBalancesFunction(unittest.TestCase):
    
    def setUp(self):
        create_standard_accountlist_testset(self)
        self.app = gledger.app.test_client()
        self.app.testing = True
        
    def tearDown(self):
        gledger.db.session.rollback()
    
    def test_unknown_account_balance(self):
        """ Check an unknown account returns 400  """
        logging.debug('Testing getting an unknown account throws')
        rv = self.app.get('/balance/blaffy')
        assert b'400' in rv.data
        
    def test_get_balance(self):
        """ A balance can be gotten from an account """
        rv = self.app.get('/balance/rente')
        assert b'26.11' in rv.data
        
    def test_balance_for_period(self):
        """ We can get a balance for an account period """
        rv = self.app.get('/balance/rente/month/08-2018')
        self.assertIn(b'08-2018', rv.data, 'Incorrect string for post month')
        

def add_postmonths(monthlist) :
    """Add the postmonths requested in the list to the session """
    for postmonth in monthlist :
        pm = accmodel.Postmonths(postmonth=postmonth, monthstat='a')
        pm.add()
        
def create_standard_accountlist_testset(case):
    """ Create a standard list of accounts for different tests """
    add_postmonths([201507, 201506])
    case.acc40 = accmodel.Accounts(name='inkopen', role='E')
    case.acc40.add()
    case.acc40.updated_at = datetime(1983, 12, 16, hour=23, minute=40, second=44)
    case.acc41 = accmodel.Accounts(name='voorraad', role='A')
    case.acc41.add()
    case.acc41.updated_at = datetime(1988, 12, 16, hour=23, minute=29, second=44)
    case.acc42 = accmodel.Accounts(name='bank', role='A')
    case.acc42.add()
    case.acc42.updated_at = datetime(2013, 9, 12, hour=23, minute=16, second=44)
    case.acc43 = accmodel.Accounts(name='crediteuren', role='L')
    case.acc43.add()
    case.acc43.updated_at = datetime(2003, 9, 11, hour=2, minute=40, second=41)
    case.acc44 = accmodel.Accounts(name='debiteuren', role='A')
    case.acc44.add()
    case.acc44.updated_at = datetime(2003, 9, 11, hour=2, minute=40, second=41)
    case.acc45 = accmodel.Accounts(name='rente', role='A')
    case.acc45.add()
    case.acc45.updated_at = datetime(1999, 1, 15, hour=9, minute=41, second=41)
    case.acc46 = accmodel.Accounts(name='salaris', role='E')
    case.acc46.add()
    case.acc46.updated_at = datetime(2015, 11, 9, hour=11, minute=20, second=21)
    case.bal11 = accmodel.Balances(postmonth=201507, amount=1726, value_date='2015-07-10')
    case.acc40.balances.append(case.bal11)
    case.bal12 = accmodel.Balances(postmonth=201507, amount=1830, value_date='2015-07-10')
    case.acc41.balances.append(case.bal12)
    case.bal13 = accmodel.Balances(postmonth=201507, amount=10033, value_date='2015-07-10')
    case.acc42.balances.append(case.bal13)
    case.bal14 = accmodel.Balances(postmonth=201507, amount=7263, value_date='2015-07-10')
    case.acc43.balances.append(case.bal14)
    case.bal15 = accmodel.Balances(postmonth=201507, amount=3398, value_date='2015-07-11')
    case.acc44.balances.append(case.bal15)
    case.bal16 = accmodel.Balances(postmonth=201507, amount=2611, value_date='2015-07-09')
    case.acc45.balances.append(case.bal16)
    case.bal17 = accmodel.Balances(postmonth=201507, amount=17166, value_date='2015-07-08')
    case.acc46.balances.append(case.bal17)
    case.bal18 = accmodel.Balances(postmonth=201506, amount=7468, 
                                   value_date='2015-06-09')
    case.acc42.balances.append(case.bal18)
    gledger.db.session.flush()
                    
if __name__ == '__main__':
    unittest.main()
