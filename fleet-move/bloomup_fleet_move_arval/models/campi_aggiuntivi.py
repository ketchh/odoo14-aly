from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime,timedelta
"""
Qua mettiamo i campi aggiuntivi che troviamo nel file
o nel verbale.
"""

class FleetMoveAggiuntivi(models.Model):
    _inherit="fleet.move"
    
    request_date = fields.Datetime(
        string='Request Datetime',
        default=False,
        copy=False
    )
    tassativo_bisarca = fields.Datetime(
        string="Tassativo con bisarca",
        default=False,
        copy=False
    )
    
    #30/01/23
    pneumatici_servizio = fields.Char(
        string="Pneumatici Servizio"
    )
    assicurazione_privata = fields.Char(
        string="Assicurazione privata"
    )

    notice_day_before = fields.Boolean(
        string='Notified for the day before')

    from_hour = fields.Char(
        string='From')
    to_hour = fields.Char(
        string='To')

    postpone = fields.Boolean(
        string='Postpone')

    old_date = fields.Datetime(
        string='Previous Request Datetime',
        default=False,
        copy=False)
    
    @api.constrains('confirmed_date')
    def save_previous_date(self):
        for record in self:
            if not record.postpone:
                record.old_date = record.confirmed_date

    @api.constrains('assicurazione_privata')
    def _add_message_assicurazion_privata(self):
        if self.assicurazione_privata and self.assicurazione_privata.strip().lower() == 'si':
            self.note = self.note + "\nAssicurazione privata."
    


    available_from = fields.Date(
        string='Available from',
        default=False,
        copy=False
    )

    # LETIZIA - search move for the day before and send mail/sms
    @api.model
    def notify_customer(self):
        tomorrow = datetime.now() + timedelta(1)
        start = datetime(tomorrow.year, tomorrow.month, tomorrow.day)
        end = start + timedelta(1)
        moves = self.env['fleet.move'].search([('confirmed_date', '>', start),('confirmed_date', '<', end)])
        for move in moves:
            state_id =''
            if move.delivery_address.state_id and not move.notice_day_before:
                state_id = move.delivery_address.state_id.name
            if move.white_label and move.white_label == 'simple':
                msg = 'Gentile cliente, le ricordiamo che domani {} avverrà la consegna del nuovo veicolo Simplerent {} {} {} - presso {} {} {} {}. A domani, Ars Altmann partner di Simplerent'.format(tomorrow.strftime('%d/%m/%Y'),move.vehicle_id.model_id.brand_id.name,move.vehicle_id.model_id.name,move.vehicle_id.license_plate, move.delivery_address.city,move.delivery_address.street,move.delivery_address.zip,state_id)
            else:
                msg = 'Gentile cliente, le ricordiamo che domani {} avverrà la consegna del nuovo veicolo Arval {} {} {} - presso {} {} {} {}. A domani, Ars Altmann partner di Arval'.format(tomorrow.strftime('%d/%m/%Y'),move.vehicle_id.model_id.brand_id.name,move.vehicle_id.model_id.name,move.vehicle_id.license_plate, move.delivery_address.city,move.delivery_address.street,move.delivery_address.zip,state_id)
            move.notice_day_before = True
            move.invia_sms(msg)
    
    @api.constrains('request_date','tassativo_bisarca')
    def _constrains_tipologia_data(self):
        for record in self:
            
            if self.env.context.get('no_next'):
                return
            if not record.request_date and not record.tassativo_bisarca:
                record.with_context(no_next=True).request_date = datetime.now()
            if datetime.strftime(record.request_date,'%d/%m/%Y') == "01/01/2099":
                record.tipologia_data = 'asap'
                record.with_context(no_next=True).request_date = datetime.now()
            else:
                record.tipologia_data = 'a_partire_da'
                
            if not record.request_date and record.tassativo_bisarca:
                record.tipologia_data = 'tassativo'
                record.with_context(no_next=True).request_date = record.tassativo_bisarca
    
    ###
    date_type = fields.Selection(
        string="Tipologia Data",
        selection=[
            ('asap', 'ASAP'),
            ('a_aprtire_da', 'A partire da'),
            ('tassativo', 'Tassativo')
        ],
        tracking=True,
    )
    note_importer = fields.Text(
        string="Note Importer",
        tracking=True,
    )
    ### GOMMISTA
    gommista_name = fields.Char(
        string="Nome Gommista",
        tracking=True,
    )
    gommista_luogo = fields.Char(
        string="Luogo Gommista",
        tracking=True,
    )
    gommista_1 = fields.Char(
        tracking=True,
    )
    gommista_2 = fields.Char(
        tracking=True,
    )
    gommista_3 = fields.Char(
        tracking=True,
    )
    ### DELEGATO
    delegato = fields.Boolean(
        string="Delegato?",
        tracking=True,
    )
    delegato_name = fields.Char(
        string="Nome Delegato",
        tracking=True,
    )
    delegato_lastname = fields.Char(
        string="Cognome Delegato",
        tracking=True,
    )
    delegato_phone = fields.Char(
        string="Telefono Delegato",
        tracking=True,
    )
    delegato_cel = fields.Char(
        string="Cellulare Delegato",
        tracking=True,
    )
    delegato_email = fields.Char(
        string="E-mail Delegato",
        tracking=True,
    )
    ### DATI ARVAL
    num_dossier_arval = fields.Char(
        string="N° Dossier Arval",
        tracking=True,
    )
    num_contratto = fields.Char(
        string="N° Contratto",
        tracking=True,
    )
    durata_contratto = fields.Char(
        string="Durata Contratto",
        tracking=True,
    )
    km_sottoscritti = fields.Char(
        string="Km Sottoscritti",
        tracking=True,
    )
    filiale_arval = fields.Char(
        string="Filiale Arval",
        tracking=True
    )
    referente_arval = fields.Char(
        string="Referente Arval",
        tracking=True
    )
    referente_arval_phone = fields.Char(
        string="Telefono Referente Arval",
        tracking=True
    )
    referente_arval_mail = fields.Char(
        string="E-mail referente Arval",
        tracking=True
    )
    ### ALLESTITORE
    allestitore_id = fields.Char(
        string="Id Allestitore",
        tracking=True
    )
    allestitore = fields.Char(
        string="Allestitore",
        tracking=True
    )
    referente_allestitore = fields.Char(
        string="Referente Allestitore",
        tracking=True
    )
    ### CLIENTE
    customer_id = fields.Many2one(
        string="Cliente",
        comodel_name="res.partner",
        tracking=True,
    )
    codice_cliente = fields.Char(
        string="Codice Cliente",
        store=True,
        related="customer_id.ref"
    )
    partita_iva = fields.Char(
        string="Partita Iva",
        store=True,
        related="customer_id.vat"
    )
    cliente_referente = fields.Char(
        string="Referente Cliente",
        tracking=True
    )
    cliente_driver = fields.Char(
        string="Cliente Driver",
        tracking=True
    )
    ### da mettere in vista
    incarico = fields.Char(
        string="Incarico",
        tracking=True
    )
    caratteristiche_consegna = fields.Char(
        string="Caratteristiche consegna",
        tracking=True
    )
    email_fleet_manager = fields.Char(
        string="E-mail fleet manager",
        tracking=True
    )
    segmento_appartenenza = fields.Char(
        string="Segmento di appartenenza",
        tracking=True
    )

    ### richieste arval - 24 nov 2022

    others = fields.Char(
            string="Altri destinatari",
            tracking=True
    )


    white_label = fields.Selection(
        string="White label",
        selection=[
            ('simple', 'Simplerent')
        ],
        tracking=True
    )

    note_whitelabel = fields.Text(
        string="Note white label",
        tracking = True
    )
    # data
    tipologia_data = fields.Selection(
        string="Tipologia Data",
        selection=[
            ('asap', 'Asap'),
            ('a_partire_da', 'A partire da'),
            ('tassativo', 'Tassativo')
        ]
    )
    
    def invia_sms(self, msg=False):
        """
        Invia l'sms tramite aruba,
        msg deve essere configurato nella action server
        """
        self.ensure_one()
        if not msg:
            self.message_post(
                body="Sms non inviato, messaggio mancante.",
                subject="Errore Invio SMS",
                message_type="comment"
            )
            return
        sendsms = False
        otp = self.env['sms.otp'].search([])
        if otp:
            otp = otp[0]
        else:
            self.message_post(
                body="Sms non inviato, configurazione mancante.",
                subject="Errore Invio SMS",
                message_type="comment"
            )
            return
        partner = self.delivery_address
        if partner and partner.phone:
            phone = otp.phone_format(partner.phone,partner.country_id)
            auth = otp.login()
            sendsms = otp.sendSMS(auth,phone,msg)
            if sendsms:
                body = "Inviato il seguente sms: \n %s" % msg
                self.message_post(
                    body=body,
                    subject="Invio SMS",
                    message_type="comment"
                )
            else:
                self.message_post(
                    body="Sms non inviato, problemi Aruba o numero non adatto.",
                    subject="Errore Invio SMS",
                    message_type="comment"
                )
        else:
            self.message_post(
                body="Sms non inviato, numero di telefono mancante.",
                subject="Errore Invio SMS",
                message_type="comment"
            )
    
    @api.constrains('state')
    def _constrains_state_arval_2(self):
        # ATTENZIONE RICORDARE LA FASE ATTIVITA' da mettere come fase di chiusura
        for record in self:
            if not record.state.default and not self.env.context.get("force_state"):
                # cerco le attività,
                # quelle bloccanti che non sono chiuse
                tasks = self.env['project.task'].search(
                    [('vehicle_id','=',record.vehicle_id.id),
                     ('stage_id.is_closed','=',False),
                     ('task_typology_id.block_state','=',True)]
                )
                if tasks:
                    raise ValidationError("Per cambiare stato devi attendere che tutte le attività siano completate")
            
