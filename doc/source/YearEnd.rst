.. _yearendprocessing:

Year end processing
===================


Purpose
-------

It is customary to at the end of the accounting year close your books. That means it is made sure that no postings can be made to the books in the year being closed and profit or loss is being taken into the assets and liabilities.

.. _requisites:

The prerequisites
-----------------

Before the year end processing can be executed, some prerequisites are checked.

*   The end of the accounting year is passed (can't close in the future)
*   All accounting months of the year to be closed are closed, so no postings can be done anymore
*   A valid date to close the books is supplied or can be established. It must be the first day of the new accounting year
*   No more than a year has passed since the previous closing

The process of closing the year
-------------------------------

After the checks are made detailed in :ref:`requisites` the process continues to find all balances on profit and loss accounts, type income and expense. These accounts are set to zero through counter posting the balance against an account that contains the profit.

    :account: the account to be posted to zero
    :valuedate: the first date of the new accounting period
    :amount to post: to account, -1 * its balance, to profit the original amount
    :profit account: the account we accumulate the profit
    :debcred: make sure for both postings debcred is set to the correct value!

After the processing is ended, the last date of year end processing is updated. No indication that year end processing has **started** is necessary. Restarting the process will just continue where it left off.

Changing the date of closing
----------------------------

You can pass a date to the script to close at another date. This date must also conform to :ref:`requisites`. This overrides the automatically determined date and changes **all** of the following closing dates to a new yearly schedule.

Automatically establishing the closing date
-------------------------------------------

The closing date that is automatically established is one year from the previous (latest) closing date. Follows that you need to specify a closing date when you close the accounting year for the first time.
