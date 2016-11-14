Journals - Postings and journals
================================

Postings can only be added to the GL system by supplying Journals. Journals are lists of postings that in the end balance, the sum of debit amounts must be equal to the sum of credit amounts.

The journal has some properties of itself, see :ref:`journals`

Postings
--------

Each posting applies an amount to the account in the posting, for the posting month mentioned. We refer to that as processing the posting. Each posting in the journal is for the same month. 

.. _journals:

Journals
--------

Journals are lists of postings where the total of debit amounts and credit amounts is equal. The individual amounts don't need to be equal. For example sales may be counterposted by a combination of decreasing the value of stocks and increasing taxes to be paid.

Processing of the postings is done by journal. The journal contains a flag whether it is successfully processed. As all postings are processed in journals that balance, it is guaranteed that the ledger balances. If a journal does not balance, or there is another error in the journal, it is not processed. Either a corrected version will be sent by the system that delivered it and the offending journal will remain as "unposted", or the journal will be repaired by the system that delivered it and it will then be processed. A repair message for a journal that was successfully processed, will be ignored and will remain as "unposted".

Example of a Journal
--------------------

The example below will contain all possible fields. Fields that are mandatory, will be marked with an asterisk, that is not part of the definition.
