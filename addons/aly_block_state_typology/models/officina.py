from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class TaskTypology(models.Model):
    _inherit = "task.typology"
    
    block_state = fields.Boolean(
        string="Blocca aggiornamento stato",
        default=False
    )