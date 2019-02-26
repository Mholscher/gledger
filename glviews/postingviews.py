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

class PostingView():
    """ The data from a posting, worked out to be in the format for the user
    interface.

    We start with the domain object and convert it to a way favourable to
    showing to the screen on request.
    """

    def __init__(self, posting=None):

        if not posting or (posting.id is None):
            raise posts.NoJournalError('A posting is required to create a view')
        else:
            self.posting = posting

    def _accountname_for_posting(self):
        """ Get the account name this posting should be applied to """

        return accounts.Accounts.get_by_id(self.posting.accounts_id).name

    def as_dict(self):
        """ Return a dictionary for the posting in this view.
        """

        posting_dict = {'id' : self.posting.id, 'postmonth' :
                            accounts.Postmonths.external(self.posting.postmonth),
                        'amount' : str(self.posting.amount),
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

    def __init__(self, journal=None):

        if journal is None or journal.id is None:
            raise NoJournalError('A valid journal is required to create a JournalView')
        self.journal = journal
        self.postingviews = self.createpostingviews_for_journal(journal_id=journal.id)

    def createpostingviews_for_journal(self, journal_id=None, extkey=None):
        """ Create a postingview for each of the postings
        in the journal with the id or extkey entered.
        """

        if journal_id:
            postings = posts.Journals.postings_for_id(journal_id)
        else:
            postings = posts.Journals.postings_for_key(extkey)
        postingviews = []
        for posting in postings:
            postingviews.append(PostingView(posting).as_dict())
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
