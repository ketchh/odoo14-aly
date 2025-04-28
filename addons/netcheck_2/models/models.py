from odoo import _, api, fields, models

class ChecklistModel(models.Model):
    _inherit = "ir.model"

    checklist_access = fields.Boolean(
        string="Checklist Access",
        default=False
    )

    @api.constrains('checklist_access')
    def _constrains_checklist_access(self):
        """
        If checklist_access is True
        create Window Action for the current model
        to reach the related checklists.

        If checklist_access is False
        remove Window Action if exists.
        """

        for omodel in self:
            if omodel.checklist_access:
                action = {
                    'name': _('Go to Checklists'),
                    'type': 'ir.actions.act_window',
                    'view_mode': 'tree',
                    'view_id': self.env.ref('netcheck_2.checklist_checklist_view_tree').id,
                    'res_model': 'checklist.checklist',
                    'domain': "[('ref_doc_id','=','"+omodel.model+",'+str(active_id))]",
                    'binding_model_id': omodel.id,
                    'go_to_checklist': True
                }
                res = self.env['ir.actions.act_window'].create(action)
            else:
                action = self.env['ir.actions.act_window'].search([
                    ('go_to_checklist','=',True),
                    ('binding_model_id', '=', omodel.id)
                ])
                if action:
                    action.sudo().unlink()

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    group_allow_checklist_association = fields.Boolean(
        string="Allow Checklist Association with Models",
        implied_group="netcheck_2.group_allow_checklist_association"
    )

class ActWiondow(models.Model):
    _inherit="ir.actions.act_window"

    go_to_checklist = fields.Boolean(string="Go To Checklist", default=False)