# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
import datetime
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_datetime
import base64
import csv
import io 

# se la tipologia di fleet.location è parking è un oparcheggio a pagamento.
# nel listino mettiamo il prodotto parcheggio con i giorni gratutiti.
# nell'ordine bottone calcola parcheggio che prende lep resenza parcheggio delle auto dell'ordine
# e valuta eventuale aggiunta.

class FleetLocation(models.Model):
    _name = "fleet.location"
    _description = "Fleet Location"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _parent_name = "parent_id"
    _parent_store = True
    
    parent_id = fields.Many2one(
        string="Parent",
        comodel_name="fleet.location",
        tracking=True
    )
    name = fields.Char(
        string="Name",
        tracking=True
    )
    parent_path = fields.Char(
        index=True
    )
    attendance_ids = fields.Many2many(
        string="Attendances",
        comodel_name="fleet.attendance",
        compute="_compute_attendances"
    )
    type = fields.Selection(
        string="Type",
        selection=[
            ('internal',_('Internal')),
            ('external', _('External')),
            ('parking', _('Parking')),
            ('workshop', _('Workshop'))
        ],
        default='workshop'
    )
    currently_attendance = fields.Boolean(
        string="Currently attendance",
        compute="_compute_currently",
        search="_search_currently"
    )
    
    def name_get(self):
        results = []
        for record in self:
            name=[]
            if record.parent_path:
                path = record.parent_path.split('/')
                path = [int(x) for x in path if x != '']
                name = []
                for id in path:
                    res = self.browse(id)
                    name.append(res.name)
            results.append((record.id, ' / '.join(name)))
        return results
    
    def _compute_attendances(self):
        for record in self:
            record.attendance_ids = False
            results = self.env['fleet.attendance'].search([
                ('location_id', '=', record.id),
                ('exit_date', '=', False)
            ])
            if results:
                record.attendance_ids = [(6, 0, results.ids)]
    
    def _compute_currently(self):
        for record in self:
            record.currently_attendance = False
            if record.attendance_ids:
                record.currently_attendance = True
    
    def _search_currently(self, operator, value):
        if value:
            value = False
        results = self.env['fleet.attendance'].search([
            ('exit_date', '=', False)
        ])
        
        if operator == '!=':
            operator = 'not in'
        else:
            operator = 'in'
        
        domain = [('id', operator, list(dict.fromkeys([x.location_id.id for x in results])))]

        return domain

class FleetAttendance(models.Model):
    _name = "fleet.attendance"
    _description = "Fleet Attendance"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    vehicle_id = fields.Many2one(
        string='Vehicle',
        comodel_name="fleet.vehicle",
        tracking=True
    )
    location_id = fields.Many2one(
        string="Location",
        comodel_name="fleet.location",
        tracking=True
    )
    entry_date = fields.Datetime(
        string="Date of entry",
        tracking=True,
        default=datetime.datetime.now()
    )
    exit_date = fields.Datetime(
        string="Date of exit",
        tracking=True
    )
    note = fields.Text(
        string="Note"
    )
    
    employee_id = fields.Many2one(
        string='Carrier/Employee',
        comodel_name="hr.employee",
    )
    
    @api.constrains('exit_date', 'entry_date')
    def _constrains_exit_date(self):
        if self.entry_date and self.exit_date:
            if self.exit_date < self.entry_date:
                raise ValidationError(_('The exit date must be greater than the entrance date.'))  

    @api.constrains('vehicle_id', 'location_id')
    def _constrains_vehicle_id(self):
        for record in self:
            if record.vehicle_id.fleet_attendance_id and \
                record.vehicle_id.fleet_attendance_id.id != record.id:
                    raise ValidationError(_('A vehicle cannot stay in two locations at the same time'))
    
    def name_get(self):
        results = []
        for record in self:
            name = _('%s | %s from %s') % (
                    record.vehicle_id.display_name, 
                    record.location_id.display_name, 
                    format_datetime(self.env, record.entry_date, dt_format=False))
            if record.exit_date:
                name = _('%s | %s from %s to %s') % (
                    record.vehicle_id.display_name, 
                    record.location_id.display_name, 
                    format_datetime(self.env, record.entry_date, dt_format=False), 
                    format_datetime(self.env, record.exit_date, dt_format=False))
                
            results.append((record.id, name))
        return results

    def exit(self):
        for record in self:
            if record.entry_date and not record.exit_date:
                record.exit_date = datetime.datetime.now()
    
