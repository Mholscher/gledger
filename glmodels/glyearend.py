#    Copyright 2015 Menno Hölscher
#
#    This file is part of gledger.

#    gledger is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    gledger is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.

#    You should have received a copy of the GNU Lesser General Public License
#    along with gledger.  If not, see <http://www.gnu.org/licenses/>.

""" In this module we find the year end related items of
the models. It is about constructing the journal that will take care of 
starting the new year with expense and income accounts zeroised and
profit taken to the balance sheet.
"""

import logging
from datetime import date, datetime, timedelta
from dateutils import relativedelta
from sqlalchemy import desc
from sqlalchemy.orm import validates
from sqlalchemy.orm.exc import NoResultFound
from gledger import db
from glmodels import PaginatorMixin
from glmodels.glaccount import Accounts, CloseDates, Postmonths


class YearEndJournal(dict):

    def __init__(self, start_next_year=None):

        last_close = db.session.query(CloseDates).\
            order_by(desc(CloseDates.closing_date)).first()
        if start_next_year:
            if start_next_year > datetime.now():
                raise ValueError("Can not close year in future")
            if last_close\
                and start_next_year > last_close.closing_date\
                    + relativedelta(years=1):
                raise ValueError("Should not close more than a year after last")
            self.start_next_year = start_next_year
        else:
            if last_close:
                self.start_next_year = last_close.closing_date + relativedelta(years=1)
            else:
                raise ValueError('No previous closing date: pass one')
        self._check_postmonths_closed(self.start_next_year)
        profit_loss_accounts = type(self).get_applicable_accounts()
        postings = list()
        for account in profit_loss_accounts:
            postings.append(self.posting_dict_for(account))
        self["journal"] = {"function": "insert", "postings": postings }

    @classmethod
    def get_applicable_accounts(cls):
        """ Get all profit and loss accounts having a balance at the time
        of closing the year.
        
        This routine just returns the accounts, contains no further 
        processing
        TODO Make the query a responsibility of Accounts!
        """

        return db.session.query(Accounts).filter(Accounts.role.in_(['I', 'E'])).all()

    def _check_postmonths_closed(self, start_next_year):
        """ Check that all postmonths are CloseDates

        The postmonths that should be closed are the ones prior to the 
        start_next_year
        """

        last_year = start_next_year - relativedelta(years=1)
        pmlist = Postmonths.get_postmonths_between_dates(last_year,
                                                         start_next_year,
                                                         monthstat='a')
        if len(pmlist) > 0:
            raise ValueError('Postmonth(s) have not been closed')

    def posting_dict_for(self, account):
        """ Create a dictionary for a posting nullifying balance on account
        """

        posting = dict()
        posting['account'] = account.name
        posting['currency'] = 'EUR'
        posting['amount'] = -1 * account.current_balance()
        posting['debitcredit'] = account.debit_credit()
        posting['valuedate'] = self.start_next_year.strftime('%Y-%m-%d')
        return posting
