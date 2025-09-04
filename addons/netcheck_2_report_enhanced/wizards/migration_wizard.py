# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ChecklistReportDataMigrationWizard(models.TransientModel):
    """
    Wizard per migrare le checklist completate nella nuova struttura dati per report
    """
    _name = 'checklist.report.data.migration.wizard'
    _description = 'Checklist Report Data Migration Wizard'

    checklist_count = fields.Integer(
        string='Checklist da Migrare',
        compute='_compute_checklist_count'
    )
    date_from = fields.Date(
        string='Da Data',
        default=lambda self: fields.Date.today().replace(month=1, day=1)  # Inizio anno
    )
    date_to = fields.Date(
        string='A Data',
        default=fields.Date.today
    )
    company_ids = fields.Many2many(
        'res.company',
        string='Aziende',
        default=lambda self: self.env.companies
    )
    user_ids = fields.Many2many(
        'res.users',
        string='Utenti',
        domain=[('share', '=', False)]
    )
    force_recreate = fields.Boolean(
        string='Forza Ricreazione',
        help='Se attivato, ricreerà i dati di report anche per checklist che ne hanno già'
    )
    migration_status = fields.Text(
        string='Status Migrazione',
        readonly=True
    )
    
    @api.depends('date_from', 'date_to', 'company_ids', 'user_ids', 'force_recreate')
    def _compute_checklist_count(self):
        for wizard in self:
            domain = [
                ('state', '=', 'done'),
                ('data_compilazione', '>=', wizard.date_from),
                ('data_compilazione', '<=', wizard.date_to),
            ]
            
            if wizard.company_ids:
                domain.append(('company_id', 'in', wizard.company_ids.ids))
            
            if wizard.user_ids:
                domain.append(('user_id', 'in', wizard.user_ids.ids))
            
            if not wizard.force_recreate:
                domain.append(('has_report_data', '=', False))
            
            wizard.checklist_count = self.env['checklist.checklist'].search_count(domain)

    def action_migrate(self):
        """
        Esegue la migrazione delle checklist selezionate
        """
        self.ensure_one()
        
        if self.checklist_count == 0:
            raise UserError(_('Nessuna checklist trovata con i criteri specificati.'))
        
        # Costruisce il dominio
        domain = [
            ('state', '=', 'done'),
            ('data_compilazione', '>=', self.date_from),
            ('data_compilazione', '<=', self.date_to),
        ]
        
        if self.company_ids:
            domain.append(('company_id', 'in', self.company_ids.ids))
        
        if self.user_ids:
            domain.append(('user_id', 'in', self.user_ids.ids))
        
        if not self.force_recreate:
            domain.append(('has_report_data', '=', False))
        
        # Trova le checklist
        checklists = self.env['checklist.checklist'].search(domain)
        
        success_count = 0
        error_count = 0
        error_messages = []
        
        for checklist in checklists:
            try:
                if self.force_recreate and checklist.has_report_data:
                    # Elimina i dati esistenti se forza ricreazione
                    checklist.report_data_ids.unlink()
                
                checklist.create_report_data()
                success_count += 1
                
            except Exception as e:
                error_count += 1
                error_message = f"Checklist {checklist.id} ({checklist.name}): {str(e)}"
                error_messages.append(error_message)
                _logger.warning(f"Migration failed for checklist {checklist.id}: {e}")
        
        # Aggiorna lo status
        status_message = f"""
Migrazione Completata:
• Checklist migrate con successo: {success_count}
• Errori: {error_count}
• Totale processate: {len(checklists)}

"""
        
        if error_messages:
            status_message += "Errori dettagliati:\n" + "\n".join(error_messages[:10])
            if len(error_messages) > 10:
                status_message += f"\n... e altri {len(error_messages) - 10} errori."
        
        self.migration_status = status_message
        
        # Restituisce la vista del wizard con i risultati
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'checklist.report.data.migration.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'migration_completed': True}
        }

    def action_view_migrated_data(self):
        """
        Apre la vista dei dati di report migrati
        """
        self.ensure_one()
        
        domain = []
        if self.date_from:
            domain.append(('completion_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('completion_date', '<=', self.date_to))
        if self.company_ids:
            domain.append(('company_id', 'in', self.company_ids.ids))
        if self.user_ids:
            domain.append(('user_id', 'in', self.user_ids.ids))
        
        return {
            'name': _('Dati Report Migrati'),
            'type': 'ir.actions.act_window',
            'res_model': 'checklist.report.data',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'search_default_group_by_completion_date': 1}
        }
