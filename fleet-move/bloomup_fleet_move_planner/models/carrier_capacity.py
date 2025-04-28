# The above code defines two models, "CarrierCapacity" and "FleetMoveCarrier", for
# managing the daily capacity of a carrier and assigning deliveries to carriers
# respectively.
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError    
import logging
import datetime
import holidays

_logger = logging.getLogger(__name__)

ADD_DAYS = 5

# suggested date in onchange mostra tutte le capacità ordinate per regole di ingaggio
# bottone prossima disponibilità, precedente disponibilità

# The `CarrierCapacity` class represents the capacity of a carrier to handle
# deliveries, including the maximum number of deliveries, remaining deliveries,
# and related information.
class CarrierCapacity(models.Model):
    _name = "carrier.capacity"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Carrier capacity"
        
    partner_id = fields.Many2one(
        string="Carrier",
        domain=[('company_carrier','=',True)],
        comodel_name="res.partner",
        tracking=True,
        default=lambda self: self.env.user.partner_id.id
    )
    date = fields.Date(
        string="Date",
        tracking=True
    )
    country_id=fields.Many2one(
        string="Country",
        comodel_name="res.country",
        default=lambda self: self.env.ref('base.it').id
    )
    from_state_id = fields.Many2one(
        string="State from",
        comodel_name="res.country.state",
        tracking=True
    )
    to_state_id = fields.Many2one(
        string="State to",
        comodel_name="res.country.state",
        tracking=True
    )
    max_deliveries = fields.Integer(
        string="Max Deliveries",
        default=0,
        tracking=True
    )
    remaining_deliveries = fields.Integer(
        string="Remaining Deliveries",
        compute="_compute_remaining_delivery",
        store=True,
        tracking=True
    )
    fleet_move_ids = fields.One2many(
        string="Deliveries",
        comodel_name="fleet.move",
        inverse_name="carrier_capacity_id"
    )
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee",
        tracking=True
    )
    
    @api.constrains('date','partner_id', 'from_state_id')
    def _check_unique(self):
        for record in self:
            if record.partner_id and record.date and record.from_state_id:
                domain = [
                    ('partner_id','=',record.partner_id.id),
                    ('date','=', record.date),
                    ('from_state_id','=', record.from_state_id.id),
                    ('id','!=',record.id)
                ]
                res = self.env['carrier.capacity'].search(domain)
                if res:
                    raise ValidationError(_('There is already a capacity to this day with this carrier and this "from_state_id".'))
    
    @api.depends('max_deliveries', 'fleet_move_ids')
    def _compute_remaining_delivery(self):
        """
        The function calculates the remaining delivery capacity by subtracting the
        number of assigned tasks from the maximum delivery capacity.
                
        tested
        """
        for record in self:
            record.remaining_deliveries = record.max_deliveries - len(record.fleet_move_ids)
    
    @api.constrains('fleet_move_ids')
    def _constrains_fleet_move_ids_check_availability(self):
        """
        The function checks if there are any more deliveries available and raises an
        exception if there are not.
        
        tested
        """
        for record in self:
            if record.max_deliveries - len(record.fleet_move_ids) < 0:
                raise ValidationError(_('No more deliveries available.'))
    
    @api.constrains('max_deliveries')
    def _constrains_max_deliveries_check_fleet_moves(self):
        """
        The function checks if the new maximum capacity is lower than the number of
        deliveries already assigned and raises an exception if it is.
                
        tested
        """
        for record in self:
            if record.max_deliveries < len(record.fleet_move_ids):
                raise ValidationError(_('There are more deliveries than the maximum availability set.'))
    
    def open_form(self):
        """
        The function "open_form" returns a dictionary with information about opening
        a form view.
        :return: The code is returning a dictionary with the following key-value
        pairs:
        - 'type': 'ir.actions.act_window'
        - 'name': the display name of the object
        - 'view_type': 'form'
        - 'view_mode': 'form'
        - 'res_model': 'carrier.capacity'
        - 'res_id': the id of the current object
        - 'target': 'current'
        """
        return {
            'type': 'ir.actions.act_window',
            'name': '%s' % self.display_name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'carrier.capacity',
            'res_id': self.id,
            'target': 'current',
        }
    
    def name_get(self):
        """
        The function `name_get` returns a list of tuples containing the ID and a
        formatted name for each record in the given object.
        :return: a list of tuples. Each tuple contains two elements: the record's ID
        and a string representation of the record's name, partner ID, from state
        code, to state code, and date.
        """
        result = []
        for record in self:
            name = '%s [%s -> %s] %s' % (
                record.partner_id.name,
                record.from_state_id.code,
                record.to_state_id.code,
                record.with_context(self.env.context).date
            ) 
            
            result.append((record.id, name))
        return result

    def assign_capacity(self):
        self.ensure_one()
        if self.env.context.get('fleet_move_id'):
            self.fleet_move_ids = [(4,self.env.context.get('fleet_move_id'),0)]
            if self.employee_id:
                fm = self.env['fleet.move'].browse(self.env.context.get('fleet_move_id'))
                fm.write({'employee_id':self.employee_id.id})

