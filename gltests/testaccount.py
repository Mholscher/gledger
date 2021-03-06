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
from decimal import Decimal
import gledger
import glviews.accountviews as accviews
import glviews.forms as glforms
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

    def test_role_translation(self):
        """ We can translate the role attribute """

        acc52 = accmodel.Accounts(name='creditors', role='L')
        gledger.db.session.flush()
        self.assertEqual(acc52.ROLE_NAME[acc52.role], 'Liability', 'No name found for role') 

                    
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
        """ We can read a balance back """
        acc11 =  accmodel.Accounts(role='L', name='bankloans')
        acc11.add()
        bal3 = accmodel.Balances(postmonth=accmodel.postmonth_for(date.today()), amount=1217, value_date='2015-07-21')
        acc11.balances.append(bal3)
        self.assertEqual(acc11.current_balance(), 1217, 'Balance not correctly read back')
        
    def test_history_balance(self) :
        """ The correct balances are shown for history """
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
        
    def test_branch_balance(self):
        """ The correct balance is shown for different dates """
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
        acc39.post_amount('Db', Decimal('1250'), datetime.today())
        self.assertEqual(acc39.current_balance(), -1250, 'Account balance not correct')


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
        """ We cannot create a postmonth that exists """
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

    def test_postmonth_extern(self):
        """ A postmonth is converted to a correct external format """

        pm2 = accmodel.Postmonths(postmonth=201707, monthstat = 'a')
        pm2.add()
        gledger.db.session.flush()
        self.assertEqual(accmodel.Postmonths.external(pm2.postmonth), '07-2017', 'Invalid external postmonth: ' + accmodel.Postmonths.external(pm2.postmonth))

    def test_can_close_postmonth(self):
        """ We can close a postmonth """

        pm3 = accmodel.Postmonths(postmonth=201709, monthstat = 'a')
        pm3.add()
        gledger.db.session.flush()
        self.assertTrue(pm3.status_can_post(), 'Cannot post to open month')
        pm3 = gledger.db.session.query(accmodel.Postmonths).filter_by(postmonth=201709).first()
        pm3.close()
        gledger.db.session.flush()
        self.assertFalse(pm3.status_can_post(), 'Can post to closed month')

class TestPostmonthList(unittest.TestCase):

    def setUp(self):
        
        self.pm4 = accmodel.Postmonths(postmonth=201601, monthstat='a')
        self.pm4.add()
        self.pm5 = accmodel.Postmonths(postmonth=201605, monthstat='a')
        self.pm5.add()
        self.pm6 = accmodel.Postmonths(postmonth=201705, monthstat='c')
        self.pm6.add()
        gledger.db.session.flush()
        
    def tearDown(self) :
        gledger.db.session.rollback() 
    
    def test_return_month_list(self):
        """ We can return a list of postmonths """

        pml1 = accmodel.PostmonthList()
        self.assertEqual(len(pml1), 3, 'Wrong no of months returned')
        self.assertIn(self.pm5, pml1, 'Postmonth missing')

    def test_return_list_from_month(self):
        """ We can return a list starting at a month """

        pml2 = accmodel.PostmonthList(from_month=201605)
        self.assertEqual(len(pml2), 2, 'Too many or little months returned')

    def test_from_last_closing(self):
        """ If there is one closing date, only months after it are returned 
        """

        close_date = accmodel.CloseDates(closing_date=datetime(2016, 2, 1))
        close_date.add()
        gledger.db.session.flush()
        pml7 = accmodel.PostmonthList()
        self.assertNotIn(self.pm4, pml7, 'Postmonth before closing in list')

    def test_from_second_closing(self):
        """ If there is two closing dates, months after last are returned 
        """

        close_date = accmodel.CloseDates(closing_date=datetime(2016, 2, 1))
        close_date.add()
        close_date = accmodel.CloseDates(closing_date=datetime(2016, 6, 1))
        close_date.add()
        gledger.db.session.flush()
        pml8 = accmodel.PostmonthList()
        self.assertNotIn(self.pm5, pml8, 'Postmonth before closing in list')


