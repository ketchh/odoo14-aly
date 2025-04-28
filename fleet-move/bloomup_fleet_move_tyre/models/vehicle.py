from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging
import json

_logger = logging.getLogger(__name__)

class VehicleExtension(models.Model):
    _inherit = "fleet.vehicle"
    
    front_wheel = fields.Many2one(
        string="Front Wheels",
        comodel_name="tyre.tire",
        tracking=True
    )

    rear_wheel = fields.Many2one(
        string="Rear Wheels",
        comodel_name="tyre.tire",
        tracking=True
    )

    is_wheel_missing = fields.Boolean(
        string="Modello pneumatico non registrato",
        tracking=True
    )

    is_queueing = fields.Boolean(
        string="Waiting for REST Queue",
        tracking=True
    )

    dot = fields.Char(
        string="Anno Produzione Pneumatici",
        tracking=True
    )
    
    def get_tire_dict_list(self):
        ret = []
        if self.front_wheel:
            ret.append({
                'Width': str(int(self.front_wheel.width)),
                'Section': self.front_wheel.section,
                'Diameter': str(int(self.front_wheel.diameter)),
                'LoadIndex': self.front_wheel.load_index,
                'SpeedIndex': self.front_wheel.speed_index,
                'Season': self.front_wheel.season,
                'Axle': "F",
                'Qty': 2,
                'Quality': self.front_wheel.quality,
                'TyreTechnology': self.front_wheel.technology,
                'DOT': self.dot,
                'SupplierTyreId': self.front_wheel.supplier_tire_id
            })
        if self.rear_wheel:
            ret.append({
                'Width': str(int(self.rear_wheel.width)),
                'Section': self.rear_wheel.section,
                'Diameter': str(int(self.rear_wheel.diameter)),
                'LoadIndex': self.rear_wheel.load_index,
                'SpeedIndex': self.rear_wheel.speed_index,
                'Season': self.rear_wheel.season,
                'Axle': "B",
                'Qty': 2,
                'Quality': self.rear_wheel.quality,
                'TyreTechnology': self.rear_wheel.technology,
                'DOT': self.dot,
                'SupplierTyreId': self.rear_wheel.supplier_tire_id
            })

        return ret

    def action_reset_vehicle_queue(self):
        """
        required to avoid multiple rest queue requests
        """
        self.is_queueing = False

    def send_unregistered_wheel_model_info(self, checklist_dict):
        """
        param: checklist_dict; Missing tire data collected from Netcheck
        Queues a message for TyreTeam with the info on the unregistered tires
        """
        self.ensure_one()
        self.is_wheel_missing = True
        tire_list = []
        if checklist_dict['is_front_wheel_missing']:
            list_obj_front = {
                'Brand': checklist_dict['brand_front'],
                'Model': checklist_dict['model_front'],
                'Width': checklist_dict['width_front'],
                'Section': checklist_dict['section_front'],
                'Diameter': checklist_dict['diameter_front'],
                'LoadIndex': checklist_dict['load_index_front'],
                'SpeedIndex': checklist_dict['speed_index_front'],
                'Season': checklist_dict['season_front']
            }
            tire_list.append(list_obj_front)
        if checklist_dict['is_rear_wheel_missing']:
            list_obj_rear =  {
                'Brand': checklist_dict['brand_rear'],
                'Model': checklist_dict['model_rear'],
                'Width': checklist_dict['width_rear'],
                'Section': checklist_dict['section_rear'],
                'Diameter': checklist_dict['diameter_rear'],
                'LoadIndex': checklist_dict['load_index_rear'],
                'SpeedIndex': checklist_dict['speed_index_rear'],
                'Season': checklist_dict['season_rear']
            }
            tire_list.append(list_obj_rear)
        #set flag and send info
        if len(tire_list):

            _logger.info(
                    'EXECUTING SEND_MISSING_TIRE_INFO')
                # prendo i parametri di Active sezione API nelle config
            api_addr = self.env['ir.config_parameter'].sudo(
            ).get_param('bloomup_fleet_move_tyre.api_addr')

            api_key = self.env['ir.config_parameter'].sudo(
            ).get_param('bloomup_fleet_move_tyre.api_key')

            if not api_addr or not api_key:
                # errore parametri non trovati nelle config
                _logger.error(
                    "SEND_MISSING_TIRE_INFO ERROR: Mancano i parametri API all'interno delle impostazioni")
                raise UserError("Mancano i parametri API all'interno delle impostazioni")
            
            url = api_addr + "/tires/absent"

            payload = {
                'Tires': tire_list
            }
            resource = 'fleet.vehicle, ' + str(self.id)

            attrs = {
                'endpoint': url,
                'method': "POST",
                'resource_id': resource,
                'auth':"header_api_key",
                'key': "apikey",
                'value': api_key,
                'bearer_token':"",
                'user':"",
                'password':"",
                'server_action_id': self.env.ref("bloomup_fleet_move_tyre.action_reset_vehicle_queue").id,
                'payload': json.dumps(payload),
                'custom_header':"",
                'action_processed':"",
                'action_error':"",
                'response':"",
                'response_status':"",
            }
            self.env["external.rest.api.queue"].sudo().create(attrs)
            self.is_queueing = True
            return

        else:
            return
        
    def update_wheels(self, checklist_dict):
        """
        updates with data coming from netcheck
        """
        if not checklist_dict['front_wheel_id'] or not checklist_dict['rear_wheel_id']:
            raise UserError("Un tipo di pneumatico non è stato selezionato. Se il modello non è presente nel database, selezionare 'tipologia pneumatico mancante' e compilare le informazioni rilevanti")
        else:
            self.front_wheel = checklist_dict['front_wheel_id']
            self.rear_wheel = checklist_dict['rear_wheel_id']
            return





    # @api.constrains('front_wheel', 'rear_wheel')
    # def _check_wheels_set(self):
    #     if not self.front_wheel or not self.rear_wheel:
    #         raise UserError(_("Entrambe le tipologie di pneumatici devono essere inserite"))
        
    