from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ArvalChecklistLine(models.Model):
    _inherit="checklist.line"
    
    report_block = fields.Char(string="Report Block")

    is_result = fields.Boolean(string="Result")
    
class ArvalChecklist(models.Model):
    _inherit = "checklist.checklist"
    
    check_hub = fields.Boolean(
        string="Controlla assegnazione piazzalista",
        default=False
    )
    
    @api.constrains('ref_doc_id')
    def _assign_user(self):
        """
        se check_hub assegna l'utente corrispondente
        """
        for record in self:
            if record.check_hub and record.ref_doc_id:
                try:
                    original = record.ref_doc_id.pickup_address
                except:
                    continue
                res = self.env['fleet.location'].search([
                    ('pickup_address','=',original.id)
                ])
                if res:
                    if res[0].assign_to:
                        record.user_id = res[0].assign_to.id
                        record.ready()