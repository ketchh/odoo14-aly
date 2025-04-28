from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class VehicleExtension(models.Model):
    _inherit = "res.partner"
    
    tyre_team_id = fields.Char(string="Identificativo TyreTeam", default="1")