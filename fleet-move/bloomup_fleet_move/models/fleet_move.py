# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging
import datetime
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class FleetMove(models.Model):
#region DOCUMENTAZIONE
    """
    Richieste di movimentazione auto

    -----
    Gli utenti portali possono fare una richiesta dal front-end
    -----

    active : bool
        attivo si/no
    name : str
        sequenza
    request_date : datetime
        data avvenuta richiesta
    request_date_copy : datetime
        serve per i filtri current_month
    confirmed_date : datetime
        data concordata con il driver
    user_id : m2o->res.users
        utente che fa la richiesta default:utente corrente
    partner_id : m2o->res.partner
        azienda/contatto a cui è associata la richiesta (
            es: user_id è matteo che lavora per Pippo srl,
            partner_id è Pippo srl.
        ) non sono direttamente collegati user_id e partner_id,
        in quanto user_id può essere un utente interno ad Odoo
        e non necessariamente un dipendente di partner_id.
    pickup_address/delivery_address : m2o->fleet.partner
        indirizzi di prelievo e consegna, devono essere figli di partner_id(owner_id)
    vehicle_id : m2o->fleet.vehicle
        mezzo/automobile della richiesta, deve essere posseduto da partner_id(owner_id)
    note : str
        note varie, attesa stato veicolo, qualsiasi altra cosa
    employee_id : m2o->hr.employee
        dipendente di Odoo / Vettore che porterà l'auto da pickup a delivery
    state : m2o->fleet.move.status
        stato/fase. quando passa in una fase può partire l'action server dello stato.
    primary_color: str
        related a state.primary_color per colorare la kanban
    """
#endregion
    
    _name = "fleet.move"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Fleet Move"

    active = fields.Boolean(
        string='Active',
        tracking=True,
        copy=False,
        default=True
    )
    name = fields.Char(
        tracking = True,
        string='Name', 
        copy=False,
        default="New move"
    )
    upload_date = fields.Datetime(
        tracking = True,
        string='Upload Datetime',
        copy=False
    )

    op_sent_date = fields.Date(
        tracking = True,
        string='Data d\'invio all\'operatore',
        copy=False
    )

    request_date = fields.Date(
        tracking = True,
        string='Data di richiesta',
        copy=False
    )
    
    confirmed_date = fields.Date(
        tracking = True,
        string='Data di conferma',
        copy=False
    )

    sla_date = fields.Date(
        string="Data SLA",
        tracking = True,
        compute="_compute_sla_date",
        store=True
    )

    @api.depends('request_date', 'op_sent_date', 'distance', 'partner_id')
    def _compute_sla_date(self):
        """
        Calcola la data SLA basandosi sulla data più avanti tra request_date e op_sent_date,
        aggiungendo i giorni di SLA definiti nelle fasce SLA del partner_id.
        I giorni del weekend vengono saltati.
        """
        for record in self:
            if not record.request_date and not record.op_sent_date:
                record.sla_date = False
                continue

            # Prendi la data più avanti tra request_date e op_sent_date
            base_date = max(filter(None, [record.request_date, record.op_sent_date]))

            # Trova la fascia SLA corrispondente alla distanza
            sla_bracket = self.env['sla.bracket'].search([
                ('partner_id', '=', record.partner_id.id),
                ('min_dist', '<=', record.distance),
                ('max_dist', '>=', record.distance),
            ], limit=1)

            if not sla_bracket:
                record.sla_date = False
                continue

            # Aggiungi i giorni di SLA, saltando i weekend
            sla_days = sla_bracket.SLA_days
            sla_date = base_date
            while sla_days > 0:
                sla_date += datetime.timedelta(days=1)
                if sla_date.weekday() < 5:  # Lunedì=0, Domenica=6
                    sla_days -= 1

            record.sla_date = sla_date

    
    user_id = fields.Many2one(
        string='User',
        comodel_name="res.users",
        default=lambda self: self.env.user,
        tracking = True,
        copy=False
    )
    partner_id = fields.Many2one(
        string='Partner',
        comodel_name="res.partner",
        tracking=True
    )

    email_fleetmanager =fields.Char(
        string="Email Fleet Manager",
        tracking = True
    )
    phone_fleetmanager =fields.Char(
        string="Telefono Fleet Manager",
        tracking = True
    )
    name_fleetmanager =fields.Char(
        string="Nome Fleet Manager",
        tracking = True
    )
    email_customer =fields.Char(
        string="Email Cliente",
        tracking = True
    )
    phone_customer =fields.Char(
        string="Telefono Cliente",
        tracking = True
    )
    name_customer =fields.Char(
        string="Nome Cliente",
        tracking = True
    )
    distance = fields.Float(
        tracking = True,
        string = "Distanza (Km)"
    )
    distance_time = fields.Float(
        tracking = True,
        string = "Tempo percorrenza"
    )


