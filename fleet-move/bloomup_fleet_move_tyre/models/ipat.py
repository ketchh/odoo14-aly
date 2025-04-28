from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class Ipat(models.Model):
    _inherit = "bloomup.ipat"
    
    def search_record(self, data=False):
        """
        when ipat found a tyre.repair record, set its field 'found' to True
        """
        result = super(Ipat, self).search_record(data=data)
        if self.model and self.model.id == self.env.ref('bloomup_fleet_move_tyre.model_tyre_repairer').id:
            result.write({'found': True})
        return result
    
    def start_import(self):
        """
        - set found False for all tyre.repairer records
        - import
        - search_record()
        - deactivate tyre.repairer record with found = False
        """
        for record in self:
            # 1) set found: false to all tyre.repairer records
            if record.model and record.model.id == self.env.ref('bloomup_fleet_move_tyre.model_tyre_repairer').id:
                results = self.env['tyre.repairer'].search([])
                results.write({'found':False})
        # 2) start import
        res = super(Ipat, self).start_import()
        # 3) deactivate tyre.repairer records with found = false
        for record in self:
            if record.model and record.model.id == self.env.ref('bloomup_fleet_move_tyre.model_tyre_repairer').id:
                results = self.env['tyre.repairer'].search([('found','=',False)])
                results.write({'active': False})
        return res