from odoo import _, api, fields, models
import datetime

class ChooseCarrier(models.TransientModel):
    _name = "choose.carrier"
    _description = "Transient model to find and choose carrier"
    
    fleet_move_id = fields.Many2one(
        string="Fleet Move",
        comodel_name="fleet.move"
    )
    suggested_date = fields.Date(
        string="Suggested date"
    )
    carrier_capacity_ids = fields.Many2many(
        string="Capacities",
        comodel_name="carrier.capacity"
    )
    chosen_cacapacity = fields.Many2one(
        string="Chosen Capacity",
        comodel_name="carrier.capacity"
    )
    alert = fields.Boolean(
        string="Alert",
        default=False,
        compute="_compute_alert"
    )
    
    @api.depends('suggested_date')
    def _compute_alert(self):
        for record in self:
            record.alert=False
            curr = record.fleet_move_id._date_by_adding_business_days(datetime.date.today())
            if record.suggested_date < curr:
                record.alert = True
    
    @api.onchange('suggested_date')
    def _get_capacities(self):
        if self.fleet_move_id:
            capacities = self.fleet_move_id._find_available_capacities(
                from_state_id=self.fleet_move_id.pickup_address.state_id,
                # to_state_id=self.fleet_move_id.delivery_address.state_id,
                date_start=self.suggested_date
            )
            if capacities:
                self.carrier_capacity_ids = [(6,0,capacities.ids)]
            else:
                self.carrier_capacity_ids = False
    
    def next_capacities(self):
        self.ensure_one()
        if self.suggested_date:
            capacities = self.fleet_move_id._find_available_capacities(
                from_state_id=self.fleet_move_id.pickup_address.state_id,
                # to_state_id=self.fleet_move_id.delivery_address.state_id,
                date_start=self.suggested_date,
                _next=True
            )
            if capacities:
                self.suggested_date = capacities[0].date
                self._get_capacities()
                return {
                    'type': 'ir.actions.act_window',      
                    'res_model': 'choose.carrier', 
                    'res_id': self.id, 
                    'view_type': 'form',      
                    'view_mode': 'form',    
                    'target': 'new',     
                } 
            return {
                    'type': 'ir.actions.act_window',      
                    'res_model': 'choose.carrier', 
                    'res_id': self.id, 
                    'view_type': 'form',      
                    'view_mode': 'form',    
                    'target': 'new',     
                } 
    
    def prev_capacities(self):
        self.ensure_one()
        if self.suggested_date:
            capacities = self.fleet_move_id._find_available_capacities(
                from_state_id=self.fleet_move_id.pickup_address.state_id,
                # to_state_id=self.fleet_move_id.delivery_address.state_id,
                date_start=self.suggested_date,
                _prev=True
            )
            if capacities:
                self.suggested_date = capacities[0].date
                self._get_capacities()
                return {
                    'type': 'ir.actions.act_window',      
                    'res_model': 'choose.carrier', 
                    'res_id': self.id, 
                    'view_type': 'form',      
                    'view_mode': 'form',    
                    'target': 'new',     
                } 
            return {
                    'type': 'ir.actions.act_window',      
                    'res_model': 'choose.carrier', 
                    'res_id': self.id, 
                    'view_type': 'form',      
                    'view_mode': 'form',    
                    'target': 'new',     
                } 