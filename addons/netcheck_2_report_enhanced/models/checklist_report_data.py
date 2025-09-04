# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ChecklistReportData(models.Model):
    """
    Struttura dati ottimizzata per i report delle checklist completate.
    Questa tabella viene popolata automaticamente quando una checklist 
    viene completata e fornisce una struttura più efficiente per la generazione dei report.
    """
    _name = 'checklist.report.data'
    _description = 'Checklist Report Data'
    _order = 'checklist_id, sequence'
    _rec_name = 'checklist_name'

    # Riferimenti base
    checklist_id = fields.Many2one(
        'checklist.checklist',
        string='Checklist',
        required=True,
        ondelete='cascade',
        index=True
    )
    checklist_name = fields.Char(
        string='Checklist Name',
        required=True,
        index=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        index=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True
    )
    completion_date = fields.Datetime(
        string='Completion Date',
        required=True,
        index=True
    )
    confirmed_date = fields.Date(
        string='Confirmed Date',
        index=True
    )
    
    # Dati GPS
    latitude = fields.Char(string='Latitude')
    longitude = fields.Char(string='Longitude')
    
    # Metadati checklist
    day_start = fields.Boolean(string='Day Start')
    day_end = fields.Boolean(string='Day End')
    
    # Riferimento al documento associato
    ref_doc_model = fields.Char(string='Referenced Document Model')
    ref_doc_id = fields.Integer(string='Referenced Document ID')
    ref_doc_name = fields.Char(string='Referenced Document Name')
    
    # Linee della checklist (struttura denormalizzata per performance)
    line_ids = fields.One2many(
        'checklist.report.data.line',
        'report_data_id',
        string='Report Lines'
    )
    
    # Campi computati per statistiche
    total_lines = fields.Integer(
        string='Total Lines',
        compute='_compute_statistics',
        store=True
    )
    completed_lines = fields.Integer(
        string='Completed Lines', 
        compute='_compute_statistics',
        store=True
    )
    completion_percentage = fields.Float(
        string='Completion %',
        compute='_compute_statistics',
        store=True
    )
    
    @api.depends('line_ids', 'line_ids.has_data')
    def _compute_statistics(self):
        for record in self:
            record.total_lines = len(record.line_ids)
            record.completed_lines = len(record.line_ids.filtered('has_data'))
            if record.total_lines > 0:
                record.completion_percentage = (record.completed_lines / record.total_lines) * 100
            else:
                record.completion_percentage = 0

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.checklist_name} - {record.user_id.name}"
            if record.completion_date:
                name += f" ({record.completion_date.strftime('%d/%m/%Y %H:%M')})"
            result.append((record.id, name))
        return result


