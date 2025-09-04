# -*- coding: utf-8 -*-
from odoo import api, models
import locale
from odoo.tools import format_datetime, format_date


class ChecklistEnhancedReport(models.AbstractModel):
    """
    Modello per il report migliorato delle checklist che utilizza 
    la struttura dati ottimizzata
    """
    _name = 'report.netcheck_2_report_enhanced.report_checklist_enhanced'
    _description = 'Enhanced Checklist Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        Genera i dati per il report utilizzando la struttura dati ottimizzata
        """
        # Ottieni i dati di report
        report_data = self.env['checklist.report.data'].browse(docids)
        
        # Configura il locale per la formattazione numerica
        lang = self.env['res.lang'].sudo().search([
            ('code', '=', self.env.context.get('lang'))
        ], limit=1)
        
        if lang:
            if hasattr(locale, '_override_localeconv'):
                locale._override_localeconv["thousands_sep"] = lang.thousands_sep
                locale._override_localeconv["decimal_point"] = lang.decimal_point
        
        # Prepara i dati per il template
        processed_data = []
        
        for report in report_data:
            # Raggruppa le linee per sezione
            sections = {}
            lines_without_section = []
            
            for line in report.line_ids.filtered(lambda l: not l.is_section).sorted('sequence'):
                section_name = line.section_name or 'General'
                
                if section_name not in sections:
                    sections[section_name] = []
                
                # Prepara i dati della linea
                line_data = {
                    'line': line,
                    'name': line.line_name,
                    'type': line.line_type,
                    'has_data': line.has_data,
                    'formatted_value': line.formatted_value,
                    'registration_count': line.registration_count,
                    'registrations': []
                }
                
                # Aggiungi le registrazioni
                for registration in line.registration_ids.sorted('create_date'):
                    reg_data = {
                        'registration': registration,
                        'raw_value': registration.raw_value,
                        'formatted_value': registration.formatted_value,
                        'display_value': registration.display_value,
                        'user_name': registration.user_id.name,
                        'create_date': registration.create_date,
                    }
                    line_data['registrations'].append(reg_data)
                
                sections[section_name].append(line_data)
            
            # Prepara i dati del report
            report_info = {
                'report': report,
                'checklist_name': report.checklist_name,
                'user_name': report.user_id.name,
                'completion_date': report.completion_date,
                'confirmed_date': report.confirmed_date,
                'company_name': report.company_id.name,
                'has_gps': bool(report.latitude and report.longitude),
                'latitude': report.latitude,
                'longitude': report.longitude,
                'day_start': report.day_start,
                'day_end': report.day_end,
                'ref_doc_name': report.ref_doc_name,
                'total_lines': report.total_lines,
                'completed_lines': report.completed_lines,
                'completion_percentage': report.completion_percentage,
                'sections': sections,
                'section_names': sorted(sections.keys())
            }
            
            processed_data.append(report_info)
        
        return {
            'docs': report_data,
            'processed_data': processed_data,
            'format_datetime': self._format_datetime,
            'format_date': self._format_date,
        }

    def _format_datetime(self, datetime_value, tz=None):
        """
        Helper per formattare le date/time
        """
        if not datetime_value:
            return ''
        try:
            return format_datetime(self.env, datetime_value, tz=tz)
        except:
            return str(datetime_value)

    def _format_date(self, date_value):
        """
        Helper per formattare le date
        """
        if not date_value:
            return ''
        try:
            return format_date(self.env, date_value)
        except:
            return str(date_value)
