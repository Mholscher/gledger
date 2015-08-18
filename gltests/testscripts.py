import unittest
import gledger
import glmodels.glaccount as accmodel
from sqlalchemy.exc import DatabaseError
from datetime import date

class TestDBCreation(unittest.TestCase) :
    def setUp(self) :
        pass
    
    def tearDown(self) :
        gledger.db.session.rollback() 
    
    def test_insert(self) :
        """ We can insert an account"""
        acc1 = accmodel.Accounts(name = 'proefbalans', role = 'I')
        acc1.add()
        q = gledger.db.session.query(accmodel.Accounts).filter(accmodel.Accounts.name == 'proefbalans')
        self.assertNotEqual(q.count(), 0, 'No account updated')

    def test_insert_duplicate(self) :
        """ We cannot insert an account twice """
        acc1 = accmodel.Accounts(name = 'proefbalans', role = 'I')
        acc1.add()
        acc2 = accmodel.Accounts(name = 'proefbalans', role = 'I')
        acc2.add()
        with self.assertRaises(DatabaseError) :       
            gledger.db.session.flush()
            
    def test_accounts_related(self) :
        """ We can insert related accounts (parent child)
        """
        acc4 =  accmodel.Accounts(name = 'parent', role = 'I')
        acc4.add()
        acc5 =  accmodel.Accounts(name = 'child', role = 'I')
        acc5.add()
        acc4.children.append(acc5)
        self.assertIn(acc5, acc4.children)
        gledger.db.session.flush()
        self.assertEqual(acc5.parent, acc4.id)
        
    def test_can_add_balance(self) :
        """We can add a balance to an account """
        acc6 = accmodel.Accounts(name='creditors', role='L')
        acc6.add()
        bal1 = accmodel.Balances(postmonth=accmodel.postmonth_for(date.today()), amount=1215, value_date='2015-07-21')
        bal1.add()
        acc6.balances.append(bal1)
        gledger.db.session.flush()
        self.assertEqual(bal1.account_id, acc6.id, 
                         'Balance not attached to account')
        
    def test_insert_postmonth(self) :
        """ We can create a postmonth """
        pm1 = accmodel.Postmonths(postmonth=201507, monthstat = 'a')
        pm1.add()
        gledger.db.session.flush()
        self.assertEqual(pm1.postmonth, 201507, 'Postmonth set incorrect')
        
    def test_invalid_monthstat(self) :
        """ We cannot create a postmonth with invalid status """
        with self.assertRaises(ValueError) :
            pm2 = accmodel.Postmonths(postmonth=201507, monthstat = 'z')

    def test_postmonth_no_state(self) :
        """ We can create a postmonth """
        pm3 = accmodel.Postmonths(postmonth=201507)
        pm3.add()
        with self.assertRaises(DatabaseError) :
            gledger.db.session.flush()
                    
