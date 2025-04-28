from odoo import _, api, fields, models
import requests
import base64
import csv
from io import StringIO
from datetime import datetime
from ast import literal_eval
import dateutil
import logging

_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    
    """ 
    Configurazione per collegamento a Carpentum
    """
    
    carpentum_user = fields.Char(
        string="Username Carpentum",
        config_parameter="bloomup_carpentum.user"
    )
    carpentum_psw = fields.Char(
        string="Password Carpentum",
        config_parameter="bloomup_carpentum.psw"
    )
    carpentum_url = fields.Char(
        string="Url Carpentum",
        config_parameter="bloomup_carpentum.url"
    )
    
class Carpentum(models.TransientModel):
    _name = "carpentum.api"
    
    """ 
    Transient model per l'uso delle funzioni di carpentum
    """
    @api.model
    def get_type(self, code_tipo_entrata_veicolo, stato_incarico):
        """
        dato il codice e lo stato incarico ritorna il nome usato per la tipologia incarico
        """  
        ttype = False  
        if code_tipo_entrata_veicolo == 'Gate In':
            ttype = 'Gate In'
            
        if code_tipo_entrata_veicolo == 'Pronto Dealer':
            ttype = 'Rit-Dea'
            
        if code_tipo_entrata_veicolo == 'Gate In' and stato_incarico == 'ATTESA INCARICO':
            ttype = 'Fase zero' 
        if ttype:
            resttype = self.env['fleet.move.arval.type'].search([('name','=',ttype)])
            if resttype:
                return resttype[0].id
        return ttype
        
    def _login(self):
        """
        Effettua il login su carperntum
        prende url user e psw dalla configurazione
        restituisce un token o KO 
        """
        url = self.env['ir.config_parameter'].sudo().get_param('bloomup_carpentum.url')
        url = url + 'login'
        user = self.env['ir.config_parameter'].sudo().get_param('bloomup_carpentum.user')
        psw = self.env['ir.config_parameter'].sudo().get_param('bloomup_carpentum.psw')
        response = requests.post(url, json = {'Username':user, 'Password':psw})
        if response.status_code == 200:
            if response.json() == 'KO':
                return False 
            return response.json()
        else:
            return False
        
    def _get_incarichi(self, token):
        """
        Usando il token restituito dalla login
        restituisce la lista degli incarichi
        secondo documentazione carpentum 
        """
        url = self.env['ir.config_parameter'].sudo().get_param('bloomup_carpentum.url')
        url = url + 'GetIncarichi'
        user = self.env['ir.config_parameter'].sudo().get_param('bloomup_carpentum.user')
        headers = {'token':token,'username':user}
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            res = response.json()
            return res
        else:
            raise ValueError("Errore get incarichi")
    
    def _get_bbox_and_delivery(self, token):
        """ 
        assegna le date ai task e all'incarico
        """
        url = self.env['ir.config_parameter'].sudo().get_param('bloomup_carpentum.url')
        url = url + 'BBoxAndDeliveryTasks'
        user = self.env['ir.config_parameter'].sudo().get_param('bloomup_carpentum.user')
        headers = {'token':token,'username':user}
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            res = response.json()
            for task in res.get('Tasks'):
                # gestione codice 1 bbox
                if task.get('task') and task.get('task').get('Codice') == '1':
                    if task.get('veicolo') and task.get('veicolo').get('Targa'):
                        targa = task.get('veicolo').get('Targa')
                        ptask = self.env['project.task'].search([
                            ('vehicle_id.license_plate','=ilike',targa),
                            ('date_deadline','=',False) # se già decise da ars non le modifico altrimenti mi sovrascrive le date
                        ])
                        if ptask and task.get('bbox') and task.get('bbox').get('Disponibilita_Montaggio'):
                            data = task.get('bbox').get('Disponibilita_Montaggio')
                            yourdate = dateutil.parser.parse(data)
                            ptask.write({'date_dealer_availability': yourdate})
                # getsione consegna codice 2            
                if task.get('task') and task.get('task').get('Codice') == '2':
                    if task.get('veicolo') and task.get('veicolo').get('Targa'):
                        targa = task.get('veicolo').get('Targa')
                        fleet_move = self.env['fleet.move'].search(([
                            ('vehicle_id.license_plate','=ilike',targa),
                            ('date_dealer_availability','=',False) # per caso va aggiornata?
                        ]))
                        if fleet_move and task.get('delivery') and task.get('delivery').get('Disponibilita_Ritiro'):
                            data = task.get('delivery').get('Disponibilita_Ritiro')
                            yourdate = dateutil.parser.parse(data)
                            fleet_move.date_dealer_availability = yourdate
                            if fleet_move.assigned_to:
                                # creo l'attività al tizio assengato con data di scadenza la disponibilità
                                attrs={
                                    'user_id': fleet_move.assigned_to.id,
                                    'summary': 'Chiamare cliente per la consegna',
                                    'activity_type_id': self.env.ref('mail.mail_activity_data_call').id if self.env.ref('mail.mail_activity_data_call') else False,
                                    'date_deadline': yourdate ,
                                    'res_id':fleet_move.id,
                                    'res_model_id': self.env.ref('bloomup_fleet_move.model_fleet_move').id
                                }
                                self.env['mail.activity'].sudo().create(attrs)
        else:
            raise ValueError("Errore get bbox and delivery")
    
    @api.model
    def match(self):
        """
        Match tra valori di ipat (chiave) e nome campo carpentum (valore)
        Incarichi 
        
        va aggiornato in base ai campi
        
        va aggiornato IPAT con i field associati alla chiave corrispondente
        """
        return {
            # IPAT
            'ACQUISITION': 'acquisitionId',
            'ALIMENTAZIONE NUOVO': 'Veicolo/Alimentazione',
            'ALLESTITORE': 'allestitore',
            'CLIENTE':'appuntamento/cliente',
            'CLIENTE DRIVER': 'appuntamento/cliente_Driver',
            'CLIENTE EMAIL':'appuntamento/EmailIncaricatoClienteRitiro',
            'CLIENTE ID': 'appuntamento/cliente_Id',
            'CLIENTE INDIRIZZO CAP': 'appuntamento/CapCliente',
            'CLIENTE INDIRIZZO LOCALITA': 'appuntamento/LocalitaCliente',
            'CLIENTE INDIRIZZO PROVINCIA': 'appuntamento/ProvinciaCliente',
            'CLIENTE INDIRIZZO VIA': 'appuntamento/IndirizzoCliente',
            'CLIENTE REFERENTE CONSEGNA': 'appuntamento/cliente_Referente_Consegna',
            'CLIENTE TELEFONO': 'appuntamento/TelefonoIncaricatoClienteRitiro',
            'COLORE ESTERNO NUOVO': 'Veicolo/Colore_Esterno',
            'COLORE INTERNO NUOVO': 'Veicolo/Colore_Interno',
            #Letizia
            'CONCESSIONARIO': 'code_LuogoDispveicolo',
            #Letizia
            'ASSICURAZIONE PRIVATA': 'assicurazione_Privata',
            #Letizia
            'CARICAMENTO CERTIFICATO':'caricamento_Certificato_Ass_Privato',
            'CONCESSIONARIO INDIRIZZO PROVINCIA': 'appuntamento/concessionario_Ind_Provincia',
            'Durata': 'durata_Contratto', 
            'EMAIL FLEET MANAGER': 'email_Fleet_Manager',
            'FILIALE ARVAL ': 'filiale_arval',
            'ID ALLESTITORE': 'Id_Allestitore',
            'KM': 'km_Sottoscritti',
            'NOTE': 'note',
            'Numero porte veicolo nuovo': 'Veicolo/Numero_Porte',
            'PESO COMPLESSIVO NUOVO': 'Veicolo/Peso',
            'PNEUMATICI MARCA': 'pneumatici/MarcaPneumaticiPrimoImpianto',
            'PNEUMATICI MISURE ANTERIORI': 'pneumatici/MisureAnterioriPneumaticiPrimoImpianto', #TODO: MODIFICA IN IPAT VEICOLO
            'PNEUMATICI MISURE POSTERIORI': 'pneumatici/MisurePosterioriPneumaticiPrimoImpianto', #TODO: AGGIUNGI IN IPAT VEICOLO
            'PNEUMATICI MODELLO': 'pneumatici/ModelloPneumaticiPrimoImpianto',
            'PNEUMATICI TIPO': 'pneumatici/tipologia_Gomme',
            'REFERENTE ALLESTITORE - TELEFONO': 'referente_Allestitore',
            'REFERENTE ARVAL': 'referente_arval',
            'REFERENTE ARVAL TELEFONO': 'referente_arval_Telefono',
            'REFERENTE ARVAL MAIL': 'referente_arval_Mail',
            'SEGMENTO DI APPARTENENZA': 'Veicolo/Segmento_Appartenenza',
            'TASSATIVO CON BISARCA': 'tassativo_Con_Bisarca', #TODO: controllare importazioni con date vere
            'Trasmissione veicolo Nuovo': 'Veicolo/Trasmissione',
            'VEICOLO NUOVO ACCESSORI': 'Veicolo/Accessori',
            'VEICOLO NUOVO ALLESTIMENTI': 'Veicolo/Allestimenti',
            'VEICOLO NUOVO ANTIFURTO SATELLITARE': 'Veicolo/Antifurto_Satellitare', #TODO: CAMBIA I VALORI BOOLEAN
            'VEICOLO NUOVO DVP': 'dvp_date', #TODO: controllare importazioni con date vere
            'VEICOLO NUOVO ID': 'Veicolo/Id',
            'VEICOLO NUOVO MARCA': 'Veicolo/Marca',
            'VEICOLO NUOVO MODELLO': 'Veicolo/Modello',
            'VEICOLO NUOVO OPTIONS': 'Veicolo/Optionals',
            'VEICOLO NUOVO TARGA': 'Veicolo/Targa',
            'VEICOLO NUOVO TELAIO': 'Veicolo/Telaio',
            'VEICOLO NUOVO TELEPASS': 'Veicolo/Telepass', #TODO: CAMBIA I VALORI BOOLEAN
            'VEICOLO NUOVO TIPO': 'Veicolo/Tipo',
            # NUOVI
            'CODICE INCARICO': 'Codice_Incarico',
            'CODE TIPO ENTRATA VEICOLO': 'code_tipo_entrata_veicolo',
            'STATO INCARICO': 'Stato_Incarico',
            # HUB
            'INSTALLATORE BLACK BOX':'Veicolo/Installatore_BlackBox',
            'LOJACK': 'Veicolo/Lojack',
            'PNEUMATICI SERVIZIO': 'pneumatici/servizio_Pneumatici',
            'PROGETTO INCLUSIONE': 'progetto_Inclusione'
            
        }
    
