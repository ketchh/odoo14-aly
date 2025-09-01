from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import requests

class Checklist(models.Model):
    _inherit = "checklist.checklist"

    auto_create = fields.Boolean(
        string="Auto creation",
        default=False
    )
    auto_create_state = fields.Many2one(
        string="Auto creation state",
        comodel_name="fleet.move.status"
    )

    white_label = fields.Selection(
        string="White label",
        selection=[
            ('simple', 'Simplerent')
        ],
        tracking=True
    )
    close_model = fields.Boolean(
        string="Close the related model",
        default=False
    )

    @api.constrains('state')
    def _constrains_state_addons(self):
        """
        Quando viene completata una checklist si controlla che chiuda
        oggetto referenziato,
        se si la movimentazione va in completato.
        """
        for record in self:
            if record.state == 'done' and record.close_model:
                state = self.env['fleet.move.status'].sudo().search([('done', '=', True)])
                if state:
                    record.sudo().ref_doc_id.state = state[0].id


class FleetMove(models.Model):
    _inherit = "fleet.move"

    distance = fields.Float(
        string = "Distanza"
    )
    distance_time = fields.Float(
        string="Tempo percorrenza"
    )
    
    # def get_distance(self):
    #     gmaps_api = self.env['ir.config_parameter'].sudo().get_param('base_geolocalize.google_map_api_key')
    #     for record in self:
    #         if record.pickup_address and record.delivery_address:
    #             origin = [
    #                 record.pickup_address.city,
    #                 record.pickup_address.street,
    #                 record.pickup_address.state_id.name if record.pickup_address.state_id else '',
    #                 record.pickup_address.zip
    #             ]
    #             origin = ','.join([x for x in origin if x or x != ''])
                
    #             destination = [
    #                 record.delivery_address.city,
    #                 record.delivery_address.street,
    #                 record.delivery_address.state_id.name if record.delivery_address.state_id else '',
    #                 record.delivery_address.zip
    #             ]
    #             destination = ','.join([x for x in destination if x or x != ''])
    #             url = "https://maps.googleapis.com/maps/api/distancematrix/json?origins=%s&destinations=%s&units=metric&key=%s"
    #             response = requests.request("GET", url % (origin,destination,gmaps_api), headers={},data={})
                
    #             matrix = response.json()
    #             if matrix.get('status') == 'OK':
    #                 rows = matrix.get('rows')
    #                 if rows:
    #                     row = rows[0]
    #                     distance = row.get('elements')[0].get('distance').get('value')
    #                     distance_time = row.get('elements')[0].get('duration').get('value')
    #                     record.distance = distance / 1000
    #                     record.distance_time = (distance_time / 60) / 60
    #             else:
    #                 record.message_post(
    #                     message_type='comment',
    #                     body="Google maps: %s" % matrix.get('error_message')
    #                 )
    
    # @api.model
    # def create(self, vals):
    #     res_ids = super(FleetMove, self).create(vals)
    #     res_ids.get_distance()
    #     return res_ids
    # # LETIZIA - open a wizard to compose an email from fleet move for ethos customer care

    def action_fleet_move_send(self):
        self.ensure_one()
        lang = self.env.context.get('lang')
        ctx = {
            'default_model': 'fleet.move',
            'default_res_id': self.ids[0],
            'default_composition_mode': 'comment',
            'force_email': True,

        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def action_fleet_move_sms(self):
        self.ensure_one()
        lang = self.env.context.get('lang')
        otp = self.env['sms.otp'].search([])
        if otp and self.delivery_address.phone and self.delivery_address.country_id:
            otp = otp[0]
            phone = otp.phone_format(
                self.delivery_address.phone, self.delivery_address.country_id)
            ctx = {
                'default_model': 'fleet.move',
                'default_res_id': self.ids[0],
                'default_composition_mode': 'comment',
                'default_recipient_single_number_itf': phone

            }
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'sms.composer',
                'views': [(False, 'form')],
                'view_id': False,
                'target': 'new',
                'context': ctx,
            }
        else:
            raise UserError(_('Verify partner phone!'))
 
    @api.constrains('state')
    def _create_auto_checklist(self,white_label=None):
        """
        Funzione per l'azione server che prende i modelli con campo auto_create == True
        e crea le checklist corrispondenti per la movimentazione corrente
        azione: Creazione automatica della checklist
        """
        
        for record in self:
            
            if white_label:
                checklist_models = self.env['checklist.checklist'].sudo().search([
                    ('auto_create', '=', True), ('is_template', '=', True),
                    ('white_label','=',white_label),('auto_create_state', '=', record.state.id)
                ])
            else:
                checklist_models = self.env['checklist.checklist'].sudo().search([
                    ('auto_create', '=', True), ('is_template', '=', True),
                    ('auto_create_state', '=', record.state.id)
                ])
            print('###', record.state, checklist_models)
            for checklist_model in checklist_models:
                checklist = checklist_model.copy()
                name = checklist.name
                checklist.with_context({'lang':record.partner_id.lang}).write({
                    'confirmed_date': record.confirmed_date,
                    'is_template': False,
                    'is_copied': True,
                    'name': "[{}] {}".format(record.vehicle_id.license_plate,name)
                })
                for line in checklist_model.line_ids:
                    new_line = line.copy()
                    new_line.write({
                        'checklist_id': checklist.id,
                        'option_precompiled': line.option_precompiled
                    })
                checklist.write({
                    'ref_doc_id': "fleet.move,%s" % record.id,
                    'user_id': record.employee_id.user_id.id if record.employee_id else False,
                    
                })

    @api.model
    def create_day_checklists(self):
        """
        Crea le checklist di inizio e fine giornata da template con day_start e day_end a True.
        Se esistono già checklist con day_start o day_end a True per lo stesso user_id e confirmed_date
        con is_template a False, non vengono create nuove checklist.
        """
        for record in self:
            # Cerca checklist esistenti non template con day_start o day_end a True
            existing_checklists = self.env['checklist.checklist'].sudo().search([
                ('is_template', '=', False),
                ('confirmed_date', '=', record.confirmed_date),
                ('user_id', '=', record.employee_id.user_id.id if record.employee_id else False),
                '|',
                ('day_start', '=', True),
                ('day_end', '=', True)
            ])

            # Se esistono checklist, non creare nuove
            if existing_checklists:
                continue

            # Cerca template per day_start e day_end
            checklist_templates = self.env['checklist.checklist'].sudo().search([
                ('is_template', '=', True),
                '|',
                ('day_start', '=', True),
                ('day_end', '=', True)
            ])

            # Crea checklist da template
            for template in checklist_templates:
                checklist = template.copy()
                checklist.write({
                    'is_template': False,
                    'is_copied': True,
                    'confirmed_date': record.confirmed_date,
                    'user_id': record.employee_id.user_id.id if record.employee_id else False,
                    'ref_doc_id': "fleet.move,%s" % record.id,
                    'name': "{} {}".format(template.name , record.confirmed_date)
                })

                # Copia le linee della checklist
                for line in template.line_ids:
                    new_line = line.copy()
                    new_line.write({
                        'checklist_id': checklist.id,
                        'option_precompiled': line.option_precompiled
                    })

    @api.constrains('state')
    def _check_state_and_create_checklists(self):
        #Crea checklist di inizio e fine giornata quando 
        for record in self:
            pronto = self.env['fleet.move.status'].search([('pronto','=',True)])
            if record.state == pronto:  
                record.create_day_checklists()

        

 
class Task(models.Model):
    _inherit = "project.task"
    
    @api.constrains('stage_id')
    def _metti_a_pronto(self):
        """
        Quando tutte le attività bloccanti sono completate
        mette a pronto la movimentazione
        """
        pronto = self.env['fleet.move.status'].search([('pronto','=',True)])
        if not pronto:
            return True
        for record in self:
            if record.stage_id.is_closed:
                if record.task_typology_id.block_state:
                    mov = self.env['fleet.move'].search([
                        ('vehicle_id','=',record.vehicle_id.id)
                    ])
                    if not mov:
                        return True
                    
                    tasks = self.env['project.task'].search(
                        [('vehicle_id','=',record.vehicle_id.id),
                        ('stage_id.is_closed','=',False),
                        ('task_typology_id.block_state','=',True),
                        ('id','!=',record.id)]
                    )
                    
                    if not tasks:
                        mov.state = pronto[0].id
                    
