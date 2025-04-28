# -*- coding: utf-8 -*-
from werkzeug import urls, utils
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, AccessError, MissingError, UserError
from odoo.http import content_disposition, Controller, request, route
from werkzeug.exceptions import NotFound, Forbidden
import werkzeug

class VehicleUser(Controller):
    @route('/my/vehicles', type='http', auth='user', website=True)
    def vehicle(self):
        """
        Pagina dell'app per vedere e inserire i veicoli della propria azienda
        """
        if request.lang.code != request.env.user.lang:
            request.env.user.lang = request.lang.code
        values = {}
        return request.render("bloomup_fleet_move.my_vehicle", values)
    
    @route('/my/fleet-addresses', type='http', auth='user', website=True)
    def addresses(self):
        if request.lang.code != request.env.user.lang:
            request.env.user.lang = request.lang.code
        values = {}
        return request.render("bloomup_fleet_move.my_addresses", values)

    @route('/my/move-requests', type='http', auth='user', website=True)
    def move_requests(self):
        if request.lang.code != request.env.user.lang:
            request.env.user.lang = request.lang.code
        values = {}
        return request.render("bloomup_fleet_move.my_move", values)
    