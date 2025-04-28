from odoo import _, api, fields, models
from odoo.addons.bloomup_owl_components.models.store import AVAILABLE_MODEL
import datetime
from datetime import timedelta
 
class FleetMoveGroup(models.Model):
    """
    Raggruppa movimentazioni o altri eventi (event_ids) 
    per poi riorganizzarli in orari

    name: srt
        il nome che viene assegnato da uan sequenza
    event_ids: one2many -> fleet_move_event
        eventi all'interno dei quali possono esserci o una movimentazione o un testo
    employee_id: many2one -> hr.employee
        vettore a cui è assegnato il gruppo e tutte le movimentazioni del gruppo
    state: sele
        stato del gruppo
    user_id: many2one -> res.users
        utente che può vedere il gruppo (record rule)
    """
    _name = "fleet.move.group"
    _description = "Fleet move Group"
    # TODO: record rule su user_id
    name = fields.Char(string='Name')
    event_ids = fields.One2many(
        comodel_name='fleet.move.event', 
        inverse_name='fleet_group_id', 
        string='Events'
    )
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee"
    )
    state = fields.Selection(
        string="State",
        selection=[
            ('draft', _('Draft')),
            ('done', _('Done'))
        ],
        default='draft'
    )
    user_id = fields.Many2one(
        string="user",
        comodel_name="res.users"
    )

    @api.model
    def create(self, vals):
        """
        Override per assegnare la sequenza al nome 
        e lo stato di default (se esiste un default)
        """
        vals['name'] = self.env['ir.sequence'].sudo().next_by_code('fleet.move.group.sequence')
        return super(FleetMoveGroup, self).create(vals)
    
    @api.model
    def search_group(self):
        """
        Ritorna i gruppi utili al planner
        """
        results = self.with_context(
            {'lang':self.env.user.lang}).search(
                [('state','=','draft')],
                order="id asc"
            )
        groups = []
        for res in results:
            attrs = {
                'id': res.id,
                'name':res.name,
                'employee_id': False,
                'state': res.state,
                'event_ids':[
                   
                ],
                'user_id': False
            }
            for event in res.event_ids:
                if event.fleet_move_id:
                    attrs['event_ids'].append({
                        'event_date': event.event_datetime,
                        'name': event.display_name,
                        'id': event.id,
                        'obj': {
                            'id': event.fleet_move_id.id,
                            'name': event.fleet_move_id.name,
                            'confirmed_date': event.fleet_move_id.confirmed_date,
                            'pickup_address': [
                                event.fleet_move_id.pickup_address.id,
                                "%s, %s %s <b>%s (<span class='text-danger'>%s</span>)</b>" % (
                                    event.fleet_move_id.pickup_address.name,
                                    event.fleet_move_id.pickup_address.street,
                                    event.fleet_move_id.pickup_address.street2,
                                    event.fleet_move_id.pickup_address.city,
                                    event.fleet_move_id.pickup_address.state_id.code)
                            ],
                            'delivery_address': [
                                event.fleet_move_id.delivery_address.id,
                                "%s, %s %s <b>%s (<span class='text-danger'>%s</span>)</b>" % (
                                    event.fleet_move_id.delivery_address.name,
                                    event.fleet_move_id.delivery_address.street,
                                    event.fleet_move_id.delivery_address.street2,
                                    event.fleet_move_id.delivery_address.city, 
                                    event.fleet_move_id.delivery_address.state_id.code)
                            ],
                            'user_id': [event.fleet_move_id.user_id.id, event.fleet_move_id.user_id.name],
                            'vehicle_id': [event.fleet_move_id.user_id.id, event.fleet_move_id.user_id.display_name],
                            'partner_id': [event.fleet_move_id.partner_id.id, event.fleet_move_id.partner_id.name],
                            'bg': 'bg-light'
                        } 
                    })
            
            if res.employee_id:
                attrs['employee_id'] = [res.employee_id.id, res.employee_id.display_name]
            if res.user_id:
                attrs['user_id'] = [res.user_id.id, res.user_id.display_name]
            groups.append(attrs)
        return groups

    @api.constrains('employee_id')
    def _constrains_employee_id(self):
        """
        Aggiorna il vettore di ogni movimentazione
        """
        for event in self.event_ids:
            if event.fleet_move_id:
                event.fleet_move_id.employee_id = self.employee_id.id if self.employee_id else False

    def go_to_calendar(self):
        return {
            'name': _('Calendar Event'),
            'type': 'ir.actions.act_window',
            'view_mode': 'calendar',
            'res_model': 'fleet.move.event',
            'domain': [('fleet_group_id', '=', self.id)]
        }
        
