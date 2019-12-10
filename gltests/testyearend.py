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
from dateutil.relativedelta import relativedelta
import logging
import json
from sqlalchemy.exc import DatabaseError
import gledger
import glviews.postingviews as postviews
import glmodels.glposting as posts
import glmodels.glaccount as accmodel
import glmodels.glyearend as yearend
from gltests.testaccount import add_postmonths


class TestCreateJournal(unittest.TestCase):

    def setUp(self):

        create_standard_accountlist_testset(self)
        gledger.db.session.flush()
        self.start_next_year = datetime(2016, 1, 1)

    def tearDown(self):

        gledger.db.session.rollback()

    def test_journal_has_posting(self):
        """ A journal in internal format is created """

        jrn1 = yearend.YearEndJournal(start_next_year=self.start_next_year)
        self.assertIn('account', jrn1['journal']['postings'][0],
                      'No field account in first posting')
        self.assertIn(jrn1['journal']['postings'][0]['account'], 
                      {'inkopen', 'verkopen'}, "Wrong account selected")

    def test_journal_has_function(self):
        """ The journal should have a function of "insert" """

        jrn2 = yearend.YearEndJournal(start_next_year=self.start_next_year)
        self.assertIn('function', jrn2['journal'],
                      'Journal should have function')
        self.assertEqual(jrn2['journal']['function'], 'insert',
                         "Invalid function: "+ jrn2['journal']['function'])

    def test_journal_counter_post(self):
        """ The journal has a posting to a balance account """

        jrn11 = yearend.YearEndJournal(start_next_year=self.start_next_year)
        self.assertIn('winst', [account['account'] for account \
            in jrn11['journal']['postings']], 'No profit posting')

    def test_amount_profit(self):
        """ The amount of profit should balance profit/loss accounts """

        jrn12 = yearend.YearEndJournal(start_next_year=self.start_next_year)
        for posting in jrn12['journal']['postings']:
            if posting['account'] == 'winst':
                winst_posted = posting['amount']
                debcred = posting['debitcredit']
        self.assertEqual(winst_posted, 3449, 'Incorrect profit posted')


class TestYearEndDateEtc(unittest.TestCase):

    def setUp(self):

        create_standard_accountlist_testset(self)
        gledger.db.session.flush()

    def tearDown(self):

        gledger.db.session.rollback()

    def test_pass_date(self):
        """ If we pass a specific date, it should pick that date """

        jrn3 = yearend.YearEndJournal(start_next_year=datetime(2016, 1, 1))
        self.assertEqual(jrn3['journal']['postings'][0]['valuedate'], 
                      '2016-01-01', "Wrong valuedate in journal")

    def test_close_year_from_last(self):
        """ If we do not pass date, close one year from last """

        last_close = accmodel.CloseDates(closing_date=datetime(2015, 1, 1))
        last_close.add()
        gledger.db.session.flush()
        jrn4 = yearend.YearEndJournal()
        self.assertEqual(jrn4['journal']['postings'][0]['valuedate'], 
                      '2016-01-01', "Wrong value date determined")

    def test_year_from_last_missing(self):
        """ We try to close year from last, but no last close in db """

        with self.assertRaises(ValueError):
            jrn5 = yearend.YearEndJournal()

    def test_close_in_future(self):
        """ A closing date can not be in the future """

        new_closing = datetime.now() + relativedelta(days=1)
        with self.assertRaises(ValueError):
            jrn6 = yearend.YearEndJournal(start_next_year=new_closing)

    def test_closing_after_more_than_1_year(self):
        """ Closing can not be done at more than a year from previous """

        last_close = accmodel.CloseDates(closing_date=datetime(2014, 1, 1))
        last_close.add()
        gledger.db.session.flush()
        with self.assertRaises(ValueError):
            jrn7 = yearend.YearEndJournal(start_next_year=datetime(2016, 1, 1))

    def test_open_month_fails_year_end(self):
        """ An open postmonth makes year end fail """

        pm1 = accmodel.Postmonths(postmonth=201509, monthstat='a')
        pm1.add()
        gledger.db.session.flush()
        with self.assertRaises(ValueError):
            jrn8 = yearend.YearEndJournal(start_next_year=datetime(2016, 1, 1))

    def test_open_month_after_close(self):
        """ An open postmonth after close date don't matter """

        pm2 = accmodel.Postmonths(postmonth=201609, monthstat='a')
        pm2.add()
        gledger.db.session.flush()
        jrn9 = yearend.YearEndJournal(start_next_year=datetime(2016, 1, 1))
        self.assertTrue(jrn9)


