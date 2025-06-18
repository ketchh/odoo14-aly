# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import base64
import csv
import io
from datetime import datetime

class ConfigImporter(models.Model):
    _name = "fleet.move.config.importer"
    _description = "Config Importer"

    field_id = fields.Selection(
        string="Field",
        selection=[

            ('pickup_company_type', _('Pickup Address Type')),
            ('pickup_name', _('Pickup Address Name')),
            ('pickup_reference', _('Pickup Address Reference')),
            ('pickup_firstname', _('Pickup First Name')),
            ('pickup_lastname', _('Pickup Last Name')),
            ('pickup_street', _('Pickup Address')),
            ('pickup_street2', _('Pickup Address Number')),
            ('pickup_city', _('Pickup Address City')),
            ('pickup_state_id', _('Pickup Address State')),
            ('pickup_state_id_code', _('Pickup Address State Code')),
            ('pickup_zip', _('Pickup Address Zip')),
            ('pickup_country_id', _('Pickup Address Country')),
            
            ('email_fleetmanager', _('E-mail Fleet Manager')),
            ('phone_fleetmanager', _('Telefono Fleet Manager')),
            ('name_fleetmanager', _('Nome Fleet Manager')),
            ('email_customer', _('E-mail Cliente')),
            ('phone_customer', _('Telefono Cliente')),
            ('name_customer', _('Nome Cliente')),
            ('contract_code', _('Codice Contratto')),
            ('order_number', _('Numero Ordine')),
            ('move_typology', _('Tipologia Movimentazione')),
            ('distance_km', _('Distanza')),
            ('distance_time', _('Tempo Percorrenza')),

            ('delivery_company_type', _('Delivery Address Type')),
            ('delivery_name', _('Delivery Address Name')),
            ('delivery_reference', _('Delivery Address Reference')),
            ('delivery_firstname', _('Delivery Address First Name')),
            ('delivery_lastname', _('Delivery Address Last Name')),
            ('delivery_street', _('Delivery Address')),
            ('delivery_street2', _('Delivery Address Number')),
            ('delivery_city', _('Delivery Address City')),
            ('delivery_state_id', _('Delivery Address State')),
            ('delivery_state_id_code', _('Delivery Address State Code')),
            ('delivery_zip', _('Delivery Address Zip')),
            ('delivery_country_id', _('Delivery Address Country')),
            
            ('vehicle_plate', _('Vehicle Plate')),
            ('vehicle_brand', _('Vehicle Brand')),
            ('vehicle_model', _('Vehicle Model')),
            ('vehicle_vin_sn', _('Vehicle SN')),

            #Veicolo Contestuale
            ('contex_vehicle_plate', _('Targa Contestuale')),
            ('contex_vehicle_brand', _('Marca Contestuale')),
            ('contex_vehicle_model', _('Modello Contestuale')),
            ('contex_vehicle_vin_sn', _('Telaio Contestuale')),
            
            #Altri campi
            ('notes',_('Note')),
            ('confirmed_date',_('Data di conferma')),
            ('sales_request_date', _('Data Richiesta Sales')),
            ('op_sent_date', _('Data Invio Operatore')),
            ('timeslot', _('Fascia Oraria'))

        ]
    )
    name = fields.Char(
        string="Field csv"
    )
    partner_id = fields.Many2one('res.partner', string='Azienda')

