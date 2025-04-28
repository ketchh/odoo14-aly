from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta

class AddonsFleetMoveHistory(models.Model):
    _name = "fleet.move.state.history"
    _description = "History"
    
    fleet_move_id = fields.Many2one(
        string="Movimentazione",
        comodel_name="fleet.move"
    )
    state_id = fields.Many2one(
        string="Fase",
        comodel_name="fleet.move.status"
    )
    days = fields.Integer(
        string="Giorni",
        store=True,
        compute="_compute_days",
        readonly=True
    )
    
    @api.depends('fleet_move_id')
    def _compute_days(self):
        for record in self:
            record.days=0
            start = record.fleet_move_id.create_date
            record.days = (record.create_date - start).days
            
    
class AddonsFleetMove(models.Model):
    _inherit="fleet.move"
    
    history=fields.One2many(
        string="Storia degli stati",
        comodel_name="fleet.move.state.history",
        inverse_name="fleet_move_id"
    )
    
    @api.constrains('state')
    def _constrains_state_history(self):
        for record in self:
            record.history= [
                (0,0,{
                    'state_id': record.state.id
                })
            ]

class FleetMoveStatus(models.Model):
    _inherit = "fleet.move.status"
    
    pronto = fields.Boolean(
        string="Pronto",
        default=False
    )