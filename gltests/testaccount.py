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
from datetime import date
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
        self.assertEqual(acc5.parent, acc4.id)
        
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
                    
class TestDomainProcesses(unittest.TestCase) :
    
    def tearDown(self) :
        gledger.db.session.rollback() 

    def test_refuse_accttype(self) :
        """ We refuse an invalid account type """        
        with self.assertRaises(ValueError) :       
            acc3 = accmodel.Accounts(name = 'rekening', role = 'C')  
            
    def test_refuse_future_postmonth(self) :
        """ A balance cannot be created for a future postmonth """
        current_postmonth  = accmodel.postmonth_for(date.today())
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
        self.assertEqual(acc27.name, acc8.parent, 'Failed to set parent')
        
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
        acc16.parent = acc15.id
        gledger.db.session.flush()
        accountsView3 = accviews.AccountView.createView(name = acc16.name)
        self.assertEqual(accountsView3.asDictionary()["parent"]["name"],acc15. name, 'Parent not set properly') 
    
    def test_accountview_null_parent(self) :
        """ An account with a null parent can be in an accountview """
        acc17 = accmodel.Accounts(name = 'parent', role = 'I')
        acc17.add()
        acc18 =  accmodel.Accounts(name = 'this', role = 'I')
        acc18.add()
        gledger.db.session.flush()
        acc18.parent = acc17.id
        gledger.db.session.flush()
        accountsView4 = accviews.AccountView.createView(name = acc17.name)
        self.assertEqual(accountsView4.parent, None, 'An accountview of an account with no parent should have None as parent')
        asDictionary = accountsView4.asDictionary()
        self.assertTrue("parent" not in asDictionary)
        
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
        
class TestViewFunction(unittest.TestCase) :
    
    def setUp(self) :
        self.app = gledger.app.test_client()
        self.app.testing = True
        acc23 = accmodel.Accounts(name='wonky', role='L')
        acc23.add()
        acc24 = accmodel.Accounts(name='wonkyparent', role='L')
        acc24.add()
        acc24.children.append(acc23)
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
        gledger.db.session.commit() 
        
        
    def test_account_view(self) :
        """ Test if the account page returns the account name """
        logging.debug('Test getting account view') 
        rv = self.app.get('/accounts/wonky')
        assert b'wonky' in rv.data
        
#    def test_account_post(self) :
#        """ Test if account role can be changed """
#        logging.debug('before posting')
#        rv = self.app.post('/accounts/wonky', data = dict(Account = "wonky", Type = "A"),
#            follow_redirects=True)
#        logging.debug('Posting change of role done')
#        acc25 = accmodel.Accounts.get_by_name("wonky")
#        logging.debug('acc25: ' + acc25.name + ', ' + acc25.role)
#        self.assertEqual(acc25.role, 'A', 'wonky account should be changed to asset')
    
#    def test_set_parent(self) :
#        """ Test if account parentage can be set """
#        logging.debug('Before setting parent')
#        acc26 = accmodel.Accounts(name='creditorgranny', role='L')
#        acc26.add()
#        gledger.db.session.commit()
#        logging.debug('Granny added to database; now the transaction')
#        rv = self.app.post('/accounts/creditorparent', data = dict(Account = "creditorparent", 
#                                                            Parent = 'creditorgranny', Type = "A"),
#            follow_redirects=True)
#        logging.debug('Transaction done, now re-read accounts...')
#        parent = accmodel.Accounts.get_by_name('creditorparent')
#        acc26 = accmodel.Accounts.get_by_name('creditorgranny')
#        self.assertEqual(acc26.id, parent.parent, 'Not able to set parent property') 
#        gledger.db.session.delete(parent)
#        gledger.db.session.delete(acc26)
#        gledger.db.session.commit()


def add_postmonths(monthlist) :
    """Add the postmonths requested in the list to the session """
    for postmonth in monthlist :
        pm = accmodel.Postmonths(postmonth=postmonth, monthstat='a')
        pm.add()
                    
if __name__ == '__main__':
    unittest.main()
