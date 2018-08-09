GLViews - the General Ledger views
==================================

The GLViews contains the conversions for the display of data. All items are converted to strings and added to a dictionary with a key that enables the views to easily get to the data. This is based on the way Jinja2 uses data.

Also in his module we find the forms for submitting changes to the system. This is for use with HTML forms

Accountsview
------------

The accountsview returns the data from a GL account. Creating an accountsview taps the underlying Accounts instance for the data, calling asDictionary() creates a Dictionary containing the data with fieldnames as the key. The view does not contain any code to keep itself up to date if the underlying data changes. It is advised to re-create the view when the view needs to be produced again. 

AccountListview
---------------

This view is a dictionary which as its values hold an unspecified number of accounts. Each account is held as a dictionary of the fields of the account. It is used to display any list of accounts; it holds no indication of how the list was compiled.

Balanceview
-----------

The Balance view returns the balance data for an account. It can return the data for any posting month requested, it always tells the balance at ultimo, unless you are looking at the current month. It is than returning the current balance.

Accountform
------------

To update and show the account data.

NewAccountform
---------------

To create a new account.