#region Tratta
    pickup_address = fields.Many2one(
        string="Pickup Address",
        comodel_name="fleet.partner",
        tracking=True
    )

    pickup_address_copy = fields.Char(string='Prelievo Completo', compute='_compute_pickup_address_copy', store=True)
    
    @api.depends('pickup_address', 'pickup_address.street', 
                'pickup_address.zip', 'pickup_address.city', 'pickup_address.state_id', 
                'pickup_address.country_id')
    def _compute_pickup_address_copy(self):
        for record in self:
            if record.pickup_address:
                # Estrai i valori dal record dell'indirizzo
                parts = []
                if record.pickup_address.street:
                    parts.append(record.pickup_address.street)
                if record.pickup_address.street2:
                    parts.append(record.pickup_address.street2)
                
                city_zip = []
                if record.pickup_address.zip:
                    city_zip.append(record.pickup_address.zip)
                if record.pickup_address.city:
                    city_zip.append(record.pickup_address.city)
                
                if city_zip:
                    parts.append(" ".join(city_zip))
                    
                if record.pickup_address.state_id:
                    parts.append(record.pickup_address.state_id.name)
                if record.pickup_address.country_id:
                    parts.append(record.pickup_address.country_id.name)
                
                # Unisci tutte le parti dell'indirizzo
                record.pickup_address_copy = ", ".join(filter(None, parts))
            else:
                record.pickup_address_copy = False

    pickup_address_city = fields.Char(
        string = "Pickup address city",
        related = "pickup_address.city"
    )

    pickup_address_code = fields.Char(
        string = "Pickup address code",
        related = "pickup_address.state_id.code"
    )
    
    delivery_address = fields.Many2one(
        string="Delivery Address",
        comodel_name="fleet.partner",
        tracking=True
    )

    delivery_address_copy = fields.Char(string='Consegna completo', compute='_compute_delivery_address_copy', store=True)
    
    @api.depends('delivery_address', 'delivery_address.street', 
                'delivery_address.zip', 'delivery_address.city', 'delivery_address.state_id', 
                'delivery_address.country_id')
    def _compute_delivery_address_copy(self):
        for record in self:
            if record.delivery_address:
                # Estrai i valori dal record dell'indirizzo
                parts = []
                if record.delivery_address.street:
                    parts.append(record.delivery_address.street)
                
                city_zip = []
                if record.delivery_address.zip:
                    city_zip.append(record.delivery_address.zip)
                if record.delivery_address.city:
                    city_zip.append(record.delivery_address.city)
                
                if city_zip:
                    parts.append(" ".join(city_zip))
                    
                if record.delivery_address.state_id:
                    parts.append(record.delivery_address.state_id.name)
                if record.delivery_address.country_id:
                    parts.append(record.delivery_address.country_id.name)
                
                # Unisci tutte le parti dell'indirizzo
                record.delivery_address_copy = ", ".join(filter(None, parts))
            else:
                record.delivery_address_copy = False

    delivery_address_city = fields.Char(
        string = "Delivery Address City",
        related = "delivery_address.city",
        store = True
    )

    delivery_address_code = fields.Char(
        string = "Delivery Address Code",
        related = "delivery_address.state_id.code",
        store = True
    )