class TestYearEndSplit(unittest.TestCase):

    def setUp(self):

        create_standard_accountlist_testset(self)
        create_accounts_for_more(self)
        gledger.db.session.flush()

    def tearDown(self):

        gledger.db.session.rollback()

    def test_limit_accounts(self):
        """ We can limit the number of accounts processed """

        jrn10 = yearend.YearEndJournal(start_next_year=datetime(2016, 1, 1), num_accounts=3)
        self.assertEqual(len(jrn10['journal']['postings']), 4, 'Wrong number of accounts')


def create_standard_accountlist_testset(case):
    """ Create a standard list of accounts for different tests """
    add_postmonths([201507, 201506])
    case.acc1 = accmodel.Accounts(name='inkopen', role='E')
    case.acc1.add()
    case.acc2 = accmodel.Accounts(name='voorraad', role='A')
    case.acc2.add()
    case.acc3 = accmodel.Accounts(name='winst', role='A')
    case.acc3.add()
    case.acc4 = accmodel.Accounts(name='verkopen', role='I')
    case.acc4.add()
    case.bal1 = accmodel.Balances(postmonth=201507, amount=1716, value_date='2015-07-10')
    case.acc1.balances.append(case.bal1)
    case.bal2 = accmodel.Balances(postmonth=201507, amount=8826, value_date='2015-07-18')
    case.acc2.balances.append(case.bal2)
    case.bal3 = accmodel.Balances(postmonth=201507, amount=-1733, value_date='2015-07-19')
    case.acc4.balances.append(case.bal3) # Careful: bal3 and acc4
    pmlist = gledger.db.session.query(accmodel.Postmonths).\
        filter(accmodel.Postmonths.postmonth.in_([201507, 201506])).all()
    for pm in pmlist:
        pm.monthstat = 'c'

def create_accounts_for_more(case):
    """ Create a list of accounts for tests involving 'many' accounts """
    
    pmlist = gledger.db.session.query(accmodel.Postmonths).\
        filter(accmodel.Postmonths.postmonth.in_([201507, 201506])).all()
    for pm in pmlist:
        pm.monthstat = 'a'
    case.acc5 = accmodel.Accounts(name='kantoorart', role='E')
    case.acc5.add()
    case.bal5 = accmodel.Balances(postmonth=201507, amount=3316, value_date='2015-07-12')
    case.acc5.balances.append(case.bal5)
    case.acc6 = accmodel.Accounts(name='declaraties', role='E')
    case.acc6.add()
    case.bal6 = accmodel.Balances(postmonth=201507, amount=2566, value_date='2015-07-31')
    case.acc6.balances.append(case.bal6)
    case.acc7 = accmodel.Accounts(name='ontvangen rente', role='I')
    case.acc7.add()
    case.bal7 = accmodel.Balances(postmonth=201507, amount=5764, value_date='2015-07-18')
    case.acc7.balances.append(case.bal7)
    case.acc8 = accmodel.Accounts(name='int late bet', role='E')
    case.acc8.add()
    case.bal8 = accmodel.Balances(postmonth=201507, amount=1755, value_date='2015-07-21')
    case.acc8.balances.append(case.bal8)
    pmlist = gledger.db.session.query(accmodel.Postmonths).\
        filter(accmodel.Postmonths.postmonth.in_([201507, 201506])).all()
    for pm in pmlist:
        pm.monthstat = 'c'




if __name__ == '__main__':
    unittest.main()
