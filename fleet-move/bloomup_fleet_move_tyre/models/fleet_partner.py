from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)

class FleetPartner(models.Model):
    _inherit="fleet.partner"
    
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

    parking_id = fields.Char(
        string="Tyre team parking id",
        tracking=True
    )
    
    def geo_localize(self):
        """
        The function `geo_localize` is used to geolocate partners by their address
        and update their latitude and longitude coordinates, and it also sends a
        notification if no match is found for any partner's address.
        :return: a boolean value of True.
        """
        
        partners_not_geo_localized = self.env['fleet.partner']
        for partner in self.with_context(lang='en_US'):
            result = self._geo_localize(partner.street,
                                        partner.zip,
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