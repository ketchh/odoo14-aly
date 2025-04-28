from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging
import pytz
from datetime import datetime
import json

_logger = logging.getLogger(__name__)

class FleetMove(models.Model):
    _inherit = "fleet.move"
    
    google_maps = fields.Char(
        string="Google Maps",
        compute="_compute_google_maps"
    )
    selected_tyre_repairer = fields.Many2one(
        string="Tyre repairer",
        comodel_name="tyre.repairer",
        tracking=True
    )
    tyre_order_id = fields.Char(
        string="TyreTeam Order ID",
        tracking=True
    )
    
    is_queueing = fields.Boolean(
        string="Waiting for REST Queue",
        tracking=True
    )

    def _compute_google_maps(self):
        """ 
        Assign the google maps api settings to google_maps field
        """
        google_maps_api_key = self.env['ir.config_parameter'].sudo().get_param('base_geolocalize.google_map_api_key')
        for record in self:
            if google_maps_api_key:
                record.google_maps = google_maps_api_key
            else:
                record.google_maps = False
    
    def find_tyre_repairer(self):
        self.ensure_one()
        try:
            form_view_id = self.env.ref("bloomup_fleet_move_tyre.fleet_move_view_form__tyre").id
        except Exception as e:
            form_view_id = False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Find Tyre Repairer',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'fleet.move',
            'res_id': self.id,
            'views': [(form_view_id, 'form')],
            'target': 'new',
        }

    def send_repairer_selection_mail(self):
        """
        Send a confirmation Mail to repairer containing vehicle and tires to be installed
        """
        self.ensure_one()
        template_id = self.env.ref('bloomup_fleet_move_tyre.tyre_repairer_delivery_mail').id
        partner_ids = []
        if self.selected_tyre_repairer:
            partner_ids.append(self.selected_tyre_repairer.id)
        else:
            raise UserError(_("No repairer selected"))
        action = {
            'name': "Invia Mail",
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': {
                'default_composition_mode': 'comment',
                'default_model': 'fleet.move',
                'default_res_id': self.ids[0],
                'default_use_template': bool(template_id),
                'default_template_id': template_id,
                'default_email_layout_xmlid':'mail.mail_notification_light',
                'active_ids': self.ids,
                'default_notify': False,
                'default_notify_followers':False
            },
        }
        if len(partner_ids):
            action.get('context').update({'default_partner_ids':partner_ids})

        return action
    
    def action_reset_queueing(self):
        """
        reset queue status
        """
        self.is_queueing = False
        return
    
    def confirm_repairer(self):
        """
        Sends to TyreTeam info on the selected tire repairer
        """
        #crea nuova riga nel modello queuee
        self.ensure_one()
        _logger.info(
            'EXECUTING CONFIRM_REPAIRER')
        # prendo i parametri di Active sezione API nelle config
        api_addr = self.env['ir.config_parameter'].sudo(
        ).get_param('bloomup_fleet_move_tyre.api_addr')

        api_key = self.env['ir.config_parameter'].sudo(
        ).get_param('bloomup_fleet_move_tyre.api_key')

        if not api_addr or not api_key:
            # errore parametri non trovati nelle config
            _logger.error(
                "CONFIRM_REPAIRER ERROR: Mancano i parametri API all'interno delle impostazioni")
            raise UserError("Mancano i parametri API all'interno delle impostazioni")
        
        url = api_addr + "/orders/garage"

        if not self.tyre_order_id:
            # errore ordine non registrato
            _logger.error(
                "CONFIRM_REPAIRER ERROR: Ordine non registrati su TyreTeam")
            raise UserError("Ordine non registrato su TyreTeam")
        
        if self.pneumatici_servizio != "WINTER KIT":
            #errore pneumatici servizio
            _logger.error(
                "CONFIRM_REPAIRER ERROR: Il campo Pneumatici Servizio deve essere settato a 'WINTER KIT'")
            raise UserError("Il campo Pneumatici Servizio deve essere settato a 'WINTER KIT'")
        
        if not self.selected_tyre_repairer or not self.selected_tyre_repairer.customer_center:
            #gommista assente   
            _logger.error(
                "CONFIRM_REPAIRER ERROR: Gommista Assente o non registrato")
            raise UserError("Gommista Assente o non registrato")

        payload = {
            'OrderId': self.tyre_order_id,
            'CustomerCode': self.selected_tyre_repairer.customer_center
        }

        resource = 'fleet.move, ' + str(self.id)

        attrs = {
            'endpoint': url,
            'method': "POST",
            'resource_id': resource,
            'auth':"header_api_key",
            'key': "APIKEY",
            'value': api_key,
            'server_action_id': self.env.ref("bloomup_fleet_move_tyre.action_reset_queueing").id,
            'payload': json.dumps(payload),
        }

        self.env["external.rest.api.queue"].sudo().create(attrs)
        self.is_queueing = True
        return
    
    def confirm_driver_delivery(self):
        """
        Sends to TyreTeam confirmation for the end of a request
        """
        #crea nuova riga nel modello queuee
        self.ensure_one()
        _logger.info(
            'EXECUTING CONFIRM_DRIVER_DELIVERY')
        # prendo i parametri di Active sezione API nelle config
        api_addr = self.env['ir.config_parameter'].sudo(
        ).get_param('bloomup_fleet_move_tyre.api_addr')

        api_key = self.env['ir.config_parameter'].sudo(
        ).get_param('bloomup_fleet_move_tyre.api_key')

        if not api_addr or not api_key:
            # errore parametri non trovati nelle config
            _logger.error(
                "CONFIRM_DRIVER_DELIVERY ERROR: Mancano i parametri API all'interno delle impostazioni")
            raise UserError("Mancano i parametri API all'interno delle impostazioni")
        
        url = api_addr + "/orders/driverdeliver"

        if not self.tyre_order_id:
            # errore ordine non registrato
            _logger.error(
                "CONFIRM_REPAIRER ERROR: Ordine non registrati su TyreTeam")
            raise UserError("Ordine non registrato su TyreTeam")
        
        if self.pneumatici_servizio != "WINTER KIT":
            #errore pneumatici servizio
            _logger.error(
                "CONFIRM_REPAIRER ERROR: Il campo Pneumatici Servizio deve essere settato a 'WINTER KIT'")
            raise UserError("Il campo Pneumatici Servizio deve essere settato a 'WINTER KIT'")
        
        date_format = '%Y-%m-%d %H:%M:%S'
        localtz = pytz.timezone("Europe/Rome")
        print(datetime.strftime(datetime.now(tz=localtz), date_format))

        payload = {
            'OrderId': self.tyre_order_id,
            'DeliverDateTime': datetime.strftime(datetime.now(tz=localtz), date_format)
        }
        resource = 'fleet.move, ' + str(self.id)

        attrs = {
            'endpoint': url,
            'method': "POST",
            'resource_id': resource,
            'auth':"header_api_key",
            'key': "APIKEY",
            'value': api_key,
            'server_action_id': self.env.ref("bloomup_fleet_move_tyre.action_reset_queueing").id,
            'payload': json.dumps(payload),
        }

        self.env["external.rest.api.queue"].sudo().create(attrs)
        self.is_queueing = True
        return

    
    def action_set_tyre_team_order(self, response):
        """
        Sets order_id received after a succesful creation request
        """
        res = json.loads(response)
        if res['OrderId']:
            self.tyre_order_id = res['OrderId']
        self.is_queueing = False
        return

    def create_tyre_team_order(self):
        """
        Sends to TyreTeam an order for the installation of the tires assigned to the vehicle in the fleet_move
        """
        #crea nuova riga nel modello queuee
        self.ensure_one()
        _logger.info(
            'EXECUTING SEND_TYRE_TEAM_ORDER')
        # prendo i parametri di Active sezione API nelle config
        api_addr = self.env['ir.config_parameter'].sudo(
        ).get_param('bloomup_fleet_move_tyre.api_addr')

        api_key = self.env['ir.config_parameter'].sudo(
        ).get_param('bloomup_fleet_move_tyre.api_key')

        if not api_addr or not api_key:
            # errore parametri non trovati nelle config
            _logger.error(
                "SEND_TYRE_TEAM_ORDER ERROR: Mancano i parametri API all'interno delle impostazioni")
            raise UserError("Mancano i parametri API all'interno delle impostazioni")
        
        url = api_addr + "/orders/add"

        if not self.vehicle_id.front_wheel or not self.vehicle_id.rear_wheel:
            # errore pneumatici mancanti
            _logger.error(
                "SEND_TYRE_TEAM_ORDER ERROR: Mancano le tipologie di pneumatici sul veicolo")
            raise UserError("Mancano le tipologie di pneumatici sul veicolo")
        
        if self.pneumatici_servizio != "WINTER KIT":
            #errore pneumatici servizio
            _logger.error(
                "SEND_TYRE_TEAM_ORDER ERROR: Il campo Pneumatici Servizio deve essere settato a 'WINTER KIT'")
            raise UserError("Il campo Pneumatici Servizio deve essere settato a 'WINTER KIT'")
        
        if self.tyre_order_id:
            #ordine già esistente   
            _logger.error(
                "SEND_TYRE_TEAM_ORDER ERROR: Ordine Tyre Team già esistente")
            raise UserError("Ordine Tyre Team già esistente")
        

        tire_list = self.vehicle_id.get_tire_dict_list()

        payload = {
            'EcoOrderId': self.name,
            'OwnerId': self.partner_id.tyre_team_id if self.partner_id.tyre_team_id else "1",
            'VehiclePlate': self.vehicle_id.license_plate,
            'ParkingId': self.pickup_address.parking_id if self.pickup_address.parking_id else "1",
            'Tires': tire_list
        }
        resource = 'fleet.move, ' + str(self.id)

        attrs = {
            'endpoint': url,
            'method': "POST",
            'resource_id': resource,
            'auth':"header_api_key",
            'key': "apikey",
            'value': api_key,
            'server_action_id': self.env.ref("bloomup_fleet_move_tyre.action_set_tyre_team_order").id,
            'payload': json.dumps(payload),
            # 'payload': payload,
        }

        self.env["external.rest.api.queue"].sudo().create(attrs)
        self.is_queueing = True
        return
            
        