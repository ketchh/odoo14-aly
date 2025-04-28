# The `TransactionCaseCarrierCapacity` class is a test case that tests the
# functionality of rules and access lists in an Odoo application.
import logging
from odoo.tests import tagged
from odoo.tests.common import Form, TransactionCase
from odoo import fields, api, SUPERUSER_ID
from odoo.exceptions import ValidationError, AccessError
from odoo.tools import mute_logger
from odoo.tests.common import new_test_user
_test_logger = logging.getLogger('odoo.tests')

class TransactionCaseCarrierCapacity(TransactionCase):
    
    def setUp(self):
        """
        The setUp function is used to set up test users with different roles and
        groups.
        """
        super(TransactionCaseCarrierCapacity, self).setUp()
        self.carrier1 = new_test_user(
            self.env, 
            'carrier1', 
            groups='bloomup_fleet_move_planner.group_carrier_planner'
        )
        self.carrier2 = new_test_user(
            self.env, 
            'carrier2', 
            groups='bloomup_fleet_move_planner.group_carrier_planner'
        )
        self.carrier_manager = new_test_user(
            self.env, 
            'carrier_manager', 
            groups='bloomup_fleet_move_planner.group_carrier_manager_planner'
        )
        self.user_a = new_test_user(
            self.env, 
            'user_a', 
            groups='base.group_user'
        )
        
    
    def test_rules(self):
        """
        The function `test_rules` tests various rules and constraints related to
        carrier capacities and user access.
        """
        
        # controllo constrains user_ids company_carrier
        self.assertTrue(
            self.carrier1.partner_id.company_carrier
        )
        self.assertTrue(
            self.carrier2.partner_id.company_carrier
        )
        self.assertFalse(
            self.carrier_manager.partner_id.company_carrier
        )
        self.assertFalse(
            self.user_a.partner_id.company_carrier
        )
        
        # creazione capacity
        capacity_carrier1 = self.env['carrier.capacity'].with_user(self.carrier1).create({
            'date':'2023-07-23',
            'from_state_id':self.env.ref('base.state_it_tr').id,
            'to_state_id':self.env.ref('base.state_it_tr').id,
            'max_deliveries': 2,
        })
        capacity_carrier2 = self.env['carrier.capacity'].with_user(self.carrier2).create({
            'date':'2023-07-23',
            'from_state_id':self.env.ref('base.state_it_tr').id,
            'to_state_id':self.env.ref('base.state_it_tr').id,
            'max_deliveries': 2,
        })
        
        # controllo assegnazione partner
        self.assertEqual(
            capacity_carrier1.partner_id.id,
            self.carrier1.partner_id.id
        )
        self.assertEqual(
            capacity_carrier2.partner_id.id,
            self.carrier2.partner_id.id
        )
        
        # controllo la visibilità delle capacità
        results_carrier1 = self.env['carrier.capacity'].with_user(self.carrier1).search([])
        results_carrier2 = self.env['carrier.capacity'].with_user(self.carrier2).search([])
        results_carrier_manager = self.env['carrier.capacity'].with_user(self.carrier_manager).search([])
        _test_logger.info('********* %s' % results_carrier_manager)
        self.assertEqual(
            len(results_carrier1),
            1
        )
        self.assertEqual(
            len(results_carrier2),
            1
        )
        self.assertEqual(
            len(results_carrier_manager),
            2
        )
        
        # ogni utente vede solo le sue
        self.assertEqual(
            results_carrier1.mapped('partner_id'),
            self.carrier1.partner_id
        )
        self.assertEqual(
            results_carrier2.mapped('partner_id'),
            self.carrier2.partner_id
        )
        # controllo che un utente normale non acceda alle capacity
        with self.assertRaises(AccessError):
            results_user_a = self.env['carrier.capacity'].with_user(self.user_a).search([])
        