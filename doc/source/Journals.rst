Journals - Postings and journals
================================

Postings can only be added to the GL system by supplying Journals. Journals are lists of postings that in the end balance, the sum of debit amounts must be equal to the sum of credit amounts.


Example of a Journal
--------------------

The example below will contain all possible fields. Fields that are mandatory, will be marked with an asterisk, that is not part of the definition::

    {"journal"* : 
        {"function"* : "insert",
         "journalno" : "12"
         "extkey"* : "f234",
         "postings"* : 
            [{  "account"* : "verkopen",
                "currency"* : "EUR",
                "amount"* : "23000",
                "debitcredit"* : "Cr",
                "valuedate"* : "2017-01-12"},
            {   "account"* : "kas",
                "currency"* : "EUR",
                "amount"* : "25000",
                "debitcredit"* : "Db",
                "valuedate"* : "2017-01-12"},
            {   "account"* : "btw (ontvangen)",
                "currency"* : "EUR",
                "amount"* : "2000",
                "debitcredit"* : "Cr",
                "valuedate"* : "2017-01-12"}]
            }
    }

The definitions of the fields are as follows:

    journal
        contains the full journal, with all fields pertaining to the journal and the postings are embedded.
        
    function
        what to do with the postings. "insert" will create a new journal, "add" will add the postings to the journal having journalno as its number.
        
    journalno
        in case of an "add", the number of the journal to add the postings to. Ignored for insert.
        
    extkey
        a mandatory key to the journal in the system that generated it. It will be added to the response when adding a journal. It enables finding a journals source and is also a search key within the system. These keys are not required to be unique, but it is advisable to make these unique, so that the source of postings is always traceable. "extkey" stands for "external key". GLedger does not assume anything about these keys, the format is at the discretion of the system that submits a journal. 
        
    postings
        the list of postings for this journal.
        
    account
        The account this posting is to be made to.
        
    currency
        The currency code of the posting. It is recommended to use the SWIFT currency codes
        
    amount
        The amount in the smallest unit of the currency (e.g. cents)
        
    debitcredit
        Debit ('Db') or credit ('Cr') of the posting
        
    valuedate
        The date this posting should be applied

The result of the submission if successful will be the following message::

    {   "status":"OK";
        "message":"Journal f234 added"
    }

If not successful, a message will be sent as follows::

    {   "status":"Not correct";
        "message":"Journal was not balancing";
        "extkey":"f234";
    }

Where the "f234" is the external key passed by the application.

Finding journals by key
-----------------------

If you have the key to a journal and you want to find that journal, the place to look is the journal list. You can ask for a list of journal keys by (part of) a key. All journals that contain the search string as (part of) the key are listed and are clickable to see all postings in the journal.