class WizardAttendance(models.TransientModel):
    _name = "fleet.attendance.wizard"
    _description = "Fleet Attendance Wizard"
    
    vehicle_id = fields.Many2one(
        string='Vehicle',
        comodel_name="fleet.vehicle"
    )
    location_id = fields.Many2one(
        string="Location",
        comodel_name="fleet.location"
    )

    attendance_id = fields.Many2one(
        string="Attendance",
        comodel_name="fleet.attendance"
    )
    note = fields.Text(
        string="Note"
    )
    employee_id = fields.Many2one(
        string='Carrier/Employee',
        comodel_name="hr.employee",
    )

    view_attendance = fields.Boolean(
        string="View attendance",
        default=False
    )

    def save(self):
        # passo base:
        for record in self:
            if record.attendance_id:
                record.attendance_id.exit_date = datetime.datetime.now()
            else:
                attrs = {
                    'vehicle_id': record.vehicle_id.id,
                    'location_id': record.location_id.id,
                    'note': record.note,
                    'employee_id': record.employee_id.id,
                    'entry_date': datetime.datetime.now()
                }
                self.env['fleet.attendance'].create(attrs)
    
class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"
    
    # presenza attualmente aperta
    fleet_attendance_id = fields.Many2one(
        string="Open Attendance",
        comodel_name="fleet.attendance",
        compute="_compute_fleet_attendance",
        default=False
    )
    number_attendance = fields.Integer(
        string="Number of Attendances",
        compute="_compute_fleet_attendance",
        default=0
    )
    n_tasks = fields.Integer(
        string="Number of Tasks",
        compute="_compute_n_tasks"
    )
    
    # CAMPI PER HUB IMPORTER
    lotto_di_acquisto = fields.Char(
        string="Lotto di acquisto",
        tracking=True
    )
    N_Ordine_Aval = fields.Char(
        string="N Ordine Aval",
        tracking=True
    )
    N_Ordine_Corretto = fields.Char(
        string="N° Ordine corretto",
        tracking=True
    )
    Fornitore = fields.Char(
        string="Fornitore",
        tracking=True
    )
    Data_Ordine = fields.Date(
        string="Data Ordine",
        tracking=True
    )
    Categoria = fields.Char(
        string="Categoria",
        tracking=True
    )
    Tipo = fields.Char(
        string="Tipo",
        tracking=True
    )
    fuel_type = fields.Char(
        string = "Fuel",
        tracking=True
    )
    LCV = fields.Char(
        string="LCV",
        tracking=True
    )
    Piazzale_Appoggio = fields.Char(
        string="Piazzale_Appoggio",
        tracking=True
    )
    Data_prevista_arrivo = fields.Date(
        string="Data prevista arrivo",
        tracking=True
    )
    Aftermarket = fields.Char(
        string="Aftermarket",
        tracking=True
    )
    hub_importer_ids = fields.Many2many(
        string="Hub importer",
        comodel_name="hub.importer"
    )
    
    def _compute_fleet_attendance(self):
        for record in self:
            results = self.env['fleet.attendance'].search([
                ('vehicle_id', '=', record.id),
                ('entry_date', '!=', False),
                ('exit_date', '=', False)
            ])
            if results:
                record.fleet_attendance_id = results[0].id
                record.number_attendance = 1
            else:
                record.fleet_attendance_id = False
                record.number_attendance = 0
    
    def _compute_n_tasks(self):
        for record in self:
            res = self.env['project.task'].search([('vehicle_id', '=', record.id)])
            record.n_tasks = len(res)
    
    def open_tasks(self):
        return {
            'name': _('Tasks for %s') % self.name,
            'res_model': 'project.task',
            'type': 'ir.actions.act_window',
            'context': {},
            'view_mode': 'kanban',
            'view_type': 'kanban,tree,form',
            'domain': [('vehicle_id','=', self.id)]
        }
           
    
    def open_fleet_attendance_wizard(self):
        form_id = self.env.ref('bloomup_fleet_move.fleet_attendance_wizard_view_form').id
        context = {
            'default_vehicle_id': self.id
        }
        if self.fleet_attendance_id:
            context['default_attendance_id'] = self.fleet_attendance_id.id
            context['default_location_id'] = self.fleet_attendance_id.location_id.id
            context['default_view_attendance'] = True
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fleet Attendance',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'views': [(form_id, 'form')],
            'res_model': 'fleet.attendance.wizard',
            'context': context
        }
    
    def create_activities(self, project_id):
        """
        Crea le attività default per questa auto
        project_id : obbligatorio
        """
        # predere le tipologia di attività default
        if not project_id:
            raise ValidationError(_("You can't create task without project"))
        typologies = self.env['task.typology'].search([('default','=',True)])
        tasks = []
        for record in self:
            pricelist = project_id.get_pricelist()
            for type in typologies:
                delay_days = type.get_delay(pricelist)
                attrs = {
                    'task_typology_id': type.id,
                    'vehicle_id': record.id,
                    'partner_id': project_id.partner_id.id,
                    'project_id': project_id.id,
                    'name': type.name,
                    'date_deadline': datetime.datetime.now() + datetime.timedelta(days=delay_days)
                }
                tasks.append(self.env['project.task'].create(attrs))
        return tasks

