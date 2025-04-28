from odoo import _, api, fields, models

class Checklist(models.Model):
    _inherit = "checklist.checklist"
    
    auto_create_move_type = fields.Many2many(
        string="Auto creation Typology",
        comodel_name="fleet.move.arval.type"
    )

class FleetMoveChecklist(models.Model):
    _inherit = "fleet.move"
    
    @api.constrains('state')
    def _create_auto_checklist(self,white_label=None):
        """
        Funzione per l'azione server che prende i modelli con campo auto_create == True
        e crea le checklist corrispondenti per la movimentazione corrente
        azione: Creazione automatica della checklist
        """
        
        for record in self:
            if record.move_type:
                if white_label:
                    checklist_models = self.env['checklist.checklist'].sudo().search([
                        ('auto_create', '=', True), ('is_template', '=', True),
                        ('white_label','=',white_label),('auto_create_state', '=', record.state.id),
                        ('auto_create_move_type', '=', record.move_type.id)
                    ])
                else:
                    checklist_models = self.env['checklist.checklist'].sudo().search([
                        ('auto_create', '=', True), ('is_template', '=', True),
                        ('auto_create_state', '=', record.state.id),
                        ('auto_create_move_type', '=', record.move_type.id)
                    ])
                #print('### move_type ', record.state, checklist_models)
            else:
                if white_label:
                    checklist_models = self.env['checklist.checklist'].sudo().search([
                        ('auto_create', '=', True), ('is_template', '=', True),
                        ('white_label','=',white_label),('auto_create_state', '=', record.state.id)
                    ])
                else:
                    checklist_models = self.env['checklist.checklist'].sudo().search([
                        ('auto_create', '=', True), ('is_template', '=', True),
                        ('auto_create_state', '=', record.state.id)
                    ])
                #print('###', record.state, checklist_models)
            for checklist_model in checklist_models:
                checklist = checklist_model.copy()
                name = checklist.name
                checklist.with_context({'lang':record.customer_id.lang}).write({
                    'is_template': False,
                    'is_copied': True,
                    'name': "[{}]{}".format(record.vehicle_id.license_plate,name)
                })
                for line in checklist_model.line_ids:
                    new_line = line.copy()
                    new_line.write({
                        'checklist_id': checklist.id,
                        'option_precompiled': line.option_precompiled
                    })
                checklist.write({
                    'ref_doc_id': "fleet.move,%s" % record.id,
                    'user_id': record.employee_id.user_id.id if record.employee_id else False,
                    
                })