# The `FleetMoveCarrier` class is an inherited model that adds additional fields
# and a constraint to the `fleet.move` model in order to assign carrier capacity
# and validate remaining deliveries.
class FleetMoveCarrier(models.Model):
    _inherit = "fleet.move"
    
    carrier_capacity_id = fields.Many2one(
        string="Carrier Capacity",
        comodel_name="carrier.capacity",
        tracking=True
    )
    carrier_id = fields.Many2one(
        string="Carrier",
        comodel_name="res.partner",
        related="carrier_capacity_id.partner_id"
    )
    suggested_date = fields.Date(
        string="Suggested Date",
        tracking=True
    )
    
    @api.constrains('carrier_capacity_id')
    def _constrains_capacity_id_get_data(self):
        """ 
        The function assigns the confirmed date when a carrier capacity is assigned,
        and raises a validation error if the remaining deliveries is 0.
        
        tested
        """
        for record in self:
            if record.carrier_capacity_id:
                if record.carrier_capacity_id.remaining_deliveries <0:
                    raise ValidationError(_("You can't assign capacity. Remaining deliveries is 0."))
                record.confirmed_date = record.carrier_capacity_id.date
    
    @api.model
    #def _find_available_capacities(self, from_state_id=False, to_state_id=False, date_start=False, _next=False, _prev=False):
    def _find_available_capacities(self, from_state_id=False, date_start=False, _next=False, _prev=False):
        """
        The function `_find_available_capacities` searches for available carrier
        capacities based on certain criteria.
        
        :param from_state_id: The `from_state_id` parameter is used to filter the
        carrier capacities based on the state from which the delivery is being made.
        It should be an object of the `from_state_id` model, defaults to False
        (optional)
        :param date_start: The date from which you want to find available
        capacities, defaults to False (optional)
        :param _next: The `_next` parameter is a boolean flag that indicates whether
        you want to find the next available capacity after a given date. If `_next`
        is set to `True`, the function will search for capacities with a date
        greater than the provided `date_start`, defaults to False (optional)
        :param _prev: The `_prev` parameter is a boolean flag that indicates whether
        to find capacities with a date earlier than `date_start`. If `_prev` is set
        to `True`, the function will search for capacities with a date earlier than
        `date_start`, defaults to False (optional)
        :return: a list of carrier capacities that meet the specified conditions.
        """
        if not from_state_id or not date_start:
            return []
        limit = 999
        order = 'remaining_deliveries desc'
        domain = [
            ('from_state_id','=',from_state_id.id),
            # ('to_state_id','=',to_state_id.id),
            ('remaining_deliveries','>',0)
        ]
        if _next:
            domain.append(('date','>', date_start))
            limit=1
            order = 'date asc'
        elif _prev:
            domain.append(('date','<', date_start))
            limit=1
            order = 'date desc'
        else:
            domain.append(('date','=',date_start))
        
        capacities = self.env['carrier.capacity'].sudo().search(
            domain,
            order=order,
            limit=limit
        )
        
        return capacities
    
    def find_carrier_capacity(self):
        """
        The function `find_carrier_capacity` checks if all necessary fields are set
        and then finds available capacities based on pickup and delivery addresses
        and a suggested date.
        """
        self.ensure_one()
        record = self
        if not record.pickup_address:
            raise ValidationError(_("No pickup address set."))
        if not record.delivery_address:
            raise ValidationError(_("No delivery address set."))
        if not record.pickup_address.state_id:
            raise ValidationError(_("No state_id ser for pickup address."))
        # if not record.delivery_address.state_id:
        #     raise ValidationError(_("No state_id ser for delivery address."))
        
        # set variables:
        date_start = fields.Date.today()
        from_state_id = record.pickup_address.state_id
        # to_state_id = record.delivery_address.state_id
        if record.suggested_date:
            date_start = record.suggested_date
        else:
            date_start = self._date_by_adding_business_days(datetime.date.today())
        
        capacities = record._find_available_capacities(
            from_state_id=from_state_id,
            # to_state_id=to_state_id,
            date_start=date_start
        ) 
        
        attrs = {
            'fleet_move_id': record.id,
            'suggested_date': date_start,
            'carrier_capacity_ids': [(6,0,capacities.ids)]
        }
        res = self.env['choose.carrier'].create(attrs)
        
        return {
            'type': 'ir.actions.act_window',      
            'res_model': 'choose.carrier', 
            'res_id': res[0].id, 
            'view_type': 'form',      
            'view_mode': 'form',    
            'target': 'new',     
        }
    
    def _date_by_adding_business_days(self, from_date):
        add_days = ADD_DAYS
        business_days_to_add = add_days
        current_date = from_date
        country = "IT"
        if self.pickup_address:
            country = self.pickup_address.country_id.code
        hol = holidays.country_holidays(country, years=datetime.datetime.now().year).items()
        while business_days_to_add > 0:
            current_date += datetime.timedelta(days=1)
            weekday = current_date.weekday()
            if weekday >= 5: # sunday = 6, saturday = 5
                continue
            if current_date in hol:
                continue
            business_days_to_add -= 1
        return current_date