class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"
    
    delay_days = fields.Integer(
        string="Number of Days",
        tracking=True,
        default=0
    )
    
class ConfigImporterVehicle(models.Model):
    _name = "hub.importer.config"
    _description = "Hub Importer Config"

    field_id = fields.Selection(
        string="Field",
        selection=[
            ('lotto_di_acquisto', 'LOTTO DI ACQUISTO'),
            ('N_Ordine_Aval', 'N_Ordine_Aval'),
            ('N_Ordine_Corretto', 'N° Ordine corretto'),
            ('Fornitore', 'Fornitore'),
            ('Data_Ordine', 'Data_Ordine'),
            ('vin_sn', 'Telaio'),
            ('acquisition_date', 'Data_Immatricolazione'),
            ('license_plate', 'Targa'),
            ('Categoria', 'Categoria'),
            ('brand_id', 'Marca'),
            ('Tipo', 'Tipo'),
            ('model_id', 'Modello'),
            ('fuel_type', 'Alimentazione'),
            ('LCV', 'LCV'),
            ('Piazzale_Appoggio', 'Piazzale Appoggio'),
            ('Data_prevista_arrivo', 'Data prevista arrivo'),
            ('Aftermarket', 'Aftermarket'),
        ]
    )
    name = fields.Char(
        string="Field csv"
    )
    partner_id = fields.Many2one('res.partner', string='Azienda')

