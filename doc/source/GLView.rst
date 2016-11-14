GLViews - the General Ledger views
==================================

The GLViews contains the conversions for the display of data. All items are converted to strings and added to a dictionary with a key that enables the views to easily get to the data. This is based on the way Jinja2 uses data.

Also in his module we find the forms for submitting changes to the system. This is for use with HTML forms

Accountsview
------------

The accountsview returns the data from a GL account. Creating an accountsview taps the underlying Accounts instance for the data, calling asDictionary() creates a Dictionary containing the data with fieldnames as the key. The view does not contain any code to keep itself up to date if the underlying data changes. It is advised to re-create the view when the view needs to be produced again. 

Accountform
------------

To update and show the account data.
