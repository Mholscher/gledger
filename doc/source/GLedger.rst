GLedger - The application
=========================
    
GLedger is an application to do General Ledger administration. In a General Ledger there are accounts, where postings are posted to. Together these postings make up a balance.

This documentation will not go into detail about the items in a GL administration. It is about how this is implemented.



Views
-----

The views are the transactions that GLedger is able to perform. See the :ref:`gledgerapi` API docs to find out what web transactions are supported.

As a general rule, these views are web pages to inquire upon the accounts, balance and entries into the ledger. Some entities (notably accounts) can also be changed through the web application.

Posting API
-----------

Systems can submit journals via the posting API. It receives the journals as a JSON message, that contains the full journal. Though these are not meant to be *produced* by a human, the are "human-readable"; when you see one, it will be understandable what it does.

Errors cannot be repaired; the journal containing such an error is not put into the database.