#endregion

    vehicle_id = fields.Many2one(
        string='Vehicle',
        comodel_name="fleet.vehicle",
        tracking=True
    )

    vehicle_plate = fields.Char(
        string = "Vehicle Plate",
        related = "vehicle_id.license_plate"
    )


    contextual_vehicle_id = fields.Many2one(
        string = 'Veicolo contestuale',
        comodel_name = "fleet.vehicle",
        tracking = True
    )
        
    contextual_move_id = fields.Many2one(
        comodel_name= "fleet.move",
        compute="_compute_contextual_move_id",
        string='Movimentazione contestuale',
        store=True # Appesantisce il db ma probabilmente su AWS costa monetariamente meno di fare la query ogni volta (onestamente è da verificare)
    )

    @api.depends('contextual_vehicle_id')
    def _compute_contextual_move_id(self):
        for rec in self:
            if rec.contextual_vehicle_id:
                match_move = self.env['fleet.move'].search([
                    ('vehicle_id', '=', rec.contextual_vehicle_id.id)
                ], limit=1)
                rec.contextual_move_id = match_move.id if match_move else False
            else:
                rec.contextual_move_id = False


    contract_code = fields.Char(
        string='Contract Code',
        copy=True
    )

    timeslot = fields.Char(
        string='Fascia Oraria',
        copy=True,
        tracking=True
    )

    order_number = fields.Char(
        string='Order Number',
        copy=True
    )

    move_typology = fields.Selection(
        string='Typology',
        selection=[
            ('Consegna presso Cliente', 'Consegna presso Cliente'),
            ('Ritiro presso Cliente', 'Ritiro presso cliente'),
            ('Trasferimento', 'Trasferimento')
        ],
        default=False,
        tracking=True
    )

    note = fields.Text(
        string='Note',
        tracking=True
    )
    @api.model
    def _read_group_employee_ids(self, stages, domain,order):
        """
        Serve per mostrare tutti i record dell'oggetto quando
        vai nella kanban view.
        """
        stage_ids = self.env['hr.employee'].search([], order="name asc")
        return stage_ids

    employee_id = fields.Many2one(
        string='Carrier/Employee',
        comodel_name="hr.employee",
        tracking=True,
        group_expand="_read_group_employee_ids"
    )
    @api.model
    def _read_group_state_ids(self, stages, domain, order):
        """
        Serve per mostrare tutti i record dell'oggetto quando
        vai nella kanban view.
        """
        stage_ids = self.env['fleet.move.status'].search([], order="sequence asc")
        return stage_ids
        
    state = fields.Many2one(
        string='Status',
        comodel_name="fleet.move.status",
        tracking=True,
        group_expand='_read_group_state_ids'
    )
    primary_color = fields.Char(
        string="Color",
        related="state.primary_color"
    )

    @api.model
    def create(self, vals):
        """
        Override per assegnare la sequenza al nome 
        e lo stato di default (se esiste un default)
        """
        vals['name'] = self.env['ir.sequence'].sudo().next_by_code('fleet.move.sequence')
        # assegno lo stato di default
        state = self.env['fleet.move.status'].search([('default', '=', True)])
        if state:
            vals['state'] = state.id
        return super(FleetMove, self).create(vals)
    
    @api.constrains('confirmed_date')
    def _constrains_confirmed_date(self):
        """
        Usiamo questa funzione e il campo request_date_copy per i filtri
        mese corrente, mese precedente, mese seguente.
        Questi filtri sono scritti per fare l'or tra la data di conferma
        e la data richiesta ma poichè la data richiesta deve rimanere visibile 
        questa avrebbe sballato sempre la query.
        In questo modo facciamo la query su request_date_copy che diventa False
        se è assegnata una confirmed_date
        """
        for res in self:
            if res.confirmed_date:
                pass
            else:
                res.request_date = res.request_date
    
    @api.constrains('state')
    def _constrains_state(self):
        """
        Funzione che attiva l'action della fase.
        """
        for move in self:
            if move.state and move.state.sudo().action_server_id:
                action = move.state.sudo().action_server_id
                ctx = {
                    'active_model': move._name,
                    'active_ids': move.ids,
                    'active_id': move.id
                }
                action.sudo().with_context(**ctx).run()



    def message_post(self, **kwargs):
        """
        Override del metodo message_post per inviare notifiche a tutti i follower
        quando viene postato un nuovo messaggio su un record FleetMove.
        Compatibile con Odoo 14.
        
        Flow:
        1. Si chiama il metodo originale (super) per creare il messaggio.
        2. Si verifica che il messaggio sia collegato a un record del modello 'fleet.move'.
        3. Per ogni record (in genere uno solo) si cercano i follower tramite il modello mail.followers.
        4. Per ciascun follower si crea una notifica (mail.notification) come non letta.
        5. Viene restituito il messaggio creato.
        """
        # Chiamata al metodo originale di message_post per creare il messaggio
        message = super(FleetMove, self).message_post(**kwargs)
        
        # Verifica che il messaggio sia relativo al modello 'fleet.move' e abbia un record associato
        if message.model == 'fleet.move' and message.res_id:
            for rec in self:
                # Recupera tutti i follower del record corrente
                followers = self.env['mail.followers'].search([
                    ('res_model', '=', 'fleet.move'),
                    ('res_id', '=', rec.id)
                ])
                notifications = []
                for follower in followers:
                    notifications.append({
                        'mail_message_id': message.id,             # ID del messaggio appena creato
                        'res_partner_id': follower.partner_id.id,  # Partner da notificare
                        'is_read': False,                          # Notifica inizialmente non letta
                        'notification_type': 'inbox'               # Tipo di notifica (visualizzata nell'inbox)
                    })
                # Se ci sono notifiche da creare, le inserisce con privilegi amministrativi
                if notifications:
                    self.env['mail.notification'].sudo().create(notifications)
                    
        return message


