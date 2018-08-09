API documentation
=================

.. _gledgerapi:

Module gledger
--------------

..  module:: gledger.views
    
..  autofunction:: accounts

..  autofunction:: accountList

..  autofunction:: createaccount

..  autofunction:: index

..  autofunction:: balance

..  autofunction:: posts

..  module:: gledger.postingapi

..  autoclass:: InvalidJsonError

..  autofunction:: handle_invalid_json

..  autofunction:: addjournal

Module glmodels
---------------
..  module:: glmodels.glaccount

..  autoclass:: NoAccountError
    :members:

..  autoclass:: AccountAlreadyExistsError
    :members:

..  autoclass:: Accounts
    :members:

..  autoclass:: Balances
    :members:
    
..  autoclass:: AccountList
    :members:
    
..  autoclass:: Postmonths
    :members:

..  autofunction:: postmonth_for(postdate)

..  module:: glmodels.glposting

..  autoclass:: PostingWOJournal
    :members:

..  autoclass:: NoJournalError
    :members:

..  autoclass:: JournalBalanceError
    :members:

..  autoclass:: Journals
    :members:
    
..  autoclass:: Postings
    :members:
    
Module glviews
---------------

..  module:: glviews.accountviews

..  autoclass:: AccountView
    :members:

..  autoclass:: AccountListView
    :members:
    
..  autoclass:: BalanceView
    :members:

..  module:: glviews.forms

..  autoclass:: AccountMustExist
    :members:

..  autoclass:: AccountForm
    :members:
    
..  autoclass:: NewAccountForm
    :members:
    