class TestPostmonthPaging(unittest.TestCase):

    def setUp(self):

        add_postmonths([201605, 201607, 201701, 201706, 201802])
        gledger.db.session.flush()

    def tearDown(self):

        gledger.db.session.rollback()

    def test_can_set_pagelength(self):
        """ We can set a page length for the postmonth list """

        pml3 = accmodel.PostmonthList(pagelength=3)
        self.assertEqual(len(pml3), 3, 'Wrong length ' + str(len(pml3)) + ' for list')

    def test_can_show_page_2(self):
        """ We can show a following page of postmonths """

        pml4 = accmodel.PostmonthList(pagelength=3, page=2)
        self.assertEqual(len(pml4), 2, 'Wrong length ' + str(len(pml4)) + ' for list')

    def test_postmonths_ordered(self):
        """ The postmonths in the list should be ordered ascending """

        pml5 = accmodel.PostmonthList(pagelength=3, page=2)
        self.assertEqual(pml5[0].postmonth, 201706, 'Starts at wrong month')
        self.assertEqual(pml5[1].postmonth, 201802, 'Months not in ascending order')

    def test_can_return_num_pages(self):
        """ We can get the number of pages """

        pml6 = accmodel.PostmonthList(pagelength=3, page=2)
        num_pages = pml6.num_pages()
        self.assertEqual(num_pages, 2, 'Incorrect number of pages: ' + str(num_pages))


class TestPostmonthListView(unittest.TestCase):

    def setUp(self):

        add_postmonths([201606, 201608, 201702, 201711, 201812])
        gledger.db.session.flush()

    def tearDown(self):

        gledger.db.session.rollback()

    def test_create_list_view(self):
        """ We can create a Postmonth List View """

        plv1 = accviews.PostmonthListView()
        external_postmonth = plv1[0][0]
        self.assertEqual(external_postmonth, '06-2016', 'Wrong month in 1st item')
        self.assertEqual(len(plv1), 5, 'Wrong number of views')

    def test_list_from_month(self):
        """ We can create a listview from a month onwards """

        plv2 = accviews.PostmonthListView(from_month=201702)
        self.assertEqual(len(plv2), 3, 'Wrong number of months in list')

    def test_empty_view(self):
        """ The view goes undeterred by supplying it with an empty list """

        plv3 = accviews.PostmonthListView(from_month=201902)
        self.assertEqual(len(plv3), 0, 'There should be no months in list')        

    def test_can_set_pagelength(self):
        """ We can set pagelength on a postmonth list view  """

        plv4 = accviews.PostmonthListView(pagelength=3)
        self.assertEqual(len(plv4), 3, 'Wrong number of views')

    def test_can_show_page_2(self):
        """ We can get a following page """

        plv5 = accviews.PostmonthListView(pagelength=3, page=2)
        self.assertEqual(len(plv5), 2, 'Page 2 should have 2 views')

    def test_view_exposes_total_pages(self):
        """ The view exposes the total number of pages """

        plv6 = accviews.PostmonthListView(pagelength=3)
        self.assertEqual(plv6.total_pages, 2,\
            'Wrong number of pages in list view')


class TestMorePostmonthListView(unittest.TestCase):

    def setUp(self):

        add_postmonths([201706, 201808, 201902, 201911, 201912])
        gledger.db.session.flush()

    def tearDown(self):

        gledger.db.session.rollback()

    def test_list_view_create(self):
        """ We can create the postmonth list view for all months """

        pl9 = accmodel.PostmonthList()
        plv7 =accviews.PostmonthListView(pl9)
        self.assertEqual(len(plv7), 5, 'Incorrect number of months in view')
        self.assertIn(('02-2019', '201902', 'a'), plv7, 'Missing/wrong postmonth in view')
        
    def test_list_view_page_size(self):
        """ We can get the page size for the list view """

        pl10 = accmodel.PostmonthList(pagelength=3)
        plv8 = accviews.PostmonthListView(postmonths=pl10)
        self.assertEqual(plv8.pagelength, 3, 'Pagelength not adjusted')
        self.assertEqual(len(plv8), 3, 'Actual length not as advertised')

    def test_list_view_page(self):
        """ We can get the number  for a second page """

        pl11 = accmodel.PostmonthList(pagelength=3, page=2)
        plv9 = accviews.PostmonthListView(pl11)
        self.assertEqual(plv9.page, 2, 'Page not as requested')

    def test_number_of_pages(self):
        """ We can get/set the number of pages """

        pl12 = accmodel.PostmonthList(pagelength=3, page=2)
        plv10 = accviews.PostmonthListView(pl12)
        self.assertEqual(plv10.total_pages, 2, 'Incorrect number of pages')        


