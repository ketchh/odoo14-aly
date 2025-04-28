from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class TyreRepairer(models.Model):
    _name = "tyre.repairer"
    _description = "Tyre Repairer"
    
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    found = fields.Boolean(
        string="Found",
        default=True,
        tracking=True,
    )
    active = fields.Boolean(
        string="Active",
        tracking=True,
        default=True
    )
    company_id = fields.Many2one(
        'res.company', 
        required=True, 
        readonly=True, 
        default=lambda self: self.env.company
    )
    name = fields.Char(
        string="Name",
        tracking=True
    )
    customer_center = fields.Char(
        string="Customer Center",
        tracking=True
    )
    latitude = fields.Char(
        string="Latitude",
        tracking=True
    )
    longitude = fields.Char(
        string="Longitude",
        tracking=True
    )
    date_localization = fields.Date(
        string="Date Localization",
        tracking=True
    )
    vat = fields.Char(
        string="Vat",
        tracking=True
    )
    address = fields.Char(
        string="Address",
        tracking=True
    )
    cap = fields.Char(
        string="Cap",
        tracking=True
    )
    city = fields.Char(
        string="City",
        tracking=True
    )
    country_id = fields.Many2one(
        string="Country",
        comodel_name="res.country",
        tracking=True
    )
    state_id = fields.Many2one(
        string="Province",
        comodel_name="res.country.state",
        tracking=True
    )
    region = fields.Char(
        string="Region",
        tracking=True
    )
    phone = fields.Char(
        string="Phone",
        tracking=True
    )
    email = fields.Char(
        string="E-mail",
        tracking=True
    )
    network = fields.Char(
        string="Network",
        tracking=True
    )
    adesione_pw_totali = fields.Char(
        string="Adesione PW totali",
        tracking=True
    )
    status_description = fields.Char(
        string="Status description",
        tracking=True
    )
    
    def geo_localize(self):
        """
        The function `geo_localize` is used to geolocate partners by their address
        and update their latitude and longitude coordinates, and it also sends a
        notification if no match is found for any partner's address.
        :return: a boolean value of True.
        """
        
        partners_not_geo_localized = self.env['tyre.repairer']
        for partner in self.with_context(lang='en_US'):
            result = self._geo_localize(partner.address,
                                        partner.cap,
                                        partner.city,
                                        partner.state_id.name,
                                        partner.country_id.name)
            
            if result:
                partner.write({
                    'latitude': result[0],
                    'longitude': result[1],
                    'date_localization': fields.Date.context_today(partner)
                })
            else:
                partners_not_geo_localized |= partner
        
        if partners_not_geo_localized:
            self.env['bus.bus']._sendone(self.env.user.partner_id, 'simple_notification', {
                'title': _("Warning"),
                'message': _('No match found for %(partner_names)s address(es).', partner_names=', '.join(partners_not_geo_localized.mapped('name')))
            })
            partner.write({
                'latitude': 0,
                'longitude': 0,
                'date_localization': fields.Date.context_today(partner)
            })
        return True

    @api.model
    def _geo_localize(self, street='', zip='', city='', state='', country=''):
        """
        The function `_geo_localize` uses a geocoder object to query and find the
        geographic location based on the provided address parameters.
        
        :param street: The street parameter is used to specify the street address of
        the location you want to geolocate
        :param zip: The "zip" parameter refers to the postal code or ZIP code of the
        address
        :param city: The city parameter is used to specify the name of the city for
        which you want to perform the geolocation
        :param state: The "state" parameter refers to the state or province of the
        address. It is typically used in combination with the "city" parameter to
        provide a more specific location
        :param country: The "country" parameter represents the country where the
        address is located. It is used to specify the country when querying the
        geocoder for address information
        :return: the result of the geocoding process, which is the location
        information (latitude and longitude) of the given address.
        """
        geo_obj = self.env['base.geocoder']
        search = geo_obj.geo_query_address(street=street, zip=zip, city=city, state=state, country=country)
        result = geo_obj.geo_find(search, force_country=country)
        if result is None:
            search = geo_obj.geo_query_address(city=city, state=state, country=country)
            result = geo_obj.geo_find(search, force_country=country)
        return result

    @api.model
    def get_tyre_repairers(self, bounds, loaded_markers):
        """
        The function `get_tyre_repairers` retrieves a list of tyre repairers within
        a given geographical boundary and returns information about each repairer,
        including their name, geographical coordinates, and whether they are a part
        of the "G - TYRE TEAM" network.
        
        :param bounds: The 'bounds' parameter is a dictionary that contains latitude
        and longitude boundaries for searching tyre repairers. 
        :return: a list of dictionaries, where each dictionary represents a marker.
        Each marker has the following properties:
        - 'name': the name of the tyre repairer
        - 'tyreteam': a boolean indicating if the tyre repairer is part of the 'G -
        TYRE TEAM' network
        - 'geo': a dictionary containing the latitude and longitude of the tyre
        repairer
        - 'favorite_customers': a list of customer id that represents if this customer has 
        the tyre repairer in his favorite list.
        """
        
        results = self.search([
            ('latitude','>=',float(bounds['lat']['lo'])),
            ('latitude','<=', float(bounds['lat']['hi'])),
            ('longitude', '>=', float(bounds['lng']['lo'])),
            ('longitude','<=', float(bounds['lng']['hi'])),
            ('id','not in', [s['id'] for s in loaded_markers])
        ])
        codes = results.mapped('customer_center')
        favorites = self.env['tyre.repairer.favorite'].search([
            ('tyre_repairer_code','in',codes)
        ])
        markers =[
            {
                'id':x.id,
                'name':x.name,
                'address': "%s %s" % (x.address, x.city),
                'tyreteam': True if x.network.strip() == 'G - TYRE TEAM' else False,
                'geo':{
                    'lat': float(x.latitude),
                    'lng': float(x.longitude)
                }, 
                'favorite_customers': [c.customer_id.id if c.customer_id else '' for c in favorites if c.tyre_repairer_code==x.customer_center]
            } for x in results
        ]
        return markers
    
class TyreRepairerRadius(models.Model):
    _name="tyre.repairer.radius"
    _description="Tyre Repairer Radius"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    cap = fields.Char(
        string="Zip",
        tracking=True
    )
    radius = fields.Integer(
        string="Radius",
        tracking=True
    )
    
class TyreRepairerFavorites(models.Model):
    _name = "tyre.repairer.favorite"
    _description = "Tyre Repairer Favorite"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    customer_code = fields.Char(
        string="Customer Code",
        tracking=True
    )
    tyre_repairer_code = fields.Char(
        string="Tyre Repairer Code",
        tracking=True
    )
    customer_name = fields.Char(
        string="Customer Name",
        tracking=True
    )
    tyre_repairer_name = fields.Char(
        string="Tyre repairer name",
        tracking=True
    )
    customer_id = fields.Many2one(
        string="Customer Partner",
        comodel_name="res.partner",
        compute="_compute_customer_partner"
    )
    
    def _compute_customer_partner(self):
        for record in self:
            record.customer_id = False
            res = self.env['res.partner'].search([('ref','=',record.customer_code)])
            if res:
                record.customer_id = res[0].id