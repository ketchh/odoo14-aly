from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging
import requests
import json

#API_SLICE = 200

_logger = logging.getLogger(__name__)

class TyreTire(models.Model):
    _name = "tyre.tire"
    _description = "Tire Type"

    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(
        string="Active",
        tracking=True,
        default=True
    )

    name = fields.Char(
        string="Name",
        tracking=True
    )

    brand = fields.Char(
        string="Brand",
        tracking=True
    )

    model = fields.Char(
        string="Model",
        tracking=True
    )

    supplier_tire_id = fields.Char(
        string="TyreTeam Tire ID",
        tracking=True
    )

    supplier_code = fields.Char(
        string="TyreTeam Code",
        tracking=True
    )

    producer_code = fields.Char(
        string="Producer Code",
        tracking=True
    )

    width = fields.Float(
        string="Width",
        tracking=True
    )

    section = fields.Char(
        string="Section",
        tracking=True
    )

    diameter = fields.Float(
        string="Diameter",
        tracking=True
    )

    load_index = fields.Char(
        string="Load Index",
        tracking=True
    )

    speed_index = fields.Char(
        string="Speed Index",
        tracking=True
    )

    season = fields.Selection(
        string="Brand",
        selection=[
            ('I', _('Winter')),
            ('E', _('Summer')),
            ('4', _('4 Seasons'))
        ],
        tracking=True
    )

    quality = fields.Selection(
        string="Type",
        selection=[
            ('Q', _('Normal Quality')),
            ('P', _('Premium'))
        ],
        tracking=True
    )

    technology = fields.Selection(
        string="Technology",
        selection=[
            ('RF', _('Run Flat')),
            ('SS', _('Self Sealing')),
            ('ST', _('Standard'))
        ],
        tracking=True
    )

    # dot = fields.Char(
    #     string="Year of production",
    #     tracking=True
    # )

    # axle = fields.Selection(
    #     string="Riferimento Assale",
    #     selection=[
    #         ('F', _("Assale anteriore")),
    #         ('B', _("Assale posteriore")),
    #         ('T', _("Pneumatici tutti uguali")),
    #         ('O', _("Altro"))
    #     ],
    #     tracking=True
    # )

    def get_name(self, width, section, diameter,load_index,speed_index, brand, model, season,technology):
        name = "{} / {} R{} {}{} {} {} {} {}".format(width,section,diameter,load_index,speed_index,brand, model, season,technology)
        
        return name       


    @api.model
    def update_tire_name(self):
        for record in self:
            record.name = self.get_name(record.width, record.section, record.diameter, record.load_index, record.speed_index, record.brand,record.model, record.season, record.technology)

    #creazione lista di pneumatici
    @api.model
    def _create_tires(self, list):
        """
        params: list of dictionaries
        Used both by external API and tyre_sync
        """
        for tire in list:
            #prima controllo se esiste già usando l'ID e creo lista di roba da aggiungere 
            id = tire['SupplierTireId']
            if not id or len(self.env['tyre.tire'].search([('supplier_tire_id', '=', id)])):
                continue

            name = self.get_name(tire["Width"], tire["Section"], tire['Diameter'], tire['LoadIndex'], tire['SpeedIndex'], tire['Brand'],tire['Model'],tire['Season'],tire['TyreTechnology'])
            #creo nuova anagrafica
            attrs = {
                'active': True,
                'name': name,
                'brand': tire["Brand"] if tire["Brand"] else False,
                'model': tire["Model"] if tire["Model"] else False,
                'supplier_tire_id': tire["SupplierTireId"] if tire["SupplierTireId"] else False,
                'supplier_code': tire["SupplierCode"] if tire["SupplierCode"] else False,
                'producer_code': tire["ProducerCode"] if tire["ProducerCode"] else False,
                'width': float(tire["Width"]) if tire["Width"] else 0.0,
                'section': tire["Section"] if tire["Section"] else False,
                'diameter': float(tire["Diameter"]) if tire["Diameter"] else 0.0,
                'load_index': tire["LoadIndex"] if tire["LoadIndex"] else False,
                'speed_index': tire["SpeedIndex"] if tire["SpeedIndex"] else False,
                'season': tire["Season"] if tire["Season"] in ['I', 'E', '4'] else False,
                'quality': tire["TyreTyre"] if tire["TyreTyre"] in ['Q', 'P'] else False,
                'technology': tire["TyreTechnology"] if tire["TyreTechnology"] in ['ST', 'SS', 'RF'] else False
            }

            tid = self.env['tyre.tire'].sudo().create(attrs)
            _logger.info("%s created", tid)
        return True

    #sincronizzazione anagrafiche pneumatici tramite API
    @api.model
    def cron_tire_sync(self):
        _logger.info(
            'EXECUTING CRON SYNC TIRE INFO')
        self.tire_sync()
        return True

    @api.model
    def tire_sync(self):
        _logger.info(
            'EXECUTING SYNC_TIRE_INFO')
        # prendo i parametri di Active sezione API nelle config
        api_addr = self.env['ir.config_parameter'].sudo(
        ).get_param('bloomup_fleet_move_tyre.api_addr')

        api_key = self.env['ir.config_parameter'].sudo(
        ).get_param('bloomup_fleet_move_tyre.api_key')

        api_seq = self.env['ir.config_parameter'].sudo(
        ).get_param('bloomup_fleet_move_tyre.api_seq')

        api_slice = self.env['ir.config_parameter'].sudo(
        ).get_param('bloomup_fleet_move_tyre.api_slice')

        if not api_addr or not api_key:
            # errore parametri non trovati nelle config
            _logger.error(
                "SYNC_TIRE_INFO ERROR: Mancano i parametri API all'interno delle impostazioni")
            raise ImportError("Mancano i parametri API all'interno delle impostazioni")

        url = api_addr + "/tires/summer"

        payload = ""
        headers = {
            'apikey': api_key
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        if response.status_code != 200:
            #errore chiamata api fallita
            _logger.error(
                response.text)
            raise ImportError(response.text)
        
        data = json.loads(response.text)
        list = data["tires"]

        #slicing response to avoid timeout)

        seq_start = int(api_seq)
        seq_end = int(api_seq) + int(api_slice)
        if seq_end > len(list)-1:
            #if we are at the end of the response e reset the index
            seq_end = len(list)-1
            self.env['ir.config_parameter'].sudo().set_param('bloomup_fleet_move_tyre.api_seq', 0)
        else:
            self.env['ir.config_parameter'].sudo().set_param('bloomup_fleet_move_tyre.api_seq', seq_end)

        self._create_tires(list[seq_start:seq_end])

        return    

    # def _get_tire_dict(self):
    #     self.ensure_one()
    #     ret = {
    #         'Width': str(self.width),
    #         'Section': self.section,
    #         'Diameter': str(self.diameter),
    #         'LoadIndex': self.load_index,
    #         'SpeedIndex': self.speed_index,
    #         'Season': self.season,
    #         'Axle': self.axle,
    #         'Qty': 2,
    #         'Quality': self.quality,
    #         'TyreTechnology': self.technology,
    #         'DOT': self.dot,
    #         'SupplierTyreId': self.supplier_tire_id
    #     }
    #     return ret