class TestPostmonthTransactions(unittest.TestCase):

    def setUp(self):

        add_postmonths([201606, 201608, 201702, 201711, 201812])
        self.app = gledger.app.test_client()
        self.app.testing = True

        gledger.db.session.flush()

    def tearDown(self):

        gledger.db.session.rollback()
        #Delete any remaining records
        pm = gledger.db.session.query(accmodel.Postmonths).filter(accmodel.Postmonths.postmonth.in_([201606, 201608, 201702, 201711, 201812])).all()
        for postmonth in pm:
            gledger.db.session.delete(postmonth)
        gledger.db.session.commit()

    def test_show_all(self):
        """ Show all available postmonths """

        rv = self.app.get('/postmonthlist')
        self.assertIn(b'201702', rv.data, 'Expected month not in response')

    def test_show_edited(self):
        """ Available postmonths are edited """

        rv = self.app.get('/postmonthlist')
        self.assertIn(b'02-2017', rv.data, 'Expected edited month not in response')

    def test_get_with_closing_date(self):
        """ We get a restricted set with a closing date in the DB """

        close_date = accmodel.CloseDates(closing_date=datetime(2017, 1, 1))
        close_date.add()
        gledger.db.session.flush()
        rv = self.app.get('/postmonthlist')
        self.assertIn(b'02-2017', rv.data, 'Expected edited month not in response')
        self.assertNotIn(b'08-2016', rv.data, 'Unexpected month in data')

    def test_with_from_month(self):
        """ We can limit the postmonths through a request argument """

        rv = self.app.get('/postmonthlist?from_month=01-2017')
        self.assertIn(b'02-2017', rv.data, 'Expected edited month not in response')
        self.assertNotIn(b'08-2016', rv.data, 'Unexpected month in data')

    def test_request_page_2(self):
        """ We can request the second page """

        rv = self.app.get('/postmonthlist?page=2')
        self.assertNotIn(b'12-2018', rv.data, 'Not on (empty) page 2')

    def test_updates_succeed(self):
        """ We can update the postmonths """

        all_months = {'201606':'c', '201608':'c', '201702':'c',\
            '201711':'c', '201812':'c'}
        rv = self.app.post('/postmonthlist', data=all_months)
        pms = gledger.db.session.query(accmodel.Postmonths).filter(accmodel.Postmonths.monthstat == 'c').all()
        self.assertEqual(len(pms), 5, 'Not all/too many months closed')

    def test_corrupt_update_is_bad_request(self):
        """ Corrupted post requests lead to bad request """

        all_months = {'201606':'c', '201608':'c', '201702':'c',\
            '201707':'c', '201711':'c', '201812':'c'}
        rv = self.app.post('/postmonthlist', data=all_months)
        self.assertIn(b'Bad Request', rv.data, 'No Bad Request returned')