class FleetMoveEvent(models.Model):
    """
    Evento con movimentazione o testo

    name: str
        nome evento
    event_datetime: datetime
        data e ora dell'evento
    fleet_move_id: manu2one -> fleet.move
        se presente l'evento è una movimentazione
    event_type: selection
        movimentazione oppure trasposrto o altro
    fleet_group_id: many2one -> fleet.move.group
        gruppo a cui è assegnato
    """
    _name="fleet.move.event"
    _description="Fleet Move Event"

    name = fields.Char(string='Name') 
    event_datetime = fields.Datetime(string='Date Time')
    event_datetime_end = fields.Datetime(
        string='Date Time end',
    )
    fleet_move_id = fields.Many2one(
        comodel_name='fleet.move', 
        string='Fleet move'
    )
    event_type = fields.Selection(
        string="Type",
        selection=[
            ('fleet_move', _('Fleet move')),
            ('transport', _('Transport'))
        ]
    )
    fleet_group_id = fields.Many2one(
        string="Group",
        comodel_name="fleet.move.group"
    )
    def name_get(self):
        result = []
        for event in self:
            name = event.name
            if event.event_type == 'fleet_move' and event.fleet_move_id:
                res = event.fleet_move_id
                name = "%s (%s) -> %s (%s)" % (
                    res.pickup_address.city, 
                    res.pickup_address.state_id.code,
                    res.delivery_address.city,
                    res.delivery_address.state_id.code
                )
            result.append((event.id, name))
        return result

    @api.constrains('fleet_move_id')
    def _constrains_fleet_move_id(self):
        """
        Quando viene assegnata una movimentazione allora la data dell'evento 
        diventa quella confermata della movimentazione
        """
        if(self.fleet_move_id and self.fleet_move_id.confirmed_date):
            self.event_datetime = self.fleet_move_id.confirmed_date
    
    def unlink(self):
        for record in self:
            if record.fleet_move_id:
                record.fleet_move_id.employee_id = False
        return super(FleetMoveEvent, self).unlink()

    @api.model
    def create(self, vals):
        if vals.get('fleet_group_id'):
            group = self.env['fleet.move.group'].browse(int(vals.get('fleet_group_id')))
            if group.employee_id:
                if vals.get('fleet_move_id'):
                    move = self.env['fleet.move'].browse(int(vals.get('fleet_move_id')))
                    move.employee_id = group.employee_id.id
        res = super(FleetMoveEvent, self).create(vals)
        
        return res

    @api.constrains('event_datetime')
    def _constrains_event_datetime(self):
        if self.event_datetime and not self.event_datetime_end:
            self.event_datetime_end = self.event_datetime + timedelta(hours=1)
        if not self.event_datetime:
            self.event_datetime_end = False

class FleetMove(models.Model):
    """
    Override Richiesta di Movimentazione

    Aggiunti:
    fleet_move_event_ids: one2many -> fleet.move.group
        evento a cui è assegnata la movimentazione (many2one one2many 
        anche se dovrebbe essere una one2one)
    """
    _inherit="fleet.move"

    fleet_move_event_ids = fields.One2many(
        comodel_name='fleet.move.event', 
        inverse_name='fleet_move_id', 
        string='Events')
    
    
    
    @api.model
    def search_planner(self, date=False):
        """
        Funzione di ritorno dei dati delle movimentazioni
        """
        
        if not date:
            date = datetime.datetime.now()
        else:
            date = datetime.datetime.strptime(date, '%Y-%m-%d')
        date_start = date.strftime('%Y-%m-%d') + ' 00:00:00'
        date_end = date.strftime('%Y-%m-%d') + ' 23:59:59'
        # la data è quella confermata
        domain = [
            ('fleet_move_event_ids', '=', False),
            ('state.planner_visible', '=', True),
            ('confirmed_date', '>=', date_start),
            ('confirmed_date', '<=', date_end)
        ]
        results = self.with_context({'lang':self.env.user.lang}).search(domain)
        records = []
        for res in results:
            records.append({
                'id': res.id,
                'name': res.name,
                'confirmed_date': res.confirmed_date,
                'pickup_address': [
                    res.pickup_address.id,
                    "%s, %s %s <b>%s (<span class='text-danger'>%s</span>)</b>" % (
                        res.pickup_address.name,
                        res.pickup_address.street,
                        res.pickup_address.street2,
                        res.pickup_address.city,
                        res.pickup_address.state_id.code)
                ],
                'delivery_address': [
                    res.delivery_address.id,
                    "%s, %s %s <b>%s (<span class='text-danger'>%s</span>)</b>" % (
                        res.delivery_address.name,
                        res.delivery_address.street,
                        res.delivery_address.street2,
                        res.delivery_address.city, 
                        res.delivery_address.state_id.code)
                ],
                'user_id': [res.user_id.id, res.user_id.name],
                'vehicle_id': [res.user_id.id, res.user_id.display_name],
                'partner_id': [res.partner_id.id, res.partner_id.name],
                'bg': 'bg-light'
            })
        return records