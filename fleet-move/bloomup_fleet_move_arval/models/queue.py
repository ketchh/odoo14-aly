# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from ast import literal_eval
from email import utils
from datetime import timedelta, datetime
import base64

class QueueMail(models.Model):
    _name = "arval.queue.mail.line"
    _inherit = ['mail.thread']
    _description = 'Arval mail queue line'
    
    """ 
    Riga di una coda, ogni mail in ingresso è una riga.
    Quando viene letta e avviato l'importer viene messo processed a True
    """
    name = fields.Char(
        string="Name"
    )
    queue_id = fields.Many2one(
        string="Mail Queue",
        comodel_name="arval.queue.mail"
    )
    processed = fields.Boolean(
        string="Processed",
        default=False
    )
    error = fields.Boolean(
        string="Error",
        default=False
    )
    company_id = fields.Many2one(
        'res.company', 
        required=True, 
        readonly=True, 
        default=lambda self: self.env.company
    )
    mail_from = fields.Char(
        string="Mail From"
    )
    body = fields.Html(
        string="Body"
    )
    
    def message_new(self, msg, custom_values=None):
        """ 
        Quando arriva una mail esegue questi passaggi
        """
        # assegna il body e la mail di provenienza
        defaults={
            'mail_from': utils.parseaddr(msg.get('email_from', False))[1],
            'body': msg.get('body', '')
        }
        defaults.update(custom_values or {})
        return super(QueueMail, self).message_new(msg,custom_values=defaults)

    @api.model
    def _cron_process(self):
        results = self.search([('processed','=',False)])
        for res in results:
            res.create_fleet_move()
    
    def create_fleet_move(self):
        """
        trova il file e se c'è lo importa
        """
        self.ensure_one()
        if self.processed:
            return
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        base_url += '/web#id=%d&view_type=form&model=%s' % (self.id, self._name)
        filenames = self.queue_id.filename.split(',')
        filenames = [x.lower() for x in filenames]
        
        for filename in filenames:
            attachments = self.env['ir.attachment'].search([
                ('res_model','=',self._name),
                ('res_id','=',self.id),
                ('name','=ilike',filename)
            ])
            self.processed=True
            for attachment in attachments:
                self.queue_id.partner_id.excel_file = (attachment.datas).decode('utf-8')
                if self.queue_id.fleet_move:
                    try:
                        self.queue_id.partner_id.import_file_ipat()
                    except Exception as e:
                        self.env.cr.rollback()
                        self.message_post(
                            subject=_("Error import fleet move"),
                            body=_("[Mail Line %s] Error import fleet move: %s<br/> <a href='%s'>%s</a>") % (self.id, e, base_url, base_url),
                            message_type='email',
                            partner_ids=self.queue_id.partners_send_mail.ids
                        )
                        self.error=True
                        continue
                    if self.queue_id.partner_id.ipat_id.refused:
                        d = literal_eval(self.queue_id.partner_id.ipat_id.refused)
                        html = '<b>Righe con campi obbligatori mancanti:</b><ul>'
                        for row in d:
                            html += '<li><b>%s:</b>' % (row)
                            html += str(d[row])
                            html += '</li>'
                        html += '</ul>'
                        html += "<br/><a href='%s'>%s</a>" % (base_url,base_url)
                        self.message_post(
                            subkect="Campi obbligatori mancanti",
                            body=html,
                            message_type='email',
                            partner_ids=self.queue_id.partners_send_mail.ids
                        )
                        self.error = True
                    self.message_post(
                        body=_("Fleet move import: <br/>%s") % self.queue_id.partner_id.ipat_message,
                        message_type='comment'
                    )
                if self.queue_id.hub:
                    hub = self.env['hub.importer'].create({
                        'name': self.name,
                        'project_id': self.queue_id.project_id.id,
                        'source_data': 'file',
                        'source_file': (attachment.datas).decode('utf-8')
                    })
                    try:
                        hub.save_import()
                    except Exception as e:
                        # lo faccio per evitare che il passaggio precedente mi abbia 
                        # salvato qualcosa
                        self.env.cr.rollback()
                        self.message_post(
                            subject=_("Error import hub"),
                            body=_("[Mail Line %s] Error import hub: %s<br/> <a href='%s'>%s</a>") % (self.id, e, base_url, base_url),
                            message_type='email',
                            partner_ids=self.queue_id.partners_send_mail.ids
                        )
                        self.error=True
                        continue
                    base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                    base_url += '/web#id=%d&view_type=form&model=%s' % (hub.id, hub._name)
                    self.message_post(
                        body=_("Hub import: <a href='%s'>%s</a>") % (base_url, base_url),
                        message_type='comment'
                    )

class ArvalQueue(models.Model):
    _name = "arval.queue.mail"
    _inherit = [
        'mail.thread',
        'mail.alias.mixin'
    ]
    _description = "Arval Mail Queue"
    
    """ 
    Il raccoglitore della coda delle mail.
    Si crea e gli si assegna un alias.
    L'alias crea un arval.queue.mail.line collegata all'oggetto padre.
    """
    active = fields.Boolean(
        string="Active",
        default=True
    )
    name = fields.Char(
        string="Name"
    )
    alias_id = fields.Many2one(
        'mail.alias',
        string='Alias ref', 
        ondelete="restrict",
        required=True
    )
    company_id = fields.Many2one(
        'res.company', 
        required=True, 
        readonly=True, 
        default=lambda self: self.env.company
    )
    queue_line_ids = fields.One2many(
        string="Lines",
        comodel_name="arval.queue.mail.line",
        inverse_name="queue_id"
    )
    queue_line_count = fields.Integer(
        string="Line count",
        compute="_compute_line_count"
    )
    alias_value = fields.Char(
        string="Alias",
        compute="_compute_alias_value"
    )
    partner_id = fields.Many2one(
        string="Assign to",
        comodel_name="res.partner",
        domain=[('parent_id','=',False)]
    )
    fleet_move = fields.Boolean(
        string="Fleet Move",
        default=True
    )
    hub = fields.Boolean(
        string="Hub",
        default=True
    )
    filename = fields.Char(
        string="Filename"
    )
    project_id = fields.Many2one(
        string="Project",
        comodel_name="project.project"
    )
    partners_send_mail = fields.Many2many(
        string="Parter to send error mail",
        comodel_name="res.partner"
    )
    
    def _alias_get_creation_values(self):
        """ 
        Funzione che crea l'alias quando metti l'alias name
        """
        values = super(ArvalQueue, self)._alias_get_creation_values()
        # assegna il modello da creare
        values['alias_model_id'] = self.env['ir.model']._get('arval.queue.mail.line').id
        # assegna i valori di default
        # nel caso specifico il collegamento all'oggetto padre
        values['alias_defaults'] = {'queue_id': self.id}
        return values

    def _compute_line_count(self):
        """
        Calcola il numero di mail in ingresso presenti
        """
        for record in self:
            record.queue_line_count = len(record.queue_line_ids)
    
    def queue_line_tree(self):
        """ 
        Apre la vista tree per le arval.queue.mail.line
        """
        self.ensure_one()
        return {
            'name':_("Mail - %s") % self.name,
            'view_mode': 'tree,form',
            'res_model': 'arval.queue.mail.line',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('queue_id','=', self.id)],
        }
    
    def _compute_alias_value(self):
        """
        Alias mail completo
        """
        for record in self:
            record.alias_value = ''
            if record.alias_name and record.alias_domain:
                record.alias_value = "%s@%s" % (record.alias_name, record.alias_domain)