class CarpentumResPartner(models.Model):
    _inherit = "res.partner"
    
    def import_carpentum(self):
        """ 
        Crea una struttura dati compatibile con ipat dagli incarichi
        ottenuti da carpentum. Usa la funzion match per assegnare la chiave
        corretta delal struttura dati al campo.
        
        Se gate in, verifica che non sia già stato importato. Crea così una struttura
        dati per l'importazioen hub e crea l'importatore corrispondente.
        
        Importa le movimentazioni
        
        CHANGE LOG:
        - 03/07/23 attualmente l'hub deve essere processato manualmente
        assegnando il progetto e premendo carpentum import
        """
        self.ensure_one()
        token = self.env['carpentum.api'].sudo()._login()
        if not token:
            raise ValueError("Erorre Login")
        incarichi = self.env['carpentum.api'].sudo()._get_incarichi(token)
        _logger.info(incarichi.get('Incarichi'))
        incarichi = incarichi.get('Incarichi')
        match = self.env['carpentum.api'].sudo().match()
        datas = []
        hub_datas = []   
        for incarico in incarichi:
            attrs = {}
            for key in match:
                val = match[key].split('/')
                if len(val) == 1:
                    if incarico.get(val[0]):
                        attrs[key] = (incarico.get(val[0]), 1)
                    else:
                        attrs[key] = ('',0)
                elif len(val) > 1:
                    prefix = incarico
                    for k in val:
                        prefix = prefix.get(k)
                    if not prefix:
                        attrs[key] = ('',0)
                    else:
                        attrs[key] = (prefix, 1)
                else:
                    continue
            codice_incarico = attrs['CODICE INCARICO'][0]
            tipo = attrs['CODE TIPO ENTRATA VEICOLO'][0]
            
            # controlla che non esiste l'incarico
            if tipo == 'Gate In':
                res = self.env['fleet.move'].search([('codice_incarico','=',codice_incarico)])
                if not res:
                    row = {x:attrs[x][0] for x in attrs}
                    hub_datas.append(row)
            
            datas.append(attrs)
        if self.ipat_id:
            self.ipat_id.clear_datas()
            self.ipat_id.datas = datas
            self.ipat_id.start_import()
            # se ho qualche riga hub
            
            if len(hub_datas)>0:
                pid = self.env['project.project'].search([('is_hub','=',True)])
                if not pid:
                    pid = False
                hub = self.env['hub.importer'].create({
                    'name': 'IMPORT CARPENTUM %s' % datetime.now(),
                    'project_id': pid[0].id if pid else False,
                    'raw_data': hub_datas,
                    'source_data': 'carpentum'
                })