class ResPartner(models.Model):
    _inherit = "res.partner"

    csv_configuration = fields.One2many(
        comodel_name='fleet.move.config.importer', 
        inverse_name='partner_id', 
        string='Csv Configuration'
    )
    input_file = fields.Binary(string="Csv")
    delimiter = fields.Char(string="Delimiter", default=';')
    message = fields.Char(string="Errore")

    def get_field(self):
        self.ensure_one()
        attrs = {}
        for res in dict(self.env['fleet.move.config.importer']._fields['field_id'].selection):
            attrs[res] = self.csv_configuration.filtered(lambda x: x.field_id == res)
        return attrs
    
    def return_values(self, fields, selection, line, header):
        results = {}
        for field in fields:
            results[field] = line[header.index(selection.get(field).name)] if selection.get(field) else False
        return results 

    def import_file(self):
        for record in self:
            if not record.input_file:
                return
            output = base64.b64decode(record.input_file).decode("utf-8")
            output = io.StringIO(output)
            reader = csv.reader(output, delimiter=record.delimiter)
            i = 0
            header = []
            selection = record.get_field()

            msg = []
            for line in reader:
                if i == 0:
                    header = line
                    i+=1
                else:
                    import pprint
                    i+=1
                    # prendere i campi 
                    # auto
                    fields = [
                        'vehicle_plate', 
                        'vehicle_brand', 
                        'vehicle_model', 
                        'vehicle_vin_sn'
                    ]
                    auto = self.return_values(fields, selection, line, header)
                    if not auto['vehicle_plate'] or not auto['vehicle_brand'] or not auto['vehicle_model']:
                        msg.append('Riga %s (errore veicolo): manca un campo tra Targa, Modello, Marca' % i)
                        continue
                    auto_add = self.env['fleet.vehicle'].search([
                        ('license_plate', '=', auto['vehicle_plate']),
                        ('owner_id', '=', record.id)
                    ])
                    if not auto_add:
                        brand = self.env['fleet.vehicle.model.brand'].sudo().search([
                            ('name', '=ilike', auto['vehicle_brand'])
                        ],limit=1) 
                        if not brand:
                            brand = self.env['fleet.vehicle.model.brand'].sudo().create({
                                'name': auto['vehicle_brand']
                            })
                        model = self.env['fleet.vehicle.model'].sudo().search([
                            ('name', '=ilike', auto['vehicle_model'], )
                        ], limit=1)
                        if not model:
                            model = self.env['fleet.vehicle.model'].sudo().create({
                                'name': auto['vehicle_model'],
                                'brand_id': brand.id
                            })
                        auto_add = self.env['fleet.vehicle'].create({
                            'model_id': model.id,
                            'license_plate': auto['vehicle_plate'],
                            'vin_sn': auto['vehicle_vin_sn'],
                            'owner_id': record.id
                        })

                    #auto contestuale
                    fields = [
                        'contex_vehicle_plate', 
                        'contex_vehicle_brand', 
                        'contex_vehicle_model', 
                        'contex_vehicle_vin_sn'
                    ]

                    auto_contex = self.return_values(fields, selection, line, header)
                    
                    if auto_contex['contex_vehicle_plate']:
                        if not auto_contex['contex_vehicle_brand'] or not auto_contex['contex_vehicle_model']:
                            msg.append('Riga %s (errore veicolo): manca un campo tra Modello, Marca del contestuale' % i)
                            continue
                            
                        contex_auto_add = self.env['fleet.vehicle'].search([
                            ('license_plate', '=', auto_contex['contex_vehicle_plate']),
                            ('owner_id', '=', record.id)
                        ])
                        if not contex_auto_add:
                            brand = self.env['fleet.vehicle.model.brand'].sudo().search([
                                ('name', '=ilike', auto_contex['contex_vehicle_brand'])
                            ], limit=1) 
                            if not brand:
                                brand = self.env['fleet.vehicle.model.brand'].sudo().create({
                                    'name': auto_contex['contex_vehicle_brand']
                                })
                            model = self.env['fleet.vehicle.model'].sudo().search([
                                ('name', '=ilike', auto_contex['contex_vehicle_model'], )
                            ], limit=1)
                            if not model:
                                model = self.env['fleet.vehicle.model'].sudo().create({
                                    'name': auto_contex['contex_vehicle_model'],
                                    'brand_id': brand.id
                                })
                            contex_auto_add = self.env['fleet.vehicle'].create({
                                'model_id': model.id,
                                'license_plate': auto_contex['contex_vehicle_plate'],
                                'vin_sn': auto_contex['contex_vehicle_vin_sn'],
                                'owner_id': record.id
                            })
                    else:
                        contex_auto_add = False

                    # prelievo
                    fields = [
                        'pickup_company_type',
                        'pickup_name',
                        'pickup_reference',
                        'pickup_firstname',
                        'pickup_lastname',
                        'pickup_street',
                        'pickup_street2', 
                        'pickup_city',
                        'pickup_state_id',
                        'pickup_state_id_code',
                        'pickup_zip',
                        'pickup_country_id'
                    ]
                    pickup = self.return_values(fields, selection, line, header)
                    if not pickup['pickup_name'] and not pickup['pickup_firstname'] and not pickup['pickup_lastname']:
                        msg.append('Riga %s (errore Indirizzo prelievo): Manca il nome dell\'azienda o il nome e cognome' % i)
                    
                    state_id = False
                    
                    if pickup['pickup_state_id']:
                        state_id = self.env['res.country.state'].with_context({'lang':self.env.user.lang}).sudo().search([
                            ('name', '=ilike', pickup['pickup_state_id']),
                            ('country_id.code', '=', 'IT')
                        ], limit=1)
                    elif pickup['pickup_state_id_code']:
                        state_id = self.env['res.country.state'].with_context({'lang':self.env.user.lang}).sudo().search([
                            ('code', '=ilike', pickup['pickup_state_id_code']),
                            ('country_id.code', '=', 'IT')
                        ], limit=1)
                        # if not state_id:
                        #     msg.append('Whoops! Alla riga %s manca la provincia' % i)                    



                    # pickup_add = self.env['fleet.partner'].search([
                    #     ('name', '=ilike', pickup['pickup_name']),
                    #     ('owner_id', '=', record.id)
                    # ])
                    # if not pickup_add:
                    #     pickup_add = self.env['fleet.partner'].search([
                    #     ('firstname', '=ilike', pickup['pickup_firstname']),
                    #     ('lastname', '=ilike', pickup['pickup_lastname']),
                    #     ('owner_id', '=', record.id)
                    # ])

                    # COMMENTO IL VECCHIO CODICE PER PROVARE UNA NUOVA STRATEGIA:
                    # cerco l'indirizzo per address, se non lo trovo lo creo 
                    # (serve ad evitare movimentazioni con la stessa partenza
                    #  in piattaforma, perché la società è la stessa ma non la stessa persona)

                    # pickup_add = self.env['fleet.partner'].search([
                    #     ('street', '=ilike', pickup['pickup_street']),
                    #     ('owner_id', '=', record.id)
                    
                    # ])
                    
                    pickup_add = False

                    if not pickup_add:
                        attrs = {
                            'owner_id': record.id,
                            'street': pickup['pickup_street'],
                            'street2': pickup['pickup_street2'],
                            'city': pickup['pickup_city'],
                            'state_id': state_id.id if state_id else False,
                            'country_id': state_id.country_id.id if state_id else False,
                            'zip': pickup['pickup_zip'],
                            'reference': pickup['pickup_reference'],
                            'company_type': pickup['pickup_company_type'] if pickup['pickup_company_type'] else 'company'
                        }
                        if pickup['pickup_name']:
                            attrs['name'] = pickup['pickup_name']
                        else:
                            attrs['firstname'] = pickup['pickup_firstname']
                            attrs['lastname'] = pickup['pickup_lastname']
                        pickup_add = self.env['fleet.partner'].create(attrs)
                    

                    
                    # consegna
                    fields = [
                        'delivery_company_type',
                        'delivery_name',
                        'delivery_reference',
                        'delivery_firstname',
                        'delivery_lastname',
                        'delivery_street',
                        'delivery_street2', 
                        'delivery_city',
                        'delivery_state_id',
                        'delivery_state_id_code',
                        'delivery_zip',
                        'delivery_country_id',
                    ]

                    delivery = self.return_values(fields, selection, line, header)
                    if not delivery['delivery_name'] and not delivery['delivery_firstname'] and not delivery['delivery_lastname']:
                        msg.append('Riga %s (errore Indirizzo consegna): Manca il nome dell\'azienda o il nome e cognome' % i)
                    state_id = False
                    if delivery['delivery_state_id']:
                        state_id = self.env['res.country.state'].with_context({'lang':self.env.user.lang}).sudo().search([
                            ('name', '=ilike', delivery['delivery_state_id']),
                            ('country_id.code', '=', 'IT')
                        ], limit=1)
                    elif delivery['delivery_state_id_code']:
                        state_id = self.env['res.country.state'].with_context({'lang':self.env.user.lang}).sudo().search([
                            ('code', '=ilike', delivery['delivery_state_id_code']),
                            ('country_id.code', '=', 'IT')
                        ], limit=1)
                        # if not state_id:
                        #     msg.append('Riga %s (errore Indirizzo consegna): Manca la provincia' % i)
                            
                    # delivery_add = self.env['fleet.partner'].search([
                    #     ('name', '=ilike', delivery['delivery_name']),
                    #     ('owner_id', '=', record.id)
                    # ])

                    # delivery_add = self.env['fleet.partner'].search([
                    #     ('street', '=ilike', delivery['delivery_street']),
                    #     ('owner_id', '=', record.id)
                    # ])
                    delivery_add = False
                    
                    if not delivery_add:
                        attrs = {
                            'owner_id': record.id,
                            'street': delivery['delivery_street'],
                            'street2': delivery['delivery_street2'],
                            'city': delivery['delivery_city'],
                            'state_id': state_id.id if state_id else False,
                            'country_id': state_id.country_id.id if state_id else False,
                            'zip': delivery['delivery_zip'],
                            'reference': delivery['delivery_reference'],
                            'company_type': delivery['delivery_company_type'] if delivery['delivery_company_type'] else 'company'
                        }
                        if delivery['delivery_name']:
                            attrs['name'] = delivery['delivery_name']
                        else:
                            attrs['firstname'] = delivery['delivery_firstname']
                            attrs['lastname'] = delivery['delivery_lastname']
                        delivery_add = self.env['fleet.partner'].create(attrs)
                    
                    #Altri campi
                    fields = [
                        'email_fleetmanager',
                        'phone_fleetmanager',
                        'name_fleetmanager',
                        'email_customer',
                        'phone_customer',
                        'name_customer',
                        'contract_code',
                        'order_number',
                        'move_typology',
                        'distance_km',
                        'distance_time',
                        'op_sent_date',
                        'notes',
                        'sales_request_date',
                        'timeslot',
                        'confirmed_date'
                    ]

                    additional_fields = self.return_values(fields, selection, line, header)
                    


                    attrs = {
                        'partner_id': record.id,
                        'pickup_address': pickup_add[0].id if pickup_add else False,
                        'delivery_address': delivery_add[0].id if delivery_add else False,
                        'vehicle_id': auto_add[0].id,
                        'contextual_vehicle_id': contex_auto_add[0].id if contex_auto_add else False,
                        'email_fleetmanager': additional_fields['email_fleetmanager'],
                        'phone_fleetmanager': additional_fields['phone_fleetmanager'],
                        'name_fleetmanager': additional_fields['name_fleetmanager'],
                        'email_customer': additional_fields['email_customer'],
                        'phone_customer': additional_fields['phone_customer'],
                        'name_customer': additional_fields['name_customer'],
                        'contract_code': additional_fields['contract_code'],
                        'order_number': additional_fields['order_number'],
                        'move_typology': additional_fields['move_typology'],
                        'distance': additional_fields['distance_km'],
                        'distance_time': additional_fields['distance_time'],
                        'op_sent_date': additional_fields['op_sent_date'],
                        'note':additional_fields['notes'],
                        'request_date':additional_fields['sales_request_date'],
                        'upload_date':datetime.now(),
                        'timeslot':additional_fields['timeslot'],
                        'confirmed_date':additional_fields['confirmed_date']
                    }
                    self.env['fleet.move'].create(attrs)
            
                
            record.input_file = False
            record.message = '\n,'.join(msg)

