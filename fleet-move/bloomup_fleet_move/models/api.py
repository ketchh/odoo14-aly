from odoo import _, api, fields, models
from odoo.addons.bloomup_owl_components.models.store import AVAILABLE_MODEL
import time
import re
from odoo.osv import expression

REGEX_MAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
AVAILABLE_MODEL = ["fleet.vehicle", "fleet.move", "fleet.partner"]
 
class ResPArtner(models.Model):
    _inherit = "res.partner"

    ############ VEICOLI ############
    @api.model
    def add_modify_vehicle(self, args):
        """
        Gestice la modifica o l'aggiunta di un nuovo veicolo

        se Produttore e modello non esistono vengono creati
        """
        partner = self.env.user.partner_id
        owner = partner.id
        if partner.parent_id:
            owner = partner.parent_id.id
        # Verifico produttore e modello
        # se non ci sono li creo
        if 'id' in args:
            vehicle_id = args.pop('id')
        else:
            vehicle_id = False
        brand_id = args.get('brand_id')
        model_id = args.get('model_id')
        brand = False
        model = False
        try:
            if brand_id:
                brand = self.env['fleet.vehicle.model.brand'].sudo().search([
                    ('name', '=ilike', brand_id)
                ]) 
            if model_id:   
                model = self.env['fleet.vehicle.model'].sudo().search([
                    ('name', '=ilike', model_id)
                ])
            if (brand and len(brand)>1) or (model and len(model)>1):
                return {'error': """C'è stato un errore inatteso, 
                        contattaci per risolverlo [error 5000]"""}
            if not brand and brand_id:
                brand = self.env['fleet.vehicle.model.brand'].sudo().create({
                    'name': brand_id
                })
            if not model and model_id and brand:
                model = self.env['fleet.vehicle.model'].sudo().create({
                    'name': model_id,
                    'brand_id': brand.id
                })
            if brand:
                args['brand_id'] = brand.id
            if model:
                args['model_id'] = model.id
            
            if vehicle_id:
                vehicle = self.env['fleet.vehicle'].sudo().browse(vehicle_id)
                if vehicle.owner_id.id != owner:
                    return {'error': """C'è stato un errore inatteso, 
                        contattaci per risolverlo [error 5001]"""}
                
                if not vehicle:
                    return {'error': """C'è stato un errore inatteso, 
                        contattaci per risolverlo [error 5002]"""}
                
                vehicle.sudo().write(args)
                return {'success': 'Modifica avvenuta con successo.'}
            args['owner_id'] = owner
            
            self.env['fleet.vehicle'].sudo().create(args)
            return {'success': 'Veicolo creato con successo.'}
        except:
            return {'error': """C'è stato un errore inatteso, 
                        contattaci per risolverlo [error 5003]"""}
        
    ############ INDIRIZZI ############

    @api.model
    def add_modify_address(self, record_id):
        """
        Gestice la modifica o l'aggiunta di un nuovo veicolo
        """
        partner = self.env.user.partner_id
        owner = partner.id
        if partner.parent_id:
            owner = partner.parent_id.id
        try:
            address = False
            if record_id.get('id'):
                address = self.env['fleet.partner'].sudo().browse(record_id.get('id'))
                if not address:
                    return {'error': """C'è stato un errore inatteso, 
                            contattaci per risolverlo [error 6000]"""}
                if address.owner_id.id != owner:
                    return {'error': """C'è stato un errore inatteso, 
                            contattaci per risolverlo [error 6001]"""}
                del record_id['id']
            validation_errors = {'validation_errors': {}}
            error = False
            if record_id.get('company_type') and record_id.get('company_type') == 'company':
                if 'firstname' in record_id:
                    del record_id['firstname']
                if 'lasrname' in record_id:
                    del record_id['lastname']
            else:
                if 'name' in record_id:
                    del record_id['name']
            if record_id.get('email') and not re.fullmatch(REGEX_MAIL, record_id.get('email')):
                error = True
                validation_errors['validation_errors']['email'] = 'Inserisci un\'email valida.'
            if error:
                return validation_errors
            
            # cerca provincia e nazione
            if record_id.get('country_id'):
                country_id = self.env['res.country'].with_context({'lang':self.env.user.lang}).sudo().search([
                    ('name', '=ilike', record_id.get('country_id'))
                ])
                if not country_id:
                    return {'error': """C'è stato un errore inatteso, 
                            contattaci per risolverlo [error 6002]"""}
                record_id['country_id'] = country_id[0].id
            if record_id.get('state_id'):
                state_id = self.env['res.country.state'].with_context({'lang':self.env.user.lang}).sudo().search([
                    ('name', '=ilike', record_id.get('state_id'))
                ])
                if not state_id:
                    return {'error': """C'è stato un errore inatteso, 
                            contattaci per risolverlo [error 6003]"""}
                record_id['state_id'] = state_id[0].id
            if address:
                address.with_context({'lang':self.env.user.lang}).sudo().write(record_id)
                return {'success': "Indirizzo modificato con successo."}
            else:
                record_id['owner_id'] = owner
                self.env['fleet.partner'].with_context({'lang':self.env.user.lang}).sudo()\
                    .create(record_id)
                return {'success': "Indirizzo creato con successo."}
        except:
            return {'error': """C'è stato un errore inatteso, 
                        contattaci per risolverlo [error 6005]"""}
    
    
    ############ GENERICHE ############
    @api.model
    def get_records(self, model=False, fields=['id','name'], page=1, order="id desc", limit=8, domain=[]):
        if model not in AVAILABLE_MODEL:
            return False
        partner = self.env.user.partner_id
        owner = partner.id
        if partner.parent_id:
            owner = partner.parent_id.id
        if page<=1:
            offset=0
        elif page > 1:
            offset = limit * (page-1)
        original_domain = domain
        ## metto l'owner ##
        domain = [('owner_id', '=', owner)]
        if model == "fleet.move":
            domain = [('partner_id', '=', owner)]
        if model == "fleet.vehicle":
            domain = [
                ('owner_id', '=', owner),
                ('cancel_from_user', '=', False)
            ]
        ###################
        final_domain = domain
        if original_domain:
            final_domain = expression.AND([
                domain,
                original_domain
            ])
        results =  super(ResPArtner, self).get_records(
            model=model,
            fields=fields,
            page=page,
            order=order,
            limit=limit,
            domain=final_domain
        )
        return results
    
    @api.model
    def cancel_record(self, model=False, record_id=False):
        if model not in AVAILABLE_MODEL:
            return {'error': "C'è stato un errore imprevisto."}
        partner = self.env.user.partner_id
        owner = partner.id
        if partner.parent_id:
            owner = partner.parent_id.id
        if not model or not record_id:
            return {'error': "C'è stato un errore imprevisto."}
        try:
            record = self.env[model].sudo().with_context({'lang':self.env.user.lang}).browse(record_id)
            ## metto l'owner ##
            field = 'owner_id'
            if model == "fleet.move":
                field = 'partner_id'
            ###################
            if record[field].id == owner:
                if model == 'fleet.move':
                    ## cerco lo stato annullato ##
                    cancel_state = self.env['fleet.move.status'].sudo().search([
                        ('cancel_user', '=', True)
                    ], limit=1)
                    if cancel_state:
                        record.sudo().state = cancel_state.id
                if model == 'fleet.vehicle':
                    record.sudo().cancel_from_user = True
                if model == 'fleet.partner':
                    record.sudo().active = False
                return True
        except:
            return {'error': "C'è stato un errore imprevisto."}

    @api.model
    def get_data_record(self, model=False, record_id=False, fields=['id','name']):
        if model not in AVAILABLE_MODEL:
            return False
        partner = self.env.user.partner_id
        owner = partner.id
        if partner.parent_id:
            owner = partner.parent_id.id
        ## metto l'owner ##
        field = 'owner_id'
        if model == "fleet.move":
            field = 'partner_id'
        ###################
        data = self.env[model].sudo().with_context({'lang':self.env.user.lang}).browse(record_id)
       
        if data[field].id != owner:
            return False
        return super(ResPArtner, self).get_data_record(
            model=model,
            record_id=record_id,
            fields=fields
        )
    
    @api.model
    def save_record(self, model=False, args=False):
        if model not in AVAILABLE_MODEL:
            return False
        if model == 'fleet.vehicle':
            return self.add_modify_vehicle(args)
        if model == 'fleet.partner':
            return self.add_modify_address(args)
        if model == 'fleet.move':
            return self.add_move(args)
        return False
    
    @api.model
    def add_move(self, args):
        partner = self.env.user.partner_id
        owner = partner.id
        if partner.parent_id:
            owner = partner.parent_id.id
        vehicle = args.get('vehicle_id')
        pickup = args.get('pickup_address')
        delivery = args.get('delivery_address')
        if not vehicle or not pickup or not delivery:
            return {'error': "C'è stato un errore imprevisto."}
        res_vehicle = self.env['fleet.vehicle'].sudo().name_search(vehicle)
        vehicle_id = False
        pickup_id = False
        delivery_id = False
        if len(res_vehicle)>0:
            for v in res_vehicle:
                ve = self.env['fleet.vehicle'].sudo().browse(v[0])
                if ve.owner_id.id == owner:
                    vehicle_id = ve.id
        res_pickup = self.env['fleet.partner'].sudo().search([('owner_id', '=', owner)])
        if res_pickup:
            for pick in res_pickup:
                if pickup == pick.display_name.upper():
                    pickup_id = pick.id
                    if delivery_id:
                        break
                if delivery == pick.display_name.upper():
                    delivery_id = pick.id
                    if pickup_id:
                        break
        
        if not delivery_id or not pickup_id or not vehicle_id:
            return {'error': "C'è stato un errore imprevisto."}
        
        attrs = {
            'vehicle_id': vehicle_id,
            'pickup_address': pickup_id,
            'delivery_address': delivery_id,
            'partner_id': owner
        }
        self.env['fleet.move'].sudo().create(attrs)
        return {'success': "Movimentazione creata con successo."}

    ############ IL BADGE NELLA DASHBOARD ############
    @api.model
    def get_badge(self, model, field):
        """
        Ritorna il numero di righe per model
        - model: nome modello
        - field: campo OWNER che rappresenta il proprietario
        """
        partner = self.env.user.partner_id
        owner = partner.id
        if partner.parent_id:
            owner = partner.parent_id.id
        domain = [
            (field, '=', owner)
        ]
        if model == 'fleet.vehicle':
            domain.append(('cancel_from_user', '=', False))

        count = self.env[model].sudo().search_count(domain)
        return count

    @api.model
    def owl_autocomplete(self, model, text, 
        depends_model, depends_field, depends_value):
        """
        Override per indirizzi
        """
        partner = self.env.user.partner_id
        owner = partner.id
        if partner.parent_id:
            owner = partner.parent_id.id
        if model=='fleet.partner':
            domain = [
                '&',
                ('owner_id', '=', owner),
                '|',
                ('name', '=ilike', '%'+text+'%'),
                ('street', '=ilike', '%'+text+'%')
            ]
            results = self.env[model].sudo().with_context({'lang':self.env.user.lang}).search(domain)
            response = []
            for res in results:
                response.append(res.with_context({'lang':self.env.user.lang}).display_name.upper())
            return response
        if model=='fleet.vehicle':
            domain = [
                '&',
                ('owner_id', '=', owner),
                '|',
                ('name', '=ilike', '%'+text+'%'),
                ('license_plate', '=ilike', '%'+text+'%')
            ]
            results = self.env[model].sudo().with_context({'lang':self.env.user.lang}).search(domain)
            response = []
            for res in results:
                response.append(res.with_context({'lang':self.env.user.lang}).display_name.upper())
            return response
        return super(ResPArtner, self).owl_autocomplete(model, text, 
            depends_model, depends_field, depends_value)