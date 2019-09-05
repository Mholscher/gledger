#    Copyright 2018 Menno Hölscher
#
#    This file is part of gledger.

#    gledger is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    gledger is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.

#    You should have received a copy of the GNU Lesser General Public License
#    along with gledger.  If not, see <http://www.gnu.org/licenses/>.

from wtforms import SelectField
from glmodels.glaccount import Postmonths


class SelectPostMonthStatusField(SelectField):
    """ This field extends a selectfield with code making it usable
    to use as a field in a list of postmonth statuses.

    The field is initialized with a custom id and label to distinguish
    between postmonths in the user interface and in the submitted changes.
    """
    
    def __init__(self, label='', validators=None, id='', **kwargs):

        super().__init__(label, validators, id=id, **kwargs)
        self.coerce = str

    def process_data(self, postmonth_tuple):
        """ This creates the value in the form data and updates
        the label string and id for the field
        
        If a label was previously set, the postmonth string is
        added to it at the end. If no label is present, it is
        just the postmonth string.
        
        The id is just replaced with a stringified number; the
        postmonth key is a number.
        """

        super().process_data(postmonth_tuple[1])
        if self.label.text:
            self.label.text = self.label.text +\
                str(Postmonths.external(int(postmonth_tuple[0])))
        else:
            self.label.text = str(Postmonths.external(int(postmonth_tuple[0])))
        self.id = str(postmonth_tuple[0])
        