class ChecklistReportDataLine(models.Model):
    """
    Linee della struttura dati per report - ogni linea rappresenta un campo della checklist
    con supporto per registrazioni multiple (utile per foto e altri campi con dati multipli)
    """
    _name = 'checklist.report.data.line'
    _description = 'Checklist Report Data Line'
    _order = 'report_data_id, sequence, position'

    report_data_id = fields.Many2one(
        'checklist.report.data',
        string='Report Data',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    # Informazioni della linea originale
    line_name = fields.Char(string='Line Name', required=True)
    line_type = fields.Selection([
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('video', 'Video'),
        ('photo', 'Photo'),
        ('audio', 'Audio'),
        ('datetime', 'Datetime'),
        ('date', 'Date'),
        ('signature', 'Signature'),
        ('selection', 'Selection'),
        ('section', 'Section'),
        ('precompiled', 'Precompiled')
    ], string='Type', required=True)
    
    sequence = fields.Integer(string='Sequence', default=10)
    position = fields.Integer(string='Position')
    is_section = fields.Boolean(string='Is Section', compute='_compute_is_section', store=True)
    section_name = fields.Char(string='Section Name')
    
    # Dati delle registrazioni - supporto per registrazioni multiple
    registration_ids = fields.One2many(
        'checklist.report.data.registration',
        'line_id',
        string='Registrations'
    )
    
    # Campi computati per facilità d'uso nei template
    has_data = fields.Boolean(
        string='Has Data',
        compute='_compute_has_data',
        store=True
    )
    primary_value = fields.Text(
        string='Primary Value',
        compute='_compute_primary_value',
        store=True
    )
    formatted_value = fields.Html(
        string='Formatted Value',
        compute='_compute_formatted_value',
        store=True
    )
    registration_count = fields.Integer(
        string='Registration Count',
        compute='_compute_registration_count',
        store=True
    )
    
    @api.depends('line_type')
    def _compute_is_section(self):
        for record in self:
            record.is_section = record.line_type == 'section'
    
    @api.depends('registration_ids')
    def _compute_has_data(self):
        for record in self:
            record.has_data = bool(record.registration_ids)
    
    @api.depends('registration_ids', 'registration_ids.raw_value')
    def _compute_primary_value(self):
        for record in self:
            if record.registration_ids:
                record.primary_value = record.registration_ids[0].raw_value
            else:
                record.primary_value = ''
    
    @api.depends('registration_ids')
    def _compute_registration_count(self):
        for record in self:
            record.registration_count = len(record.registration_ids)
    
    @api.depends('registration_ids', 'line_type', 'registration_ids.formatted_value')
    def _compute_formatted_value(self):
        for record in self:
            if not record.registration_ids:
                record.formatted_value = ''
                continue
            
            if record.line_type in ['photo', 'signature']:
                # Per le foto, crea una galleria
                if len(record.registration_ids) == 1:
                    record.formatted_value = record.registration_ids[0].formatted_value
                else:
                    gallery_html = '<div class="photo-gallery">'
                    for i, reg in enumerate(record.registration_ids):
                        gallery_html += f'<div class="photo-item">'
                        gallery_html += f'<small>Foto {i+1}:</small><br/>'
                        gallery_html += reg.formatted_value
                        gallery_html += '</div>'
                    gallery_html += '</div>'
                    record.formatted_value = gallery_html
            elif record.line_type == 'selection':
                # Per le selezioni, unisci i valori
                values = [reg.formatted_value for reg in record.registration_ids if reg.formatted_value]
                record.formatted_value = ', '.join(values)
            else:
                # Per gli altri tipi, prendi il primo valore
                record.formatted_value = record.registration_ids[0].formatted_value if record.registration_ids else ''


class ChecklistReportDataRegistration(models.Model):
    """
    Registrazioni individuali per ogni linea - supporta registrazioni multiple per campo
    """
    _name = 'checklist.report.data.registration'
    _description = 'Checklist Report Data Registration'
    _order = 'line_id, create_date'

    line_id = fields.Many2one(
        'checklist.report.data.line',
        string='Report Line',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    # Dati originali della registrazione
    original_registration_id = fields.Integer(string='Original Registration ID')
    user_id = fields.Many2one('res.users', string='User', required=True)
    raw_value = fields.Text(string='Raw Value', required=True)
    create_date = fields.Datetime(string='Registration Date', required=True)
    
    # Valore formattato per il display
    formatted_value = fields.Html(
        string='Formatted Value',
        compute='_compute_formatted_value',
        store=True
    )
    display_value = fields.Text(
        string='Display Value',
        compute='_compute_display_value', 
        store=True
    )
    
    @api.depends('raw_value', 'line_id.line_type')
    def _compute_formatted_value(self):
        for record in self:
            line_type = record.line_id.line_type
            raw_value = record.raw_value
            
            if line_type in ['photo', 'signature']:
                record.formatted_value = f'<img src="{raw_value}" style="max-width: 200px; max-height: 200px; margin: 5px;" class="img-responsive"/>'
            elif line_type == 'boolean':
                if raw_value == 'true':
                    record.formatted_value = '<i class="fa fa-check-square-o text-success"></i> Sì'
                else:
                    record.formatted_value = '<i class="fa fa-square-o text-muted"></i> No'
            elif line_type == 'video':
                record.formatted_value = f'<video controls style="max-width: 300px;"><source src="{raw_value}"/></video>'
            elif line_type == 'audio':
                record.formatted_value = f'<audio controls><source src="{raw_value}"/></audio>'
            elif line_type in ['datetime', 'date']:
                try:
                    if line_type == 'datetime':
                        dt = fields.Datetime.from_string(raw_value.split('.')[0])
                        record.formatted_value = fields.Datetime.to_string(dt)
                    else:
                        record.formatted_value = raw_value
                except:
                    record.formatted_value = raw_value
            else:
                record.formatted_value = raw_value or ''
    
    @api.depends('formatted_value', 'line_id.line_type')
    def _compute_display_value(self):
        for record in self:
            if record.line_id.line_type in ['photo', 'signature', 'video', 'audio']:
                record.display_value = f'[{record.line_id.line_type.upper()}]'
            elif record.line_id.line_type == 'boolean':
                record.display_value = 'Sì' if record.raw_value == 'true' else 'No'
            else:
                record.display_value = record.raw_value or ''