class CarpentumHub(models.Model):
    _inherit = "hub.importer"
    
    """
    Aggiunto raw_data dove va la struttura dati nuova di import
    aggiunto come tipo carpentum 
    """
    
    raw_data = fields.Text(
        string="Datas"
    )
    source_data = fields.Selection(
        selection_add=[('carpentum', 'Carpentum')]
    )
    
    def save_import_carpentum(self):
        """ 
        Prende la struttura dati creata dall'importatore carpentum
        ed effettua l'importazioen hub
        """
        for record in self:
            datas = literal_eval(record.raw_data)
            attrs = {}
            for res in dict(self.env['hub.importer.config']._fields['field_id'].selection):
                line = record.project_id.partner_id.csv_hub_configuration.filtered(lambda x: x.field_id == res)
                name = dict(self.env['hub.importer.config']._fields['field_id'].selection)[res]
                if line:
                    name = line.name
                attrs[res] = name.strip()
            for riga in datas:
                foundit = False
                auto = False
                create_attrs = {}
                if attrs['vin_sn'] in riga and riga[attrs['vin_sn']]:
                    res = self.env['fleet.vehicle'].search([('vin_sn','=',riga[attrs['vin_sn']].strip())])
                    if res:
                        auto = res[0]
                        auto.hub_importer_ids = [(4, record.id, 0)]
                        foundit = True
                if auto:   
                    task = auto.create_activities_arval(record.project_id, riga=riga)
                    for t in task:
                        record.tasks = [(4, t.id, 0)]