class HubImporter(models.Model):
    _name = "hub.importer"
    _description = "Hub Vehicles Importer"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Name",
        tracking=True
    )
    source_file = fields.Binary(
        string='Source File',
        tracking=True
    )
    source_filename = fields.Char(
        string="Filename"
    )
    project_id = fields.Many2one(
        string="Project",
        comodel_name="project.project",
        tracking=True,
        domain=[("is_hub","=",True)]
    )
    state = fields.Selection(
        string="Status",
        selection=[
            ('draft',_('Draft')),
            ('done', _('Done'))
        ],
        tracking=True,
        default='draft'
    )
    source_data = fields.Selection(
        string="Source Datas",
        selection=[
            ('file', _('File')),
            ('internal', _('Internal'))
        ],
        default='file'
    )
    internal_vehicle_ids = fields.Many2many(
        string="Vehicles",
        comodel_name="fleet.attendance",
        domain=[('location_id.type', '=', 'internal')]
    )
    delimiter = fields.Char(
        string="Delimiter",
        default=","
    )
    quotechar = fields.Char(
        string="Quotechar",
        default="'"
    )
    row_header = fields.Integer(
        string="Header line number",
        default=1
    )
    vehicle_ids = fields.Many2many(
        string="Vehicles",
        comodel_name="fleet.vehicle",
        compute="_computeVehicles"
    )
    tasks = fields.Many2many(
        string="Tasks",
        comodel_name="project.task"
    )
    n_tasks = fields.Integer(
        string="Number of Tasks",
        compute="_compute_n_tasks"
    )
    
    def _computeVehicles(self):
        for record in self:
            record.vehicle_ids = False
            results = self.env['fleet.vehicle'].search([('hub_importer_ids','in',record.id)])
            if results:
                record.vehicle_ids = [(6,0,results.ids)]
    
    def _compute_n_tasks(self):
        for record in self:
            record.n_tasks = len(record.tasks)
    
    def open_tasks(self):
        return {
            'name': _('Tasks for %s') % self.name,
            'res_model': 'project.task',
            'type': 'ir.actions.act_window',
            'context': {},
            'view_mode': 'kanban',
            'view_type': 'kanban,tree,form',
            'domain': [('id','in', self.tasks.ids)]
        }
    
    def save_import(self):
        """
        Legge il file e per ogni auto controlla se esiste nel db quel numero di telaio.
        Se esiste crea le attività altrimenti crea l'auto e le attività.
        
        se non è configurata la colonna csv allora prende il nome della selection
        """
        for record in self:
            
            if record.state == 'done':
                continue
            
            if record.source_data == 'internal':
                for line in record.internal_vehicle_ids:
                    auto = line.vehicle_id
                    task = auto.create_activities(record.project_id)
                    for t in task:
                        record.tasks = [(4, t.id, 0)]
                record.state = 'done'
                continue
                
            if not record.source_file:
                continue
            
            output = base64.b64decode(record.source_file).decode("utf-8")
            output = io.StringIO(output)
            reader = csv.reader(output, delimiter=record.delimiter, quotechar=record.quotechar)
            i = 1
            
            attrs = {}
            for res in dict(self.env['hub.importer.config']._fields['field_id'].selection):
                line = record.project_id.partner_id.csv_hub_configuration.filtered(lambda x: x.field_id == res)
                name = dict(self.env['hub.importer.config']._fields['field_id'].selection)[res]
                if line:
                    name = line.name
                attrs[res] = name.strip()
            
            header = []
            for line in reader:
                if i == record.row_header:
                    header = [x.strip() for x in line]
                    i+=1
                    continue
                i+=1
                riga = {}
                for att in attrs:
                    try:
                        if header.index(attrs[att]):
                            riga[att] = line[header.index(attrs[att])]
                    except:
                        continue
                foundit = False
                auto = False
                if 'vin_sn' in riga and riga['vin_sn']:
                    res = self.env['fleet.vehicle'].search([('vin_sn','=',riga['vin_sn'])])
                    if res:
                        auto = res[0]
                        auto.hub_importer_ids = [(4, record.id, 0)]
                        foundit = True
                if not foundit and 'license_plate' in riga and riga['license_plate']:
                    res = self.env['fleet.vehicle'].search([('license_plate','=',riga['license_plate'])])
                    if res:
                        auto=res[0]
                        auto.hub_importer_ids = [(4, record.id, 0)]
                        foundit = True
                if not foundit and len(riga) and 'brand_id' in riga and 'model_id' in riga:
                    brand = self.env['fleet.vehicle.model.brand'].sudo().search([
                        ('name', '=ilike', riga['brand_id'])
                    ]) 
                    if not brand:
                        brand = self.env['fleet.vehicle.model.brand'].sudo().create({
                            'name': riga['brand_id']
                        })
                    model = self.env['fleet.vehicle.model'].sudo().search([
                        ('name', '=ilike', riga['model_id'])
                    ])
                    if not model:
                        model = self.env['fleet.vehicle.model'].sudo().create({
                            'name': riga['model_id'],
                            'brand_id': brand.id
                        })
                    riga['model_id'] = model.id
                    del riga['brand_id']
                    riga['hub_importer_ids'] = [(4, record.id, 0)]
                    if riga['acquisition_date'] == '':
                        riga['acquisition_date'] = False
                    if riga['Data_Ordine'] == '':
                        riga['Data_Ordine'] = False
                    if riga['Data_prevista_arrivo'] == '':
                        riga['Data_prevista_arrivo'] = False
                    if record.project_id and record.project_id.partner_id:
                        riga['owner_id'] = record.project_id.partner_id.id
                    _logger = logging.getLogger(__name__)
                    _logger.info(riga)
                    auto = self.env['fleet.vehicle'].create(riga)
                if auto:   
                    task = auto.create_activities(record.project_id)
                    for t in task:
                        record.tasks = [(4, t.id, 0)]
                
            record.state = 'done'
            
class TaskTypology(models.Model):
    _name = "task.typology"
    _description = "Task Typology"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Name",
        tracking=True
    )
    default = fields.Boolean(
        string="New Task Default",
        default=False,
        tracking=True
    )
    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product"
    )
    
    def get_delay(self, pricelist):
        """
        Data una pricelist ritorna i giorni di ritardo di questa tipologia
        pricelist: obbligatorio
        """
        if not pricelist:
            raise ValidationError(_('Pricelist is missing.'))
        self.ensure_one()
        line = pricelist.item_ids.filtered(
            lambda x: x.product_id.id == self.product_id.id if x.product_id else \
                      x.product_tmpl_id.id == self.product_id.product_tmpl_id.id
        )
        if not line:
            raise ValidationError(_('Pricelist Line is missing.'))
        # prendo sempre la prima per sicurezza
        # si potrebbe valutare di prendere in considerazione le date
        return line[0].delay_days
    
