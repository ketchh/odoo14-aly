# The above class is a test case for the carrier capacity functionality in Odoo.
import logging
from odoo.tests import tagged
from odoo.tests.common import Form, TransactionCase
from odoo import fields, api, SUPERUSER_ID
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger
from odoo.tests import tagged

_test_logger = logging.getLogger('odoo.tests')

class TransactionCaseCarrierCapacity(TransactionCase):
    
    def test_carrier_capacity(self):
        """
        The function `test_carrier_capacity` tests the functionality of assigning
        carrier capacity and fleet moves in a transportation management system.
        """
        # creazione vettore
        carrier = self.env['res.partner'].create({
            'name': 'Test carrier',
            'company_type': 'company'
        })
        carrier.company_carrier = True
        
        carrier2 = self.env['res.partner'].create({
            'name': 'Test carrier 2',
            'company_type': 'company'
        })
        carrier2.company_carrier = True
        
        # creazione capacity
        capacity = self.env['carrier.capacity'].create({
            'partner_id':carrier.id,
            'date':'2023-07-23',
            'from_state_id':self.env.ref('base.state_it_tr').id,
            'to_state_id':self.env.ref('base.state_it_tr').id,
            'max_deliveries': 2,
        })
        # controlla la funzione default del country
        self.assertEqual(
            capacity.country_id,
            self.env.ref('base.it'),
            "Errore default country_id"
        )
        # consttrollo il calolo dei rimanenti
        self.assertEqual(
            capacity.remaining_deliveries,
            2,
            'Errore nel calcolo delle consegne rimanenti start'
        )
        
        # creazione fleet moves
        move1 = self.env['fleet.move'].create({})
        move2 = self.env['fleet.move'].create({})
        move3 = self.env['fleet.move'].create({})
        
        # assegno le moves
        capacity.fleet_move_ids = [(4,move1.id,0)] 
        
        self.assertEqual(
            capacity.remaining_deliveries,
            1,
            'Errore nel calcolo delle consegne rimanenti'
        )
        self.assertEqual(
            move1.confirmed_date.date(),
            capacity.date,
            'Errore assegnazione data conferma'
        )
        
        #move2.carrier_capacity_id = capacity.id 
        capacity.fleet_move_ids = [(4,move2.id,0)]
        
        self.assertEqual(
            capacity.remaining_deliveries,
            0,
            'Errore nel calcolo delle consegne rimanenti'
        )
        # verifico che non posso più modificare max deliveries
        with self.assertRaises(ValidationError):
            capacity.max_deliveries = 1
        # verifico che non posso assegnare più incarichi del dovuto
        with self.assertRaises(ValidationError):
            capacity.fleet_move_ids = [(4,move3.id,0)]
        # verifico l'eccezione nell'assegnazione inversa della capacità
        with self.assertRaises(ValidationError):
            move3.carrier_capacity_id = capacity.id
            
        capacity_carrier1 = self.env['carrier.capacity'].create({
            'partner_id':carrier.id,
            'date':'2023-09-04',
            'from_state_id':self.env.ref('base.state_it_tr').id,
            'to_state_id':self.env.ref('base.state_it_tr').id,
            'max_deliveries': 1,
        })
        capacity_carrier1_2 = self.env['carrier.capacity'].create({
            'partner_id':carrier.id,
            'date':'2023-09-08',
            'from_state_id':self.env.ref('base.state_it_tr').id,
            'to_state_id':self.env.ref('base.state_it_tr').id,
            'max_deliveries': 3,
        })
        
        with self.assertRaises(ValidationError):
            test_capacity_carrier1 = self.env['carrier.capacity'].create({
                'partner_id':carrier.id,
                'date':'2023-09-04',
                'from_state_id':self.env.ref('base.state_it_tr').id,
                'max_deliveries': 1,
            })
        
        test_same_day_capacity_carrier1 = self.env['carrier.capacity'].create({
                'partner_id':carrier.id,
                'date':'2023-09-04',
                'from_state_id':self.env.ref('base.state_it_mi').id,
                'max_deliveries': 1,
            })
        
        capacity_carrier2 = self.env['carrier.capacity'].create({
            'partner_id':carrier2.id,
            'date':'2023-09-04',
            'from_state_id':self.env.ref('base.state_it_tr').id,
            'to_state_id':self.env.ref('base.state_it_tr').id,
            'max_deliveries': 3,
        })
        capacity_carrier2_2 = self.env['carrier.capacity'].create({
            'partner_id':carrier2.id,
            'date':'2023-09-05',
            'from_state_id':self.env.ref('base.state_it_tr').id,
            'to_state_id':self.env.ref('base.state_it_tr').id,
            'max_deliveries': 5,
        })
        
        capacities = self.env['fleet.move']._find_available_capacities(
            from_state_id=self.env.ref('base.state_it_tr'),
            #to_state_id=self.env.ref('base.state_it_tr'),
            date_start="2023-08-25"
        )
        _test_logger.info('**** CAPACITIES: %s' % capacities)
        for capacity in capacities:
            _test_logger.info('**** %s (%s) [%s-%s] max:%s remaining:%s ' % (
                capacity.partner_id.display_name, 
                capacity.date, 
                capacity.from_state_id.code, 
                #capacity.to_state_id.code, 
                capacity.max_deliveries, 
                capacity.remaining_deliveries
            ))