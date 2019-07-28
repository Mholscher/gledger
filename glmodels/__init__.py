class PaginatorMixin():
    """ This class holds all info for paginating lists in
    the model.
    
    It is a holder, but can also return some derived data.
    """

    def __init__(self, *args, pagelength=0, page=1, from_month=None, **kwargs):

        super().__init__()
        self.pagelength = pagelength
        self.page = page
        self.from_month = from_month

    def limit(self, q):
        """ Return the query with a limit on returned rows """

        return q.limit(self.pagelength)

    def set_page(self, q):
        """ Return the query starting at this page """

        if self.page == 1:
            return q
        q =  q.offset((self.page - 1) * self.pagelength)
        return q

    def num_pages(self):
        """ Return the number of pages for this list 
        
        For this to work, the object that we are mixing into should
        support returning the number of records in the query without paging
        through the method 'num_recs'
        """

        nr = self.num_recs()
        np =  nr // self.pagelength
        if np * self.pagelength != nr:
            np = np +1
        return np
