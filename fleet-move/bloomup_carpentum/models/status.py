from odoo import _, api, fields, models

class FleetMoveTipi(models.Model):
    _name = "fleet.move.arval.type"
    
    """
    Questo modello serve a identificare i tipi arval
    RIT-DEA
    FASE ZERO
    GATE IN
    sono installati tramite status.xml e non sono modificabili
    """
    
    name = fields.Char(
        string="Name"
    )

class FleetMoveCarpentum(models.Model):
    _inherit = "fleet.move.status"
    
    move_type = fields.Many2many(
        string="Tipologia",
        comodel_name="fleet.move.arval.type"
    )