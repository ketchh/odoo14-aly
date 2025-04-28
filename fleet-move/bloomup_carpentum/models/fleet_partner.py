from odoo import _, api, fields, models

class FleetPartnerCarpentum(models.Model):
    _inherit = "fleet.partner"
    
    user_id = fields.Many2one(
        string="Tecnico Riferimento",
        comodel_name="res.users",
        tracking=True
    )