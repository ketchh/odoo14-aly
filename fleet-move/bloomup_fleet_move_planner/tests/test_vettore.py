# The above class is a test case for creating and validating carrier partners in
# Odoo.
import logging
from odoo.tests import tagged
from odoo.tests.common import Form, TransactionCase
from odoo import fields, api, SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger
from odoo.tests import tagged

_test_logger = logging.getLogger('odoo.tests')

# The `TransactionCaseCarrier` class contains test cases for creating and
# validating carriers and their employees in a res.partner model.
class TransactionCaseCarrier(TransactionCase):

    def test_carrier(self):
        """
        The function `test_carrier` tests the creation of a carrier and its child
        employee.
        """
        """ 
        - Test creazione vettore.
        - Test creazione dipendente vettore per un vettore.
        """
        # creazione vettore
        carrier = self.env['res.partner'].create({
            'name': 'Test carrier',
            'company_type': 'company'
        })
        carrier.company_carrier = True
        self.assertTrue(
            carrier.company_carrier,
            "It's not a carrier"
        )
        # creazione dipendente vettore
        carrier.child_ids = [(0,0,{
            'name':'Dipendente vettore',
            'type': 'carrier'
        })]
        self.assertEqual(
            len(carrier.child_ids),
            1,
            "Child not created"
        )
        # verifica dipendente vettore
        self.assertEqual(
            carrier.child_ids[0].type,
            'carrier',
            "Child is not a carrier's employee"
        )
        
    def test_not_carrier(self):
        """
        The function `test_not_carrier` tests that a non-carrier company cannot have
        a carrier employee.
        """
        # creazione azienda normale
        not_carrier = self.env['res.partner'].create({
            'name': 'Test Not carrier',
            'company_carrier': False
        })
        self.assertFalse(
            not_carrier.company_carrier,
            "Company is a carrier"
        )
        # verifica che non posso creare un contatto dipendente vettore 
        # per un res.partner non vettore (company_carrier == False)
        with self.assertRaises(ValidationError), self.cr.savepoint(): 
            not_carrier.child_ids = [(0,0,{
                'name':'Dipendente vettore',
                'type': 'carrier'
            })]
        
    def test_company_carrier_type(self):
        """
        The function tests the behavior of a company carrier type in a res.partner
        model.
        """
        carrier = self.env['res.partner'].create({
            'name': 'Test carrier',
            'company_type': 'person'
        })
        # test company_carrier True se person
        with self.assertRaises(ValidationError), self.cr.savepoint():
            carrier.company_carrier = True
        self.assertFalse(
            carrier.company_carrier,
            "L'azienda è un vettore"
        )
        # company
        carrier.company_type = 'company'
        carrier.company_carrier = True
        self.assertTrue(
            carrier.company_carrier,
            "Non è realmente un vettore"
        )
        # torna a person company_carrier va a false
        carrier.company_type = 'person'
        self.assertFalse(
            carrier.company_carrier,
            "L'azienda è un vettore"
        )
        # torno a company e aggiungo child
        carrier.company_type = 'company'
        carrier.company_carrier = True
        carrier.child_ids = [(0,0,{
            'name':'Dipendente vettore',
            'type': 'carrier'
        })]
        # torna a person company_carrier va a false
        # genera un'eccezione perchè avendo dei contatti carrier
        # non può più tornare a person
        with self.assertRaises(ValidationError), self.cr.savepoint():
            carrier.company_type = 'person'