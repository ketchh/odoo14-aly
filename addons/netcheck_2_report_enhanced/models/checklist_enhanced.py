# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ChecklistEnhanced(models.Model):
    """
    Estensione del modello checklist.checklist per integrare 
    la nuova struttura dati ottimizzata per i report
    """
    _inherit = 'checklist.checklist'

    # Relazione con i dati di report
    report_data_ids = fields.One2many(
        'checklist.report.data',
        'checklist_id',
        string='Report Data',
        help='Dati ottimizzati per la generazione dei report'
    )
    
    has_report_data = fields.Boolean(
        string='Has Report Data',
        compute='_compute_has_report_data',
        store=True
    )
    
    latest_report_data_id = fields.Many2one(
        'checklist.report.data',
        string='Latest Report Data',
        compute='_compute_latest_report_data',
        store=True
    )

    @api.depends('report_data_ids')
    def _compute_has_report_data(self):
        for record in self:
            record.has_report_data = bool(record.report_data_ids)

    @api.depends('report_data_ids')
    def _compute_latest_report_data(self):
        for record in self:
            if record.report_data_ids:
                record.latest_report_data_id = record.report_data_ids.sorted('completion_date', reverse=True)[0]
            else:
                record.latest_report_data_id = False

    def create_report_data(self):
        """
        Crea la struttura dati ottimizzata per il report.
        Questo metodo viene chiamato automaticamente quando la checklist viene completata,
        ma può anche essere chiamato manualmente.
        """
        self.ensure_one()
        
        if self.state != 'done':
            raise UserError(_("Cannot create report data for checklist that is not completed."))
        
        # Verifica se esistono già dati di report per questa completazione
        existing_data = self.env['checklist.report.data'].search([
            ('checklist_id', '=', self.id),
            ('completion_date', '=', self.data_compilazione)
        ], limit=1)
        
        if existing_data:
            return existing_data
        
        # Crea i dati base del report
        report_data = self.env['checklist.report.data'].create({
            'checklist_id': self.id,
            'checklist_name': self.name,
            'user_id': self.user_id.id,
            'company_id': self.company_id.id,
            'completion_date': self.data_compilazione or fields.Datetime.now(),
            'confirmed_date': self.confirmed_date,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'day_start': self.day_start,
            'day_end': self.day_end,
            'ref_doc_model': self.ref_doc_id._name if self.ref_doc_id else False,
            'ref_doc_id': self.ref_doc_id.id if self.ref_doc_id else False,
            'ref_doc_name': self.ref_doc_id.display_name if self.ref_doc_id else False,
        })
        
        # Crea le linee del report
        current_section = False
        sequence = 10
        
        for line in self.line_ids.sorted('position'):
            if line.type == 'section':
                current_section = line.name
            
            # Crea la linea del report
            report_line = self.env['checklist.report.data.line'].create({
                'report_data_id': report_data.id,
                'line_name': line.name or '[No Name]',
                'line_type': line.type,
                'sequence': sequence,
                'position': line.position,
                'section_name': current_section,
            })
            
            # Recupera tutte le registrazioni per questa linea (incluse quelle con additional_data)
            registrations = self.env['checklist.registration'].search([
                ('checklist_line_id', '=', line.id),
                ('active', '=', True)
            ]).sorted('create_date')
            
            # Crea le registrazioni del report
            for reg in registrations:
                formatted_value = self._format_registration_value(reg, line)
                self.env['checklist.report.data.registration'].create({
                    'line_id': report_line.id,
                    'original_registration_id': reg.id,
                    'user_id': reg.user_id.id,
                    'raw_value': reg.raw_value,
                    'create_date': reg.create_date,
                })
            
            sequence += 10
        
        return report_data

    def _format_registration_value(self, registration, line):
        """
        Formatta il valore della registrazione per il display nel report
        """
        if not registration.raw_value:
            return ''
        
        line_type = line.type
        raw_value = registration.raw_value
        
        if line_type == 'selection':
            # Gestisce le selezioni
            response = raw_value.split(',')
            values = []
            
            for item_id in response:
                try:
                    item_id = int(item_id)
                    # Cerca nelle opzioni di selezione string
                    for option in line.option_selection_string:
                        if option.id == item_id:
                            values.append(option.name)
                            break
                    else:
                        # Cerca nelle opzioni di selezione model
                        for option in line.option_ids:
                            if option.code == 'option_selection_model' and line.name_model:
                                try:
                                    model_record = self.env[line.name_model.model].sudo().browse(item_id)
                                    if model_record.exists():
                                        values.append(model_record.display_name)
                                except:
                                    pass
                except (ValueError, TypeError):
                    pass
            
            return ', '.join(values) if values else raw_value
        
        elif line_type == 'precompiled':
            return line.option_precompiled_test or ''
        
        else:
            return raw_value

    @api.constrains('state')
    def _constrains_state_enhanced(self):
        """
        Override del constraint state per creare automaticamente i dati di report
        quando la checklist viene completata
        """
        for record in self:
            if record.state == 'done' and not record.has_report_data:
                try:
                    record.create_report_data()
                    _logger.info(f"Automatically created report data for checklist {record.id}")
                except Exception as e:
                    _logger.warning(f"Failed to auto-create report data for checklist {record.id}: {e}")
        
        return super()._constrains_state_enhanced()

    def action_view_report_data(self):
        """
        Azione per visualizzare i dati di report
        """
        self.ensure_one()
        
        return {
            'name': _('Report Data'),
            'view_mode': 'tree,form',
            'res_model': 'checklist.report.data',
            'domain': [('checklist_id', '=', self.id)],
            'type': 'ir.actions.act_window',
            'context': {'default_checklist_id': self.id}
        }

    def action_create_report_data(self):
        """
        Azione per creare manualmente i dati di report
        """
        for record in self:
            if record.state == 'done':
                record.create_report_data()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Report data created successfully'),
                'sticky': False,
                'type': 'success'
            }
        }

    def print_enhanced_report(self):
        """
        Stampa il report con la struttura dati ottimizzata
        """
        self.ensure_one()
        
        # Assicurati che esistano i dati di report
        if not self.has_report_data and self.state == 'done':
            self.create_report_data()
        
        if not self.has_report_data:
            raise UserError(_("No report data available. Complete the checklist first."))
        
        return self.env.ref('netcheck_2_report_enhanced.action_report_checklist_enhanced').report_action(self.latest_report_data_id)


class ChecklistRegistrationEnhanced(models.Model):
    """
    Estensione del modello checklist.registration per integrare 
    automaticamente la creazione dei dati di report
    """
    _inherit = 'checklist.registration'

    @api.model
    def create(self, vals):
        """
        Override del create per gestire l'aggiornamento automatico dei dati di report
        """
        registration = super().create(vals)
        
        # Se la checklist viene chiusa, crea automaticamente i dati di report
        if registration.close and registration.checklist_line_id.checklist_id.state == 'done':
            checklist = registration.checklist_line_id.checklist_id
            try:
                checklist.create_report_data()
            except Exception as e:
                # Log l'errore ma non bloccare la creazione della registrazione
                _logger.warning(f"Failed to create report data for checklist {checklist.id}: {e}")
        
        return registration
