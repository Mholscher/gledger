GLedger - The application
=========================
    
The GLedger module contains the application level code for the GLedger application.



Views
-----

The views are the transactions that GLedger is able to perform. See the :ref:`gledgerapi` API docs to find out what web transactions are supported.

Posting API
-----------

Programs can submit journals via the posting API. It receives the journals as a JSON message, that contains the full journal.

Also when a Journal is rejected by the API, you can send a "repair"journal that should contain postings to correct the error(s) found.

Some errors cannot be repaired; the journal containing such an error is not put into the database.