class TestPostmonthListUpdates(unittest.TestCase):

    def setUp(self):

        add_postmonths([201606, 201608, 201702, 201711, 201812])
        self.plr = [(201608, 'c'), (201711, 'a')]
        self.pd = {201608:'c', 201711:'a'}
        gledger.db.session.flush()

    def tearDown(self):

        gledger.db.session.rollback()

    def test_create_list_from_request(self):
        """ Create a list of months to be processed """

        plp = list()
        plp = accmodel.Postmonths.list_to_update(self.plr)
        pm7 = gledger.db.session.query(accmodel.Postmonths).filter(accmodel.Postmonths.postmonth.in_([201608, 201711])).all()
        self.assertEqual(len(plp), 2, 'Missing months in list')
        self.assertIn(pm7[0], plp, 'Postmonth not in list')
        self.assertIn(pm7[1], plp, 'Postmonth not in list')

    def test_execute_update(self):
        """ We can update the status flag """

        accmodel.Postmonths.update_from_list(self.plr)
        gledger.db.session.flush()
        pm8 = gledger.db.session.query(accmodel.Postmonths).filter(accmodel.Postmonths.postmonth==201608).first()
        self.assertEqual(pm8.monthstat, 'c', 'Did not close month')

    def test_update_more(self):
        """ Update more than one month status flag """

        self.plr.append((201702, 'c'))
        accmodel.Postmonths.update_from_list(self.plr)
        gledger.db.session.flush()
        pm9 = gledger.db.session.query(accmodel.Postmonths).filter(accmodel.Postmonths.monthstat=='c').all()
        self.assertEqual(len(pm9), 2, 'Not all/too many months closed')
        pm9_list = accmodel.Postmonths.list_to_update(self.plr)
        self.assertIn(pm9_list[0].postmonth, [201702, 201608], 'Unknown month in result')

    def test_cannot_set_invalid_status(self):
        """ It must be impossible to set a status to invalid value """

        self.plr.append((201702, 't'))
        with self.assertRaises(accmodel.InvalidPostmonthError):
            accmodel.Postmonths.update_from_list(self.plr)
            gledger.db.session.flush()

    def test_fail_for_missing(self):
        """ Fail for non-existing postmonth """
        
        self.plr.append((2, 'c'))
        with self.assertRaises(accmodel.InvalidPostmonthError):
            accmodel.Postmonths.update_from_list(self.plr)            

    def test_update_from_dict(self):
        """ Use a dict to pass in changes """

        accmodel.Postmonths.update_from_dict(self.pd)
        pm11 = gledger.db.session.query(accmodel.Postmonths).filter(accmodel.Postmonths.postmonth==201608).first()
        self.assertEqual(pm11.monthstat, 'c', 'Postmonth not closed')
        pm12 = gledger.db.session.query(accmodel.Postmonths).filter(accmodel.Postmonths.postmonth==201711).first()
        self.assertEqual(pm12.monthstat, 'a', 'Postmonth closed incorrectly')


class TestPostmonthSelections(unittest.TestCase):

    def setUp(self):

        add_postmonths([201606, 201608, 201702, 201711, 201812])
        self.plr = [(201608, 'c'), (201711, 'a')]
        gledger.db.session.flush()

    def tearDown(self):

        gledger.db.session.rollback()

    def test_list_status_all(self):
        """ We can list all available """

        accmodel.Postmonths.update_from_list(self.plr)
        pml10 = accmodel.Postmonths.get_postmonths_between_dates(datetime(2016, 1, 1),
                                                                 datetime(2019, 1, 1))
        self.assertEqual(len(pml10), 5, 'Wrong number of months in list')

    def test_list_only_active(self):
        """ We can list only active months """

        accmodel.Postmonths.update_from_list(self.plr)
        pml11 = accmodel.Postmonths.get_postmonths_between_dates(datetime(2016, 1, 1),
                                                                 datetime(2019, 1, 1),
                                                                 'a')
        self.assertEqual(len(pml11), 4, 'Wrong number of active months in list')

    def test_no_months_with_status(self):
        """ If we request a status that is not there, empty list """

        pml12 = accmodel.Postmonths.get_postmonths_between_dates(datetime(2016, 1, 1),
                                                                 datetime(2019, 1, 1),
                                                                 'c')
        self.assertEqual(len(pml12), 0, 'Closed months should not be in list')

    def test_date_range_empty(self):
        """ If we request a range that is empty, empty list """

        pml13 = accmodel.Postmonths.get_postmonths_between_dates(datetime(2016, 1, 1),
                                                                 datetime(2015, 8, 1))
        self.assertEqual(len(pml13), 0, 'Months in list for empty period')

    def test_conflict_postmonth(self):
        """ If we request a range that results in same months, empty list """

        pml14 = accmodel.Postmonths.get_postmonths_between_dates(datetime(2016, 1, 1),
                                                                 datetime(2016, 1, 15))
        self.assertEqual(len(pml14), 0, 'Months in list for empty period')
        
        

    #def test_list_none_with_status(self


class TestValidatePostmonthUpdates(unittest.TestCase):

    def setUp(self):

        add_postmonths([201806, 201810, 201901, 201902, 201909])
        self.plr = [(201810, 'c'), (201902, 'a')]
        self.pds = {'201810':'c', '201902':'a'}
        gledger.db.session.flush()

    def tearDown(self):

        gledger.db.session.rollback()

    def test_can_convert_month(self):
        """ Convert a month string to valid postmonth """

        self.pds1 = self.pds.copy()
        self.pds1['2017112'] = 'c'
        with self.assertRaises(accmodel.InvalidPostmonthError):
            accmodel.Postmonths.update_from_dict(self.pds1)

    def test_no_alphabetic_keys(self):
        """ A postmonth key should not comntain alpabetics """

        self.pds1 = self.pds.copy()
        self.pds1['ãnnos'] = 'a'
        with self.assertRaises(accmodel.InvalidPostmonthError):
            accmodel.Postmonths.update_from_dict(self.pds1)