class ArvalFleet(models.Model):
    _inherit = "fleet.vehicle"
    
    antifurto_satellitare = fields.Boolean(
        string="Antifurto Satelletitare",
        tracking=True
    )
    telepass = fields.Boolean(
        string="Telepass",
        tracking=True
    )
    accessori = fields.Text(
        string="Accessori",
        tracking=True,
        help="Per compatibilità con la stampa è necessario che sia una lista con - davanti ad ogni riga"
    )
    optionals = fields.Text(
        string="Optionals",
        tracking=True,
        help="Per compatibilità con la stampa è necessario che sia una lista con - davanti ad ogni riga"
    )
    allestimento = fields.Text(
        string="Allestimento",
        tracking=True,
        help="Per compatibilità con la stampa è necessario che sia una lista con - davanti ad ogni riga"
    )
    trasmissione = fields.Char(
        string="Trasmissione",
        tracking=True
    )
    atp = fields.Char(
        string="Certificato ATP",
        tracking=True
    )
    peso = fields.Char(
        string="Peso",
        tracking=True
    )
    colore_esterno = fields.Char(
        string="Colore Esterno",
        tracking=True
    )
    colore_interno = fields.Char(
        string="Colore Interno",
        tracking=True
    )
    
    ### PNEUMATICI
    brand_tires = fields.Char(
        string="Marca pneumatici",
        tracking=True
    )
    model_tires = fields.Char(
        string="Modello pneumatici",
        tracking=True
    )
    meas_ant = fields.Char(
        string="Pneumatici: misure anteriori",
        tracking=True
    )
    meas_post = fields.Char(
        string="Pneumatici: misure posteriori",
        tracking=True
    )
    antiforature = fields.Boolean(
        string="Pneumatici: Antiforatura",
        tracking=True
    )
    type_tires = fields.Char(
        string="Tipologia pneumatici"
    )
    
    class ArvalPartner(models.Model):
        _inherit = "res.partner"
        
        ipat_id = fields.Many2one(
            string="Importer",
            comodel_name="bloomup.ipat"
        )
        excel_file = fields.Binary(
            string="Excel"
        )
        ipat_message = fields.Text(
            string="Message"
        )
        
        def import_file_ipat(self):
            self.ensure_one()
            if self.excel_file and self.ipat_id:
                self.ipat_id.file = self.excel_file
                self.ipat_id.clear_datas()
                self.ipat_id.load_datas() # mi inserisco nel load datas
                self.ipat_id.start_import()
                self.ipat_message = self.ipat_id.message
    
class ArvalLocation(models.Model):
    _inherit = "fleet.location"
    
    count_vehicle = fields.Integer(
        string="Numero Veicoli",
        compute="_compute_vehicle"
    )
    assign_to = fields.Many2one(
        string="Utente",
        comodel_name="res.users"
    )
    pickup_address = fields.Many2one(
        string="Indirizzo",
        comodel_name="fleet.partner"
    )
    
    def _compute_vehicle(self):
        for record in self:
            record.count_vehicle = len(record.attendance_ids)

class ARvalPartner(models.Model):
    _inherit = "fleet.partner"
    
    default_code = fields.Char(
        string="Codice"
    )