class ProjectHub(models.Model):
    _inherit = "project.project"
    
    is_hub = fields.Boolean(
        string="Hub Project",
        help="Identifica un progetto per la manutenzione in officina",
        default=False,
        tracking=True
    )
    hub_importer_id = fields.Many2one(
        string="Importer",
        comodel_name="hub.importer",
        compute="_compute_hub_importer"
    )
    
    def _compute_hub_importer(self):
        for record in self:
            res = self.env['hub.importer'].sudo().search([('project_id', '=', record.id)])
            if res:
                record.hub_importer_id = res[0].id
            else:
                record.hub_importer_id = False
    
    def get_pricelist(self):
        self.ensure_one()
        if not self.partner_id:
            raise ValidationError(_('Customer is missing.'))      
        pricelist = self.partner_id.property_product_pricelist
        if not pricelist:
            raise ValidationError(_('Pricelist for customer %s is missing.') % self.partner_id.display_name)   
        return pricelist

    @api.constrains('is_hub')
    def _constrains_is_hub(self):
        """
        Assegna gli stage per Hub
        """
        for record in self:
            if record.is_hub:
                stage_ids = self.env['project.task.type'].search([('is_hub', '=', True)])
                stage_ids.write({
                    'project_ids': [(4, record.id, 0)]
                })
        
class TaskHub(models.Model):
    _inherit = "project.task"
    
    is_hub = fields.Boolean(
        string="Hub Task",
        related="project_id.is_hub"
    )
    task_typology_id = fields.Many2one(
        string="Typology",
        comodel_name="task.typology",
        tracking=True
    )
    vehicle_id = fields.Many2one(
        string="Vehicle",
        comodel_name="fleet.vehicle"
    )
    
    @api.model
    def create(self, values):
        """
        Quando si crea un task si cerca la fase default assegnata al progetto di quello stage
        e si assegna. (quindi i progetti devono essere assegnati a quella fase)
        Tecnicamente ogni progetto può avere fase default diversa in abse alle assegnazioni.
        """
        project_id = False
        if 'project_id' in values:
            project_id = values.get('project_id')
        task_stage = self.env['project.task.type'].search([
            ('project_ids', 'in', project_id),
            ('is_default', '=', True)
        ]) 
        if task_stage:
            values['stage_id'] = task_stage[0].id
        
        return super(TaskHub, self).create(values)

    def _create_order(self):
        """
        Crea l'ordine a partire dalle attività
        """
        # prenso solo quelle in uno stato chiuso e che non hanno riga ordine associata
        results = [record for record in self if record.stage_id.is_closed and not record.sale_line_id]
        
        orders = {x.project_id.partner_id : [] for x in results}
        for record in results:
            orders[record.project_id.partner_id].append(record)
            
        for partner in orders:
            order_attrs = {
                'partner_id': partner.id,
                'pricelist_id': partner.property_product_pricelist.id
            }
            order = self.env['sale.order'].create(order_attrs)
            
            # raggruppo per prodotto
            products = {line.task_typology_id.product_id.id : [] for line in orders[partner]}
            for line in orders[partner]:
                products[line.task_typology_id.product_id.id].append(line)
            
            for product in products:
                order_line_att = {
                    'product_id': product,
                    'name': products[product][0].task_typology_id.product_id.name + \
                        ' - ' + ', '.join([x.vehicle_id.display_name for x in products[product]]),
                    'product_uom_qty': len(products[product]),
                    'order_id': order.id
                }
                order_line = self.env['sale.order.line'].create(order_line_att)
                for line in products[product]:
                    line.sale_line_id = order_line.id
                    line.sale_order_id = order.id
            
class ResPartner(models.Model):
    _inherit = "res.partner"

    csv_hub_configuration = fields.One2many(
        comodel_name='hub.importer.config', 
        inverse_name='partner_id', 
        string='Csv Hub Configuration'
    )

class ProjectTaskType(models.Model):
    _inherit = "project.task.type"
    
    is_default = fields.Boolean(
        string="Default",
        default=False
    )
    is_hub = fields.Boolean(
        string="Is Hub",
        default=False
    )