class TestAccountviews(unittest.TestCase) :
    
    def tearDown(self) :
        gledger.db.session.rollback() 
    
    def test_accountview_load_fail(self) :
        """ Trying to load an accountview for a non-existent account
            should return an error """
        with self.assertRaises(accmodel.NoAccountError) :       
            accountsView = accviews.AccountView.create_view(id=1)
            
    def test_accountview_load(self) :
        """ creating an accountsview for an account should retain fields """
        acc13 = accmodel.Accounts(name = 'proefbalans', role = 'I')
        acc13.add()
        gledger.db.session.flush()
        accountsView1 = accviews.AccountView.create_view(id=acc13.id)
        self.assertEqual(accountsView1.account.name, acc13.name, 'Accountsview for wrong account')
        self.assertEqual(accountsView1.account.role, acc13.role, 'Accountsview did not retain field')
    
    def test_accountview_as_dict(self) :
        """ You can return an accountview as a nested dictionary """
        
        acc14 = accmodel.Accounts(name = 'voorziening251', role = 'A')
        acc14.add()
        gledger.db.session.flush()
        accountsView2 = accviews.AccountView.create_view(id=acc14.id)
        as_dictionary = accountsView2.as_dictionary()
        self.assertEqual(accountsView2.as_dictionary()["account"]["name"], acc14.name, 'Name should be key in accountsview')
        
    def test_accountview_has_parent(self) :
        """ The accountview contains the parent account """
        acc15 = accmodel.Accounts(name = 'parent', role = 'I')
        acc15.add()
        acc16 =  accmodel.Accounts(name = 'this', role = 'I')
        acc16.add()
        gledger.db.session.flush()
        acc16.parent_id = acc15.id
        gledger.db.session.flush()
        accountsView3 = accviews.AccountView.create_view(name = acc16.name)
        self.assertEqual(accountsView3.as_dictionary()["parent"]["name"],acc15. name, 'Parent not set properly in Accountsview') 
    
    def test_accountview_null_parent(self) :
        """ An account with a null parent can be in an accountview """
        acc17 = accmodel.Accounts(name = 'parent', role = 'I')
        acc17.add()
        acc18 =  accmodel.Accounts(name = 'this', role = 'I')
        acc18.add()
        gledger.db.session.flush()
        acc18.parent_id = acc17.id
        gledger.db.session.flush()
        accountsView4 = accviews.AccountView.create_view(name = acc17.name)
        self.assertEqual(accountsView4.parent, None, 'An accountview of an account with no parent should have None as parent')
        as_dictionary = accountsView4.as_dictionary()
        self.assertTrue("parent_id" not in as_dictionary)
        
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
        accountsView5 = accviews.AccountView.create_view(name=self.parent.name)
        as_dictionary = accountsView5.as_dictionary()
        self.assertIn(as_dictionary['children'][0]['name'], [self.ch1.name, self.ch2.name, self.ch3.name],
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
        self.assertEqual(len(al), 10, 'Not all items in accountlist')
        
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
        self.assertEqual(al.as_list()[0].name, 'salaris', 'Page 2 not correctly shown')
        
    def test_incomplete_page(self):
        """ We can retrieve an incomplete page """
        al = accmodel.AccountList(pagelength=3, page=4)
        self.assertEqual(len(al.as_list()), 2, 'Page with rest not correctly shown')        
        
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

    def test_one_char_search(self):
        """ A one character search string does not fail """

        with self.assertRaises(ValueError):
            al = accmodel.AccountList(search_string='n').as_list()

    def test_list_has_pageinfo(self):
        """ An account_list has page info """
        al = accmodel.AccountList(pagelength=3, page=2)
        self.assertEqual(al.page, 2, 'Wrong or no page in list')
        self.assertEqual(al.pagelength, 3, 'Wrong or no pagelength in list')
        self.assertEqual(al.num_records, 11, 'Wrong or no number of records in list')
            
class TestAccountListView(unittest.TestCase):
    
    def setUp(self):
        create_standard_accountlist_testset(self)
        self.al = accmodel.AccountList()
        
    def tearDown(self):
        gledger.db.session.rollback()
        
    def test_create_account_list_view(self):
        """ We can create a view from an account list """
        
        alv = accviews.AccountListView()
        account_bank = []
        for account in alv:
            if account['name'] == 'bank':
                account_bank.append(account)
        self.assertEqual(len(account_bank), 1, 'No/more than 1 account bank in view')
        
    def test_num_accounts_in_list(self):
        alv = accviews.AccountListView()
        self.assertEqual(len(alv), 10, 'Not all accounts in list view')

    def test_page_info_in_view(self):
        """ Page info is placed in view """

        alv = accviews.AccountListView()
        self.assertEqual(alv.page, 1, 'Wrong or no page number in view')
        self.assertEqual(alv.pagelength, 10, 'Wrong or no page length in view')
        self.assertEqual(alv.total_pages, 2, 'Wrong or no no of pages in view')

    def test_exact_no_of_pages(self):
        """The total pages is an exact multiple of pagelength """

        self.acc51 = accmodel.Accounts(name='ontvangen rente', role='I')
        self.acc51.add()
        self.acc51.updated_at = datetime(2003, 12, 18, hour=10, minute=20, second=44)
        gledger.db.session.flush()
        alv3 = accviews.AccountListView(pagelength=3, page=2)
        self.assertEqual(alv3.total_pages, 4, 'Wrong or no number of pages')
        
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
#        assert b'inkopen' in rv.data
        assert b'bank' in rv.data
        assert b'salaris' in rv.data

    def test_does_return_role(self):
        """ We return the role name in the list """

        rv = self.app.get('/accountlist')
        self.assertIn(b'Liability', rv.data, 'Missing role')
        self.assertIn(b'Expense', rv.data, 'Missing role')
        
    def test_return_list_with_search(self):
        """ requesting a list with parameter returns a smaller list """

        rv = self.app.get('/accountlist?search_for=teur')
        assert not b'inkopen' in rv.data
        assert b'crediteuren' in rv.data

    def test_return_page_2(self):
        """ We can return the 2nd page of the list """

        rv = self.app.get('/accountlist?page=2')
        self.assertIn(b'inkopen', rv.data, 'Expect inkopen, not found')
        self.assertNotIn(b'software', rv.data, 'Do NOT expect software, is present')


class TestAccountListNavigation(unittest.TestCase):

    def setUp(self):

        create_standard_accountlist_testset(self)
        self.app = gledger.app.test_client()
        self.app.testing = True

    def tearDown(self):
        gledger.db.session.rollback()

    def test_can_go_first_page(self):
        """ We see a link to the first page """

        rv = self.app.get('/accountlist?page=2')
        self.assertIn(b'page=1', rv.data, 'No link to first page')

    def test_can_go_prev_page(self):
        """ We can go to the previous page """

        rv = self.app.get('/accountlist?page=2')
        self.assertIn(b'\xe2\x8f\xb4', rv.data, 'No link to previous page')


class TestEmptyAccountListNavigation(unittest.TestCase):

    def setUp(self):

        self.app = gledger.app.test_client()
        self.app.testing = True

    def tearDown(self):
        gledger.db.session.rollback()

    def test_can_exec_empty_page(self):
        """ Navigation exists on empty page """

        rv = self.app.get('/accountlist')
        self.assertIn(b'page=1', rv.data, 'No link to first page')

    def test_can_search_on_empty_page(self):
        """ We can search on an empty page and database """

        rv = self.app.get('/accountlist?search_for=n')
        self.assertIn(b'page=1', rv.data, 'No navigation')

        

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
    case.acc47 = accmodel.Accounts(name='betaalde btw', role='E')
    case.acc47.add()
    case.acc47.updated_at = datetime(2015, 12, 7, hour=11, minute=40, second=21)
    case.acc48 = accmodel.Accounts(name='kantoorspul', role='E')
    case.acc48.add()
    case.acc48.updated_at = datetime(2017, 3, 9, hour=9, minute=20, second=45)
    case.acc49 = accmodel.Accounts(name='software', role='A')
    case.acc49.add()
    case.acc49.updated_at = datetime(2015, 12, 5, hour=15, minute=55, second=21)
    case.acc50 = accmodel.Accounts(name='afdracht', role='E')
    case.acc50.add()
    case.acc50.updated_at = datetime(2015, 10, 1, hour=13, minute=20, second=55)
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
