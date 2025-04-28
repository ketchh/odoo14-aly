from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError, MissingError
import logging
import datetime

_logger = logging.getLogger(__name__)

class TaskTypologyExtension(models.Model):
    _inherit = "task.typology"
    
    is_montaggio = fields.Boolean(
        string="Montaggio Pneumatici TyreTeam",
        default=False,
        tracking=True
    )

class ProjectTaskExtension(models.Model):
    _inherit="project.task"

    data_esecuzione=fields.Datetime(string="Data Esecuzione Montaggio", tracking=True)
    data_prevista_montaggio = fields.Datetime(string="Data Prevista Montaggio", tracking=True)

    is_montaggio = fields.Boolean(related="task_typology_id.is_montaggio", tracking=True)

    tyre_order_id = fields.Char(related="fleet_move_id.tyre_order_id", store=True, tracking=True)


    @api.model
    def _confirm_assembly_date(self, order_id, execution_date):
        """
        Called by external API: sets installation date record
        """
        tasks = self.env["project.task"].search(['&', ("tyre_order_id", '=', order_id), ('is_montaggio', '=', True)])
        if not tasks:
            raise UserError("No task found.")
        else:
            for task in tasks:
                closed_stage_id = self.env["project.task.type"].search(['&',('project_ids', 'in', task.project_id.id),('is_closed', '=', True )], limit=1)
                if not closed_stage_id:
                    raise UserError("No completion phase found for this project.")
                date_format = '%Y-%m-%d %H:%M:%S'
                date_obj = datetime.datetime.strptime(execution_date, date_format)
                task.data_esecuzione = date_obj
                task.stage_id = closed_stage_id[0]
            return True
        
    @api.model
    def _write_expected_assembly_date(self, order_id, expected_date):
        """
        Called by external API: sets scheduled date for installation
        """
        tasks = self.env["project.task"].search(['&', ("tyre_order_id", '=', order_id), ('is_montaggio', '=', True)])
        if not tasks:
            raise UserError("No task found.")
        else:
            for task in tasks:
                date_format = '%Y-%m-%d %H:%M:%S'
                date_obj = datetime.datetime.strptime(expected_date, date_format)
                task.data_prevista_montaggio = date_obj
            return True

    @api.model
    def _change_tyre_repairer(self, order_id, customer_code):
        """
        Called by external API: After selecting a new repairer, a mail is also sent to inform the new one of the assignment
        """
        tasks = self.env["project.task"].search([("tyre_order_id", '=', order_id)])
        if not len(tasks):
            raise UserError("Assembly task for order %s not found." % order_id)
        repairer = self.env["tyre.repairer"].search([("customer_center", '=', customer_code)], limit=1)
        if not len(repairer):
            raise UserError("Repairer %s not found." % customer_code)
        for task in tasks:
            task.fleet_move_id.selected_tyre_repairer = repairer.id
            task.fleet_move_id.send_repairer_selection_mail()
        return True