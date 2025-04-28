from odoo import _, api, fields, models
import datetime

class TaskTypologyCarpentum(models.Model):
    _inherit = "task.typology"
    
    move_type = fields.Many2many(
        string="Tipologia",
        comodel_name="fleet.move.arval.type",
        tracking=True
    )

class TaskCarpentum(models.Model):
    _inherit="project.task"
    
    fleet_move_id = fields.Many2one(
        string="Incarico",
        comodel_name="fleet.move",
        compute="_compute_fleet_move_from_vehicle",
        store=True
    )
    pickup_address = fields.Many2one(
        string="Pickup Address",
        comodel_name="fleet.partner",
        related="fleet_move_id.pickup_address"
    )
    date_dealer_availability = fields.Date(
        string="Data disponibilità Dealer",
        tracking=True
    )
    date_calendar = fields.Date(
        string="Calendar Date",
        traking=True
    )
    
    def name_get(self):
        result = []
        for task in self:
            name = ''
            if task.date_deadline:
                name += '* '# l'asterisco significa che è stata modificata e scelta da ars
            name += task.name
            if task.vehicle_id:
                name += ' (%s) ' % task.vehicle_id.license_plate 
            if task.pickup_address:
                name += ' %s' % task.pickup_address.display_name
            result.append((task.id, name))
        return result
    
    @api.constrains('date_deadline','date_dealer_availability')
    def _compute_calendar_date(self):
        """ 
        se presente date_deadline allora assume questo valore
        altrimenti quello della date_dealer_availability
        
        """
        for record in self:
            if record.date_deadline:
                if record.pickup_address and record.pickup_address.user_id:
                    record.user_id = record.pickup_address.user_id.id
        if self.env.context.get('no_propagate'):
            return 
        for record in self:
            record.date_calendar = False
            if record.date_deadline:
                record.with_context({'no_propagate':True}).date_calendar = record.date_deadline
            else:
                if record.date_dealer_availability:
                    record.with_context({'no_propagate':True}).date_calendar = record.date_dealer_availability
    
    @api.constrains('date_calendar')
    def _compute_other_date(self):
        if self.env.context.get('no_propagate'):
            return 
        for record in self:
            record.with_context({'no_propagate':True}).date_deadline = record.date_calendar
    
    @api.depends('vehicle_id')
    def _compute_fleet_move_from_vehicle(self):
        """ 
        serve a calcolare l'incarico a partire dal veicolo assegnato
        al task.
        
        - solo per compatibilità con le vecchie task
        """
        for record in self:
            if record.vehicle_id:
                result = self.env['fleet.move'].search([('vehicle_id','=',record.vehicle_id.id)])
                if result:
                    record.fleet_move_id = result[0].id
                    
    @api.model
    def _cron_48h(self, days):
        """
        Task a <days> giorni da adesso (il task ha solo un DATE non DATETIME)
        prende i task li raggruppa per indirizzo di prelievo
        manda la mail dal template  
        """
        date = datetime.datetime.now() + datetime.timedelta(days=days)
        date = date.date()
        # non posso fare la groupby perchè pickup_address è related e odoo si sente male
        results = self.env['project.task'].search([
            ('date_deadline','=',date),
            ('fleet_move_id.move_type','=',self.env.ref('bloomup_carpentum.arval_rit_dea').id)
        ])
        pickup_addresses = results.mapped('pickup_address')
        tasks = {}
        for pa in pickup_addresses:
            tasks.update({pa: results.filtered(lambda x: x.pickup_address.id == pa.id)})
        template = self.env.ref('bloomup_carpentum.email_template_ritdea_dealer_appointment_bbox')
        if template:
            for pa in tasks:
                html = '<ul>'
                for task in tasks[pa]:
                    html += '<li>Veicolo %s</li>' % task.vehicle_id.display_name
                html += '</ul>'
                values={
                    'bbox_date':date,
                    'activity_bbox': html
                }
                template.with_context(values).send_mail(pa.id)
        