class TestDomainProcesses(unittest.TestCase) :
    
    def tearDown(self) :
        gledger.db.session.rollback() 

    def test_refuse_accttype(self) :
        """ We refuse an invalid account type """        
        with self.assertRaises(ValueError) :       
            acc3 = accmodel.Accounts(name = 'rekening', role = 'C')  
            
    def test_refuse_future_postmonth(self) :
        """ A balance cannot be created for a future postmonth """
        current_postmonth  = accmodel.postmonth_for(date.today())
        with self.assertRaises(ValueError) :
            bal2 = accmodel.Balances(postmonth=current_postmonth + 2, 
                                     amount=1215, value_date='2015-07-21')
            
    def test_convert_date_to_postmonth(self) :
        """ If we get the correct postmonth from a date """
        postdate = date(2015, 1, 26)
        self.assertEqual(201501, accmodel.postmonth_for(postdate), 
                         'Incorrect postmonth from date')
        
    def test_change_account(self) :
        """ Changing account data. """
        acc7 = accmodel.Accounts(role='L', name='creditors')
        acc7.add()
        gledger.db.session.flush()
        acc8 = gledger.db.session.query(accmodel.Accounts).filter(accmodel.Accounts.name == 'creditors').one()
        acc8.role = 'A'
        acc8.add()
        gledger.db.session.flush()
        acc8 = gledger.db.session.query(accmodel.Accounts).filter(accmodel.Accounts.name == 'creditors').one()
        self.assertEqual('A', acc7.role, 'Role not updated after flush')
        
    def test_account_by_id(self) :
        """Getting an account by its sequence """
        acc9 = accmodel.Accounts(role='E', name='salaris')
        acc9.add()
        gledger.db.session.flush()
        accn = gledger.db.session.query(accmodel.Accounts).filter(accmodel.Accounts.name=='salaris').one()
        acci = accmodel.Accounts.get_by_id(accn.id)
        self.assertEqual(accn.id, acci.id, 'id unequal after read') 

    def test_account_by_name(self) :
        """Getting an account by its name """
        acc10 = accmodel.Accounts(role='E', name='bonus')
        acc10.add()
        gledger.db.session.flush()
        accn = gledger.db.session.query(accmodel.Accounts).filter(accmodel.Accounts.name=='bonus').one()
        acci = accmodel.Accounts.get_by_name(accn.name)
        self.assertEqual(accn.name, acci.name, 'name unequal after read') 
        
    def test_current_balance(self) :
        acc11 =  accmodel.Accounts(role='L', name='bankloans')
        acc11.add()
        bal3 = accmodel.Balances(postmonth=accmodel.postmonth_for(date.today()), amount=12.17, value_date='2015-07-21')
        acc11.balances.append(bal3)
        self.assertEqual(acc11.current_balance(), 12.17, 'Balance not correctly read back')
        
    def test_history_balance(self) :
        acc12 =  accmodel.Accounts(role='E', name='officestuff')
        acc12.add()
        add_postmonths([201504, 201506, 201507])
        bal4 = accmodel.Balances(postmonth=201506, amount=17.12, value_date='2015-06-29')
        acc12.balances.append(bal4)
        bal5 = accmodel.Balances(postmonth=201504, amount=17.18, value_date='2015-04-30')
        acc12.balances.append(bal5)
        bal6 = accmodel.Balances(postmonth=201507, amount=17.26, value_date='2015-07-10')
        acc12.balances.append(bal6)
        acc13 =  accmodel.Accounts(role='E', name='purchases')
        acc13.add()
        bal7 = accmodel.Balances(postmonth=201506, amount=17.12, value_date='2015-06-29')
        acc13.balances.append(bal7)
        self.assertEqual(acc12.balance_ultimo(201507), 17.26, 'Balance july not correct')
        self.assertEqual(acc12.balance_ultimo(201506), 17.12, 'Balance june not correct')
        self.assertEqual(acc12.balance_ultimo(201505), 17.18, 'Balance may not correct')       
        self.assertEqual(acc12.balance_ultimo(201502), 0.0, 'Balance february not correct')        

class TestAccountStructures(unittest.TestCase) :
    
    def setUp(self) :
        self.parent = accmodel.Accounts(role='I', name='topaccount')
        self.parent.add()
        self.ch1 = accmodel.Accounts(role='I', name='child1')
        self.ch1.add()
        self.parent.children.append(self.ch1)
        self.ch2 = accmodel.Accounts(role='I', name='child2')
        self.ch2.add()
        self.parent.children.append(self.ch2)
        self.ch3 = accmodel.Accounts(role='I', name='child3')
        self.ch3.add()
        self.parent.children.append(self.ch3)

    def tearDown(self) :
        gledger.db.session.rollback() 
        
    def test_return_childlist(self) :
        """Returning a list of children"""
        self.assertEqual(len(self.parent.children), 3, 'Exactly 3 children should be in list')
        
def add_postmonths(monthlist) :
    """Add the postmonths requested in the list to the session """
    for postmonth in monthlist :
        pm = accmodel.Postmonths(postmonth=postmonth, monthstat='a')
        pm.add()
                    
if __name__ == '__main__':
    unittest.main()
