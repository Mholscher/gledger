#    gledger is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    gledger is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.

#    You should have received a copy of the GNU Lesser General Public License
#    along with gledger.  If not, see <http://www.gnu.org/licenses/>.

""" The module contains the views associated with the journal and posting
entities. These views contain a reference to the posting or journal and can
supply the data contained in a human readable form. Everything is stringified
here. Fields that designate other domain objects are expanded to contain a
user readable string. This includes setting up fields like extkey, which is a
human readable key to a journal, supplied by the source system of the journal.
"""

import glmodels.glaccount as accounts
import glmodels.glposting as posts
from glmodels import PaginatorMixin

class PostingView():
    """ The data from a posting, worked out to be in the format for the user
    interface.

    We start with the domain object and convert it to a way favourable to
    showing to the screen on request.
    """

    def __init__(self, posting_id=None):

        if posting_id is None:
            raise posts.NoJournalError('A posting is required to create a view')
        else:
            self.posting = posts.Postings.get_by_id(posting_id)

    def _accountname_for_posting(self):
        """ Get the account name this posting should be applied to """

        return accounts.Accounts.get_by_id(self.posting.accounts_id).name

    def as_dict(self):
        """ Return a dictionary for the posting in this view.
        """

        posting_dict = {'id' : self.posting.id, 'postmonth' :
                            accounts.Postmonths.external(self.posting.postmonth),
                        'amount' : "{0:.2f}".format(self.posting.amount / 100),
                        'currency' : self.posting.currency,
                        'debcred' : self.posting.debcred}
        posting_dict['account'] = self._accountname_for_posting()
        posting_dict['extkey'] = posts.Journals.get_by_id(self.posting.journals_id).extkey

        return posting_dict

class JournalView():
    """ A journal is prepared for showing on a page.

    We start with the domain object and convert it to a way favourable to
    showing on request.
    """

    def __init__(self, journal_id=None, journal_key=None):

        if journal_id is None and journal_key is None:
            raise NoJournalError('A valid journal is required to create a JournalView')
        if journal_id:
            self.journal = posts.Journals.get_by_id(journal_id)
        else:
            self.journal = posts.Journals.get_by_key(journal_key)
        self.postingviews = self.createpostingviews_for_journal(journal_id=self.journal.id)

    def createpostingviews_for_journal(self, postings=None,\
                                journal_id=None, extkey=None):
        """ Create a postingview for each of the postings
        in the journal with the id or extkey entered.
        """

        if postings is None:
            if journal_id:
                postings = posts.Journals.postings_for_id(journal_id)
            else:
                postings = posts.Journals.postings_for_key(extkey)
        postingviews = []
        for posting in postings:
            postingviews.append(PostingView(posting.id).as_dict())
        return postingviews

    def as_dict(self):
        """ Return the journal as a dictionary. 

        The data of the journal are directly encoded, a dictionary for 
        the postingviews is added.
        """

        journ = self.journal
        journal_dict = {"id":journ.id, "extkey":journ.extkey,
                        "status": journ.journalstat}
        journal_dict['postings'] =\
            self.createpostingviews_for_journal(journal_id=self.journal.id)
        return journal_dict


class PostingByAccountView(PaginatorMixin):
    """ The view holds the data of a list of postings by account."""

    def __init__(self, account=None, month=None, page=1):

        if account is None:
            raise accounts.NoAccountError('An account is required')
        self.account = account
        self.postings = posts.Postings.postings_for_account(account,\
            month=month, page=page)
        super().__init__(page=self.postings.page,\
            pagelength=self.postings.pagelength)
        self.num_records = self.postings.num_records
        self.total_pages = self.num_pages()
        
    def num_recs(self):

        return self.num_records

    def as_dict(self):
        """ Return this views data as a dictionary - easy
        access for showing field values on the browser.
        """
        acc = self.account
        posting_dict = {'id' : acc.id, 'name' : acc.name, 'role' : acc.role}
        posting_list = []
        for posting in self.postings:
            posting_list.append(PostingView(posting.id).as_dict())
        posting_dict['postings'] = posting_list
        if self.page is not None:
            posting_dict['page'] = self.page
        if self.pagelength is not None:
            posting_dict['pagelength'] = self.pagelength
        if self.total_pages is not None:
            posting_dict['total_pages'] = self.total_pages
        return posting_dict

class JournalListView(PaginatorMixin, list):
    """ This class holds the extract for a journallist 
    for showing on a page
    
    TODO set up as a "real" paginated view
    """

    def __init__(self, journal_list, page=1, pagelength=25):

        for journal in journal_list:
            self.append({'extkey':journal.extkey, 'updated_at':journal.updated_at})
        #super().__init__(page=journal_list.page,\
            #pagelength=journal_list.pagelength)
        self.page = journal_list.page
        self.pagelength = journal_list.pagelength
        self.total_pages, remainder =\
            divmod(journal_list.num_records, self.pagelength)
        if remainder > 0:
            self.total_pages += 1