class SlaBracket(models.Model):
    """
    Questo modello lo usiamo per salvare gli intervalli di SLA con i relativi giorni aggiuntivi, ogni record è una fascia chilometrica
    Campi:
    
    partner_id |--> A quale cliente appartiene questa fascia
    SLA_days   |--> Quanti giorni di SLA corrispondono a questa fascia
    min_dist   |--> Distanza minima della fascia
    max_dist   |--> Distanza massima della fascia

    L'unico controllo che viene fatto è sulla max_dist |--> se è uguale a una min_dist di un altro record con lo stesso partner_id vuol dire che due fasce si overlappano, ciò non è possibile
    """

    _name = "sla.bracket"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Fascia SLA"

    partner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
        required=True,
        tracking=True
    )

    SLA_days = fields.Integer(
        string="SLA Days",
        required=True,
        tracking=True
    )
    min_dist = fields.Integer(
        string="Distanza minima",
        required=True,
        tracking=True
    )
    max_dist = fields.Integer(
        string="Distanza massima",
        required=True,
        tracking=True
    )

    @api.constrains('min_dist', 'max_dist')
    def _check_distance_overlap(self):
        """
        Controlla che non ci siano sovrapposizioni tra le fasce chilometriche
        per lo stesso partner.
        """
        for record in self:
            if record.min_dist >= record.max_dist:
                raise ValidationError(_("La distanza minima deve essere maggiore di quella massima..."))

            overlapping_brackets = self.search([
                ('partner_id', '=', record.partner_id.id),
                ('id', '!=', record.id),
                '|',
                '&', ('min_dist', '<', record.max_dist), ('max_dist', '>', record.min_dist),
                '&', ('min_dist', '<', record.max_dist), ('max_dist', '>', record.min_dist)
            ])
            if overlapping_brackets:
                raise ValidationError(_("Questo range si sovrappone con un altro della stessa azienda."))



class FleetVehicle(models.Model):
    """
    Nella flotta aggiungiamo l'owner_id per visibilità

    cancel_from_user: se True  l'utente non lo vede.
                      può essere settato dal front end.
    """
    _inherit = 'fleet.vehicle'
    
    owner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
        tracking=True
    )
    
    cancel_from_user = fields.Boolean(
        string="Cancel From User",
        default=False
    )

class FleetMoveStatus(models.Model):
    """
    Stato/Fase delle richieste di movimentazione

    name : str
        nome interno
    portal_name : str
        nome esterno visibile sul portale web 
        (più stati possono avere lo stesso portal_name)
    default : bool
        se è lo stato da assegnare quando crei una richiesta
        può esistere solo uno stato con default a true
    done : bool
        stato finale
        possono esistere più stati con done a true e avere nomi diversi
    cancel : bool
        stato annullato
        possono esistere più stati con cancel a true e avere nomi diversi
    cancel_user : bool
        quando l'utente cancella dal front end
    planner_visible: bool
        se è uno stato visibile nel pianificatore
    action_server_id : m2o -> ir.action.server
        azione da chiamare quando sleet.move va in questo stato
    sequence: int
        ordinamento degli stati, ordina le colonne nella vista kanban
    primary_color : char
        colore dello stato kanban
    """
    _name = 'fleet.move.status'
    _inherit = ['mail.thread']
    _description = 'Fleet Move Status'
    _order = "sequence"

    active = fields.Boolean(
        string='Active',
        tracking=True,
        copy=False,
        default=True
    )
    name = fields.Char(
        string='Name',
        tracking=True
    )
    portal_name = fields.Char(
        string='Portal Name',
        tracking=True
    )
    default = fields.Boolean(
        string='Default',
        tracking=True
    )
    done = fields.Boolean(
        string='Done',
        tracking=True
    )
    cancel = fields.Boolean(
        string='Cancel',
        tracking=True
    )
    cancel_user = fields.Boolean(
        string='Cancel User',
        tracking=True
    )
    planner_visible = fields.Boolean(
        string='PLanner Visible',
        tracking=True
    )
    action_server_id = fields.Many2one(
        comodel_name='ir.actions.server',
        string='Server Actions',
        delegate=False,
        ondelete='restrict',
        required=False
    )

    sequence = fields.Integer(
        string="Sequence",
        default=0
    )
    primary_color = fields.Char(string="Color")

    @api.constrains('default')
    def _constrains_default(self):
        for status in self:
            if status.default:
                results = self.search([
                    ('default', '=', True),
                    ('id', '!=', status.id)
                ])
                if results:
                    raise UserError(_('Two or more states cannot exists with default flag.'))
    @api.constrains('cancel_user')
    def _constrains_default(self):
        for status in self:
            if status.cancel_user:
                results = self.search([
                    ('cancel_user', '=', True),
                    ('id', '!=', status.id)
                ])
                if results:
                    raise UserError(_('Two or more states cannot exists with cancel_user flag.'))

    def toggle_active(self):
        for move in self:
            move.active = not move.active

    def open(self):
        return {
            'res_model': 'fleet.move.status',
            'type': 'ir.actions.act_window',
            'context': {},
            'view_mode': 'form',
            'view_type': 'form',
            'res_id':self.id
        }
