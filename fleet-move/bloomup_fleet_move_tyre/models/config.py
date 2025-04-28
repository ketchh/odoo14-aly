from odoo import api, fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    api_addr = fields.Char(string="URL API Pneumatici", config_parameter="bloomup_fleet_move_tyre.api_addr")
    api_key = fields.Char(string="Key API Pneumatici", config_parameter="bloomup_fleet_move_tyre.api_key")


    #fields used to avoid timeout during tire sync
    api_seq = fields.Integer(config_parameter="bloomup_fleet_move_tyre.api_seq", default=0)
    api_slice = fields.Integer(config_parameter="bloomup_fleet_move_tyre.api_slice", default=200)