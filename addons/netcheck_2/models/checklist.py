from odoo import _, api, fields, models
from odoo.tools.misc import formatLang, format_date, get_lang
from odoo.exceptions import UserError, ValidationError
from odoo.tools import safe_eval
import datetime
import locale
from odoo.tools import format_datetime, format_date
import base64
import pytz
import csv
from io import StringIO


class Checklist(models.Model):
    _name = "checklist.checklist"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = "Checklist"

    @api.model
    def _referencable_models(self):
        models = self.env['ir.model'].search([('checklist_access', '=', True)])
        return [(x.model, x.name) for x in models]

    name = fields.Char(
        string='Name',
        tracking=True,
        required=True,
        translate=False
    )
    state = fields.Selection(
        string="Status",
        selection=[
            ('new', _('New')),
            ('draft', _('Draft')),
            ('ready', _('Ready')),
            ('done', _('Done')),
            ('canceled', _('Canceled'))
        ],
        default='new',
        tracking=True,
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
    )
    day_start = fields.Boolean(
        string="Inizio giornata",
        default=False,
        tracking=True,
    )



    # @api.constrains('day_start')
    # def _check_unique_day_start(self):
    #     """
    #     Ensure that only one checklist template with day_start active exists.
    #     """
    #     for record in self:
    #         if record.day_start:
    #             existing_templates = self.search([
    #                 ('day_start', '=', True),
    #                 ('id', '!=', record.id),
    #                 ('is_template', '=', True)
    #             ])
    #             if existing_templates:
    #                 raise ValidationError(
    #                     _("There can only be one checklist template with 'day_start' active.")
    #                 )
    
    day_end = fields.Boolean(
        string="Fine giornata",
        default=False,
        tracking=True,
    )
    
    # @api.constrains('day_end')
    # def _check_unique_day_end(self):
    #     """
    #     Ensure that only one checklist template with day_end active exists.
    #     """
    #     for record in self:
    #         if record.day_end:
    #             existing_templates = self.search([
    #                 ('day_end', '=', True),
    #                 ('id', '!=', record.id),
    #                 ('is_template', '=', True)
    #             ])
    #             if existing_templates:
    #                 raise ValidationError(
    #                     _("There can only be one checklist template with 'day_end' active.")
    #                 )

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        tracking=True,
        required=True,
        default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        string="Assigned User",
        comodel_name="res.users",
        tracking=True,
        copy=False,
        domain=[('share', '=', False)]
    )
    
    confirmed_date = fields.Date(
        string = "Data di conferma",
        tracking = True,
        store = True
    )

    @api.model
    def _process_confirmed_date_checklists(self):
        """
        This method is intended to be called by a daily cron job.
        It finds all checklists with a confirmed_date of today
        and a state that is not yet 'ready', 'done', or 'canceled',
        and sets their state to 'ready'.
        """
        today = fields.Date.context_today(self)
        checklists_to_update = self.search([
            ('confirmed_date', '=', today),
            ('state', 'in', ['new', 'draft'])
        ])
        checklists_to_update.write({'state': 'ready'})

    description = fields.Text(
        string="Description",
        tracking=True,
        translate=True
    )
    ref_doc_id = fields.Reference(
        selection='_referencable_models',
        string='Associated Object',
        tracking=True,
        copy=False
    )


    # API PER CONTROLLO ESISTENZA ANAGRAFICA CHECKLIST
    @api.model
    def check_key_anagrafica(self, key):
        """
        Returns Boolean
        """
        # use the correct record rule
        results = self.search([
            ('state', '=', 'ready'),
            ('user_id', '=', self.env.user.id),
            # ('user_id','=', self.env.user.id) is
            # redundant but important for app user experience
            # an administrator may want to use the app to compile a checklist
        ])
        for result in results:
            for line in result.line_ids.sorted(key=lambda r: r.position):
                options = [option.code for option in line.option_ids]
                if 'option_selection_model' in options:
                    model_str = line.name_model.model if line.name_model else '[MODELLO_ASSENTE]'
                    line_key = model_str + str(line.option_selection_model)
                    if line_key == key:
                        return True
        return False


    # API PER CHECKLIST SINGOLA DATO ID
    @api.model
    def get_checklist_by_id(self, id):
        """
        Return single checklist by ID
        """
        # use the correct record rule
        results = self.search([
            ('state', '=', 'ready'),
            ('user_id', '=', self.env.user.id),
            ('id', '=', id[0])
            # ('user_id','=', self.env.user.id) is
            # redundant but important for app user experience
            # an administrator may want to use the app to compile a checklist
        ])
        checklists_dict = {
        }
        anagrafiche = {}
        checklists_dict['checklists'] = []

        for result in results:
            lines=[]
            #creo un nuovo dizionario con 
            for line in result.line_ids.sorted(key=lambda r: r.position):
                selection = []
                attrs = {
                    'id': line.id,
                    'name': line.name if line.name else "[NOME ASSENTE]",
                    'type': line.type,
                    'options': [option.code for option in line.option_ids],
                    'value': line.sudo().option_precompiled_test
                    if line.type == 'precompiled' else '',
                    # sudo() because a portal user might not access
                    # the object field
                    'min_char': line.option_min_char if line.type == 'string' else '',
                    'max_char': line.option_max_char if line.type == 'string' else '',
                }
                if 'option_selection_model' in attrs['options']:
                    if not line.name_model:
                        raise UserError("L'opzione 'selezione su modello' per la linea %s nella checklist %s è attiva ma nessun modello è stato assegnato." % (line.name, result.id))
                    model_str = line.name_model.model if line.name_model else '[MODELLO_ASSENTE]'
                    line_key = model_str + str(line.option_selection_model)
                    attrs['keys'] = line_key
                    if line.option_selection_model:
                        values = self.env[line.name_model.model].sudo().search(
                            safe_eval.safe_eval(line.option_selection_model))
                    else:
                        values = self.env[line.name_model.model].sudo().search(
                            [])
                    if line_key not in anagrafiche:
                        anagrafiche[line_key] = []
                        for value in values:
                            anagrafiche[line_key].append(
                                {
                                    'id': value.id,
                                    'name': value.display_name if value.display_name else "[NOME ASSENTE]"
                                }
                            )
                if 'option_selection' in attrs['options']:
                    for value in line.option_selection_string:
                        selection.append(
                            {'id': value.id, 
                             'name': value.display_name if value.display_name else "[NOME ASSENTE]"
                             })
                attrs['selection'] = selection
                lines.append(attrs)
            checklists_dict['checklists'].append({
                'id': result.id,
                'name': line.with_context(lang='it_IT').name if line.name else "[NOME ASSENTE]",
                'gps_position': int(result.gps_position),
                'description': result.description,
                'lines': lines
            })
            checklists_dict['anagrafiche'] = anagrafiche
        return checklists_dict



    #API PAGINATA FINALMENTE --- MATTEO , il canto del cigno
    @api.model
    def get_my_checklist_pagination(self, limit=10, offset=0):
        """
        Return ready checklist assigned to current user
        """
        counter = self.search_count([
            ('state', '=', 'ready'),
            ('user_id', '=', self.env.user.id)
        ])

        # use the correct record rule
        results = self.search([
            ('state', '=', 'ready'),
            ('user_id', '=', self.env.user.id)
            # ('user_id','=', self.env.user.id) is
            # redundant but important for app user experience
            # an administrator may want to use the app to compile a checklist
        ],limit=limit,offset=offset)
        checklists_dict = {
        }
        anagrafiche = {}
        checklists_dict['checklists'] = []
        checklists_dict['counter'] = counter
        for result in results:
            lines=[]
            #creo un nuovo dizionario con 
            for line in result.line_ids.sorted(key=lambda r: r.position):
                selection = []
                attrs = {
                    'id': line.id,
                    'name': line.name if line.name else "[NOME ASSENTE]",
                    'type': line.type,
                    'options': [option.code for option in line.option_ids],
                    'value': line.sudo().option_precompiled_test
                    if line.type == 'precompiled' else '',
                    # sudo() because a portal user might not access
                    # the object field
                    'min_char': line.option_min_char if line.type == 'string' else '',
                    'max_char': line.option_max_char if line.type == 'string' else '',
                }
                if 'option_selection_model' in attrs['options']:
                    if not line.name_model:
                        raise UserError("L'opzione 'selezione su modello' per la linea %s nella checklist %s è attiva ma nessun modello è stato assegnato." % (line.name, result.id))
                    model_str = line.name_model.model if line.name_model else '[MODELLO_ASSENTE]'
                    line_key = model_str + str(line.option_selection_model)
                    attrs['keys'] = line_key
                    
                if 'option_selection' in attrs['options']:
                    for value in line.option_selection_string:
                        selection.append(
                            {'id': value.id, 
                             'name': value.display_name if value.display_name else "[NOME ASSENTE]"
                             })
                attrs['selection'] = selection
                lines.append(attrs)
            checklists_dict['checklists'].append({
                'id': result.id,
                'name': result.name if result.name else "[NOME ASSENTE]",
                'gps_position': int(result.gps_position),
                'description': result.description,
                'lines': lines
            })
            if limit + offset >= counter:
                        # sono alla fine della chiamata per quell'utente
                        # prendo tutte le checklist
                        results = self.search(
                            [("state", "=", "ready"), ("user_id", "=", self.env.user.id)]
                        )
                        for result in results:
                            # provo a filtrare le righe checklist per prendere quelle che hanno 'Selezione su modello' per evitare di scorrerle tutte
                            # for line in result.line_ids.filtered(lambda r: 'option_selection_model' in r.option_ids_string):
                            for line in result.line_ids.filtered(lambda r: 'option_selection_model' in [option.code for option in r.option_ids]):
                                if not line.name_model:
                                    raise UserError("L'opzione 'selezione su modello' per la linea %s nella checklist %s è attiva ma nessun modello è stato assegnato." % (line.name, result.id))
                                model_str = line.name_model.model if line.name_model else '[MODELLO_ASSENTE]'
                                line_key = model_str + str(line.option_selection_model)
                                if line.option_selection_model:
                                    values = self.env[line.name_model.model].sudo().search(
                                        safe_eval.safe_eval(line.option_selection_model))
                                else:
                                    values = self.env[line.name_model.model].sudo().search(
                                        [])
                                if line_key not in anagrafiche:
                                    anagrafiche[line_key] = []
                                    for value in values:
                                        anagrafiche[line_key].append(
                                            {
                                                'id': value.id,
                                                'name': value.display_name if value.display_name else "[NOME ASSENTE]"
                                            }
                                        )
            checklists_dict['anagrafiche'] = anagrafiche
        return checklists_dict

    line_ids = fields.One2many(
        string="Lines",
        comodel_name='checklist.line',
        inverse_name='checklist_id',
        tracking=True
    )
    is_template = fields.Boolean(
        string="Template?",
        default=False,
        copy=False
    )
    is_copied = fields.Boolean(
        string="Copied",
        default=False,
        copy=False
    )
    gps_position = fields.Boolean(
        string="Gps position",
        default=False
    )
    registration_ids = fields.Many2many(
        string="Registration",
        comodel_name="checklist.registration",
        compute="_compute_registrations"
    )
    latitude = fields.Char(string="Latitude", tracking=True)
    longitude = fields.Char(string="Longitude", tracking=True)

    # AGGIUNTA SERVER ACTION MANY2MANY IN BASE ALLO STATO DELLA CHECKLIST (Daniele)
    # creo tanti many2many alle action server per ogni stato della checklist
    draft_server_actions = fields.Many2one(
        comodel_name='ir.actions.server',
        string='Draft Server Actions',
        delegate=False,
        ondelete='restrict',
        required=False,
        help='Server actions called when the checklist state change to cancelled')

    ready_server_actions = fields.Many2one(
        comodel_name='ir.actions.server',
        string='Ready Server Actions',
        delegate=False,
        ondelete='restrict',
        required=False,
        help='Server actions called when the checklist state change to ready')

    done_server_actions = fields.Many2one(
        comodel_name='ir.actions.server',
        string='Done Server Actions',
        delegate=False,
        ondelete='restrict',
        required=False,
        help='Server actions called when the checklist state change to done')

    canceled_server_actions = fields.Many2one(
        comodel_name='ir.actions.server',
        string='Canceled Server Actions',
        delegate=False,
        ondelete='restrict',
        required=False,
        help='Server actions called when the checklist state change to cancelled')

    report_id = fields.Many2one(
        string="Report",
        comodel_name="ir.actions.report",
        domain=[('model', '=', 'checklist.checklist')]
    )

    template_id = fields.Many2one(
        string="Template",
        comodel_name="checklist.checklist",
    )
    
    data_compilazione = fields.Datetime(
        string="Data compilazione",
        tracking=True,
    )
    

    @api.constrains('state')
    def _constrains_state_server_actions(self):
        """
        Funzione che attiva l'action in base allo stato(selection)
        """
        for checklist in self:
            if checklist.state == 'new':
                checklist.state = 'draft'
            if checklist.state == 'canceled':
                self.registration_ids.write({
                    'active': False
                })
            if checklist.state == 'done':
                checklist.data_compilazione = fields.Datetime.now()
            if checklist.state == 'draft' and checklist.sudo().draft_server_actions:
                action = checklist.sudo().draft_server_actions
                ctx = {
                    'active_model': checklist._name,
                    'active_ids': checklist.ids,
                    'active_id': checklist.id
                }
                action.sudo().with_context(**ctx).run()
            if checklist.state == 'ready' and checklist.sudo().ready_server_actions:
                action = checklist.sudo().ready_server_actions
                ctx = {
                    'active_model': checklist._name,
                    'active_ids': checklist.ids,
                    'active_id': checklist.id
                }
                action.sudo().with_context(**ctx).run()
            if checklist.state == 'done' and checklist.sudo().done_server_actions:
                action = checklist.sudo().done_server_actions
                ctx = {
                    'active_model': checklist._name,
                    'active_ids': checklist.ids,
                    'active_id': checklist.id
                }
                action.sudo().with_context(**ctx).run()
            if checklist.state == 'canceled' and checklist.sudo().canceled_server_actions:
                action = checklist.sudo().canceled_server_actions
                ctx = {
                    'active_model': checklist._name,
                    'active_ids': checklist.ids,
                    'active_id': checklist.id
                }
                action.sudo().with_context(**ctx).run()

    # @api.constrains('state')
    # def _constrains_state(self):
    #     for record in self:
    #         if record.state == 'new':
    #             record.state = 'draft'
    #         if record.state == 'canceled':
    #             self.registration_ids.write({
    #                 'active': False
    #             })

    def toggle_active(self):
        for record in self:
            record.active = not record.active

    def create_from_template(self):
        """
        Create new checklist from template and
        return form view
        """
        self.ensure_one()
        checklist = self.copy()
        checklist.write({
            'template_id': self.id,
            'is_template': False,
            'is_copied': True
        })
        for line in self.line_ids:
            new_line = line.copy()
            for option_selection in line.option_selection_string:
                new_option_selection = option_selection.copy()
                new_option_selection.write({
                    "line_id": new_line.id
                })
            new_line.write({
                'ref_doc_id': line.ref_doc_id,
                'checklist_id': checklist.id,
                'option_precompiled': line.option_precompiled,
                # 'option_selection_string': [(6, 0, line.option_selection_string.ids)]
            })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'checklist.checklist',
            'res_id': checklist.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
        }

    def cancel(self):
        self.write({'state': 'canceled'})

    def reset_to_draft(self):
        self.write({'state': 'draft'})

    def ready(self):
        """
        Set checklist state to ready (send to app)
        """
        for record in self:
            error = False
            message = ""
            if not record.line_ids:
                error = True
                message += _('Lines') + "\n"
            if not record.user_id:
                error = True
                message += _('Assigned User') + "\n"
            if error:
                return self.env['bus.bus'].sendone(
                    (self._cr.dbname, 'res.partner', self.env.user.partner_id.id),
                    {
                        'type': 'simple_notification',
                        'title': _('Mandatory field'),
                        'message': message,
                        'sticky': True,
                        'error': True
                    }
                )

            record.state = 'ready'

    def _compute_registrations(self):
        """
        Compute registrations for checklist
        """
        for record in self:
            registrations = self.env['checklist.registration'].search([
                ('checklist_line_id.checklist_id.id', '=', record._origin.id)
            ])
            record.registration_ids = [(6, False, registrations.ids)]

    def close(self):
        for record in self:
            record.state = 'done'

    def check_availability(self):
        """
        check permission:
        no create or modify registration if:
            - checklist state in ['draft', 'done', 'canceled']
            - checklist is template
            - current user is different from assigned user (return record rule exception)
        """
        self.ensure_one()
        checklist = self
        if checklist.state in ['draft', 'done', 'canceled']:
            raise ValidationError(
                _("You can't create or modify registrations on checklist in %s state.")
                % dict(checklist._fields['state'].selection).get(checklist.state)
            )
        if checklist.is_template:
            raise ValidationError(
                _("You can't create or modify registrations on template checklists.")
            )
        if checklist.user_id.id != self.env.user.id:
            raise ValidationError(
                _("You can't create or modify registrations for this row.")
            )
        return

    @api.constrains('ref_doc_id')
    def _constrains_ref_doc_id(self):
        """
        Precompiled lines get the same ref_doc_id
        """
        for record in self:
            for line in record.line_ids:
                if line.type == 'precompiled':
                    line.ref_doc_id = record.ref_doc_id
                    line._compute_option_precompiled_test()

    @api.onchange('ref_doc_id')
    def _onchange_ref_doc_id(self):
        self._constrains_ref_doc_id()

    # API CALL DISACCOPPIANDO MODELLI E CHECKLIST
    @api.model
    def get_my_checklist_v2(self):
        """
        Return ready checklist assigned to current user
        """
        # use the correct record rule
        results = self.search([
            ('state', '=', 'ready'),
            ('user_id', '=', self.env.user.id)
            # ('user_id','=', self.env.user.id) is
            # redundant but important for app user experience
            # an administrator may want to use the app to compile a checklist
        ])
        checklists_dict = {
        }
        anagrafiche = {}
        checklists_dict['checklists'] = []

        for result in results:
            lines=[]
            #creo un nuovo dizionario con 
            for line in result.line_ids.sorted(key=lambda r: r.position):
                selection = []
                attrs = {
                    'id': line.id,
                    'name': line.with_context(lang='it_IT').name if line.name else "[NOME ASSENTE]",
                    'type': line.type,
                    'options': [option.code for option in line.option_ids],
                    'value': line.sudo().option_precompiled_test
                    if line.type == 'precompiled' else '',
                    # sudo() because a portal user might not access
                    # the object field
                    'min_char': line.option_min_char if line.type == 'string' else '',
                    'max_char': line.option_max_char if line.type == 'string' else '',
                }
                if 'option_selection_model' in attrs['options']:
                    if not line.name_model:
                        raise UserError("L'opzione 'selezione su modello' per la linea %s nella checklist %s è attiva ma nessun modello è stato assegnato." % (line.name, result.id))
                    model_str = line.name_model.model if line.name_model else '[MODELLO_ASSENTE]'
                    line_key = model_str + str(line.option_selection_model)
                    attrs['keys'] = line_key
                    if line.option_selection_model:
                        values = self.env[line.name_model.model].sudo().search(
                            safe_eval.safe_eval(line.option_selection_model))
                    else:
                        values = self.env[line.name_model.model].sudo().search(
                            [])
                    if line_key not in anagrafiche:
                        anagrafiche[line_key] = []
                        for value in values:
                            anagrafiche[line_key].append(
                                {
                                    'id': value.id,
                                    'name': value.display_name if value.display_name else "[NOME ASSENTE]"
                                }
                            )
                if 'option_selection' in attrs['options']:
                    for value in line.option_selection_string:
                        selection.append(
                            {'id': value.id, 
                             'name': value.display_name if value.display_name else "[NOME ASSENTE]"
                             })
                attrs['selection'] = selection
                lines.append(attrs)
            checklists_dict['checklists'].append({
                'id': result.id,
                'name': result.name if result.name else "[NOME ASSENTE]",
                'gps_position': int(result.gps_position),
                'description': result.description,
                'lines': lines
            })
            checklists_dict['anagrafiche'] = anagrafiche
        return checklists_dict

    # API CALL
    @api.model
    def get_my_checklists(self):
        """
        Return ready checklist assigned to current user
        """
        # use the correct record rule
        results = self.search([
            ('state', '=', 'ready'),
            ('user_id', '=', self.env.user.id)
            # ('user_id','=', self.env.user.id) is
            # redundant but important for app user experience
            # an administrator may want to use the app to compile a checklist
        ])
        checklists = []

        for result in results:
            lines = []
            for line in result.line_ids.sorted(key=lambda r: r.position):
                selection = []
                attrs = {
                    'id': line.id,
                    'name': line.with_context(lang='it_IT').name,
                    'type': line.type,
                    'options': [option.code for option in line.option_ids],
                    'value': line.sudo().option_precompiled_test
                    if line.type == 'precompiled' else '',
                    # sudo() because a portal user might not access
                    # the object field
                    'min_char': line.option_min_char if line.type == 'string' else '',
                    'max_char': line.option_max_char if line.type == 'string' else '',
                }
                if 'option_selection_model' in attrs['options']:
                    if line.option_selection_model:
                        values = self.env[line.name_model.model].sudo().search(
                            safe_eval.safe_eval(line.option_selection_model))
                    else:
                        values = self.env[line.name_model.model].sudo().search(
                            [])
                    for value in values:
                        selection.append(
                            {'id': value.id, 'name': value.display_name})
                if 'option_selection' in attrs['options']:
                    for value in line.option_selection_string:
                        selection.append(
                            {'id': value.id, 'name': value.display_name})
                attrs['selection'] = selection
                lines.append(attrs)
            checklists.append({
                'id': result.id,
                'name': result.name,
                'gps_position': int(result.gps_position),
                'description': result.description,
                'lines': lines
            })
        return checklists

    def set_gps_position(self, latitude, longitude):
        self.ensure_one()
        if self.env.user.id == self.user_id.id:
            self.sudo().write({
                'latitude': latitude,
                'longitude': longitude
            })
            return True

    def print_report(self):
        reports = self.mapped('report_id')
        if len(reports) == 1:
            return reports.report_action(self)

    def _compute_access_url(self):
        """
        Definisce l'url di accesso alla checklist nel portale
        """
        for record in self:
            record.access_url = "/my/checklist/%s" % (record.id)
    
    def action_export_csv(self):
        # Usa i record correnti (self) invece di cercare active_ids nel contesto
        checklists = self

        # Raggruppa le checklist per data e utente
        groups = {}
        for checklist in checklists:
            # Usa confirmed_date se disponibile, altrimenti data_compilazione, altrimenti data corrente
            date_key = checklist.confirmed_date or (checklist.data_compilazione.date() if checklist.data_compilazione else fields.Date.today())
            user_key = checklist.user_id.id if checklist.user_id else 0
            group_key = (date_key, user_key)
            
            if group_key not in groups:
                groups[group_key] = {'day_start': [], 'others': [], 'day_end': []}
            
            if checklist.day_start:
                groups[group_key]['day_start'].append(checklist)
            elif checklist.day_end:
                groups[group_key]['day_end'].append(checklist)
            else:
                groups[group_key]['others'].append(checklist)

        # Ordina le checklist: day_start -> day_end -> others per ogni gruppo
        ordered_checklists = []
        for group_key in sorted(groups.keys()):  # Ordina per data e poi per utente
            group = groups[group_key]
            ordered_checklists.extend(group['day_start'] + group['day_end'] + group['others'])

        # Raccogli i nomi delle linee nell'ordine specificato (escludi photo e section)
        unique_names = []
        
        for checklist in ordered_checklists:
            lines = checklist.line_ids.filtered(lambda l: l.type not in ['photo', 'section'])
            names = [l.name.strip() or "Senza Nome" for l in lines.sorted(key='position')]
            for n in names:
                if n not in unique_names:
                    unique_names.append(n)

        # Prepara gli header
        headers = ["ID Checklist", "Nome Checklist", "Data", "Utente", "Tipo"] + unique_names

        # Prepara i dati usando l'ordine delle checklist
        rows = []
        for checklist in ordered_checklists:
            # Determina il tipo di checklist
            checklist_type = "Inizio giornata" if checklist.day_start else "Fine giornata" if checklist.day_end else "Standard"
            
            # Determina la data da mostrare
            display_date = checklist.confirmed_date
            
            row = [
                str(checklist.id), 
                checklist.name, 
                str(display_date) if display_date else "",
                checklist.user_id.name if checklist.user_id else "",
                checklist_type
            ]
            
            # mappa nome_linea -> valore
            name_to_val = {}
            for line in checklist.line_ids:
                if line.type not in ['photo', 'section']:  # Escludi photo e section dai valori
                    key = line.name.strip() or "Senza Nome"
                    if line.registration_id:
                        # Converti datetime da UTC a timezone locale
                        if line.type == 'datetime':
                            raw = line.registration_id.raw_value
                            # Rimuovi i microsecondi se presenti per evitare errori di parsing
                            if '.' in str(raw):
                                raw = str(raw).split('.')[0]
                            dt_utc = fields.Datetime.from_string(raw)
                            # Pass a recordset (self) to context_timestamp, not env, to avoid '_context' errors
                            dt_local = fields.Datetime.context_timestamp(self, dt_utc)
                            val = dt_local.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            val = line.registration_id.raw_value
                    elif line.type == 'precompiled':
                        val = line.option_precompiled_test
                    else:
                        val = ""
                    name_to_val[key] = val
            
            # allinea i valori secondo unique_names
            row += [name_to_val.get(n, "") for n in unique_names]
            rows.append(row)

        # Genera CSV
        output = StringIO()
        writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writerow(headers)
        writer.writerows(rows)

        # Ottieni i dati CSV come bytes (con BOM UTF-8)
        csv_data = output.getvalue().encode('utf-8-sig')
        
        # Crea un attachment temporaneo
        filename = 'checklist_export.csv'
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'datas': base64.b64encode(csv_data),
            'mimetype': 'text/csv',
            'res_model': 'checklist.checklist',
            'res_id': self.id if len(self) == 1 else 0,
        })
        
        # Restituisci un'azione per scaricare l'attachment
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }

    def _get_public_data(self):
        """
        Accesso alle registrazione di questa cehcklist
        ad oggi si usa nel controller ---andrebbe portato un po' in tutto---
        """
        self.ensure_one()
        lines = self.line_ids.filtered(lambda x: x.is_visible)
        attrs = {}
        try:
            tz = self.env.context.get('tz') or self.env.user.tz
        except AttributeError:
            tz = self._context.get('tz') or self.env.user.tz
        for o in self:
            attrs[o.id] = {0: []}
            section = 0
            for line in lines.sorted(key='position'):
                hidden = False
                if line.type == 'section' and line.name not in attrs[o.id].keys():
                    attrs[o.id][line.name] = []
                    section = line.name
                else:
                    for option in line.option_ids:
                        """if option.code == 'option_report_hidden':
                            hidden = True"""
                    datas = {'name': line.name, 'value': ''}
                    if line.type in ['string'] and line.registration_id:
                        datas['value'] = line.registration_id.raw_value
                    if line.type in ['integer', 'float'] and line.registration_id:
                        datas['value'] = locale.atof(
                            line.registration_id.raw_value)
                    if line.type in ['datetime'] and line.registration_id:
                        datas['value'] = format_datetime(
                            self.env, line.registration_id.raw_value.split('.')[0], tz=tz)
                    if line.type in ['date'] and line.registration_id:
                        datas['value'] = format_date(
                            self.env, line.registration_id.raw_value.split('.')[0])
                    if line.type in ['precompiled']:
                        datas['value'] = line.option_precompiled_test
                    if line.type in ['boolean'] and line.registration_id:
                        if line.registration_id.raw_value == 'true':
                            datas['value'] = '<i class="fa fa-check-square-o"></i>'
                        else:
                            datas['value'] = '<i class="fa fa-square-o"></i>'
                    if line.type in ['signature', 'photo']:
                        datas['value'] = '<a href="#" data-toggle="modal" data-target="#modal%s"/><img src="%s"' % (
                            line.registration_id.id, line.registration_id.raw_value) + ' style="max-width:100% !important"/></a>'
                        datas['value'] += """
                            <div class='modal fade' id='modal{}' tabindex='-1' role='dialog' aria-labelledby='exampleModalLabel' aria-hidden='true'>
                            <div class='modal-dialog modal-lg' role='document'>
                            
                            <div class='modal-content'>
                                <div class="modal-header">
                                    <button type="button" class="close" data-dismiss="modal" aria-label="Close">
                                    <span aria-hidden="true">&times;</span>
                                    </button>
                                </div>
                                <div class='modal-body'>
                                <img src='{}' style='max-width:100% !important'/>
                                </div>
                                <div class='modal-footer'>
                                    <button type='button' class='btn btn-secondary' data-dismiss='modal'>Close</button>
                                </div>
                            </div>
                            </div>
                            </div>
                            """.format(line.registration_id.id, line.registration_id.raw_value)
                    if line.type in ['selection'] and line.registration_id:
                        response = line.registration_id.raw_value.split(',')
                        val = []

                        for i in response:
                            for ll in line.option_selection_string:
                                if ll.id == int(i):
                                    val.append(ll.name)
                            for option in line.option_ids:
                                if option.code == 'option_selection_model':
                                    val.append(self.env[line.name_model.model].sudo().browse(
                                        int(i)).display_name)
                        datas['value'] = ','.join(val)
                    if line.type == 'audio':
                        datas['value'] = "<audio controls='controls'><source src='%s'/></audio>" % (
                            line.registration_id.raw_value)
                    if line.type == 'video':
                        datas['value'] = "<video controls><source src='%s'/></video>" % (
                            line.registration_id.raw_value)
                    if not hidden:
                        attrs[o.id][section].append(datas)

        return attrs[self.id]


class ChecklistLines(models.Model):
    _name = "checklist.line"
    _inherit = ['mail.thread']
    _description = "Checklist Line"

    @api.model
    def _referencable_models(self):
        models = self.env['ir.model'].search([])
        return [(x.model, x.name) for x in models]

    name = fields.Char(
        string="Description",
        translate=True,
        tracking=True,
    )
    position = fields.Integer(
        string="Position",
        default=99
    )
    checklist_id = fields.Many2one(
        string="Checklist",
        comodel_name="checklist.checklist",
        copy=False,
        tracking=True,
    )
    type = fields.Selection(
        string="Type",
        selection=[
            ('string', _('String')),
            ('integer', _('Integer')),
            ('float', _('Float')),
            ('boolean', _('Boolean')),
            ('video', _('Video')),
            ('photo', _('Photo')),
            ('audio', _('Audio')),
            ('datetime', _('Datetime')),
            ('date', _('Date')),
            #('time', _('Time')),
            ('signature', _('Signature')),
            ('selection', _('Selection')),
            ('section', _('Section')),
            ('precompiled', _('Precompiled'))
        ],
        tracking=True
    )
    option_ids = fields.Many2many(
        string="Options",
        comodel_name="checklist.line.option"
    )
    option_ids_string = fields.Char(
        string="Option string",
        compute="_compute_option_ids_string"
    )
    option_min_char = fields.Integer(
        string="Min Char",
        tracking=True,
    )
    option_max_char = fields.Integer(
        string="Max Char",
        tracking=True,
    )
    option_selection_model = fields.Char(
        string="Model Domain",
        tracking=True,
    )
    option_selection_string = fields.One2many(
        string="Selection",
        comodel_name="checklist.line.option.selection",
        inverse_name="line_id"
    )
    option_precompiled = fields.Char(
        string="Precompiled Field",
        default="display_name",
        tracking=True,
    )
    option_precompiled_test = fields.Char(
        string="Precompiled Preview",
        compute="_compute_option_precompiled_test"
    )
    ref_doc_id = fields.Reference(
        selection='_referencable_models',
        string='Precompiled Object',
        copy=False
    )
    registration_id = fields.Many2one(
        string="Registration",
        comodel_name="checklist.registration",
        compute="_compute_registration"
    )

    name_model = fields.Many2one(string="Model Name", comodel_name="ir.model")
    name_model_string = fields.Char(compute="_compute_name_model_string")

    is_visible = fields.Boolean(
        string="Is Visible?",
        default=True
    )

    def _compute_option_ids_string(self):
        """
        Service function for fields visbility based on options
        """
        for line in self:
            options = ''
            for option in line.option_ids:
                options += option.code + ','
            line.option_ids_string = options

    @api.onchange('option_ids')
    def _onchange_(self):
        """
        Service onchange function for fields visbility based on options
        """
        self._compute_option_ids_string()

    def _compute_name_model_string(self):
        """
        Service function for change model for the domain field widget
        """
        for line in self:
            line.name_model_string = ''
            if line.name_model:
                line.name_model_string = line.name_model.model

    @api.onchange('name_model')
    def _onchange_name_model(self):
        """
        Service onchange function for change model for the domain field widget
        """
        self._compute_name_model_string()

    def _compute_option_precompiled_test(self):
        """
        Service function for the chosen precompiled field preview
        """
        for line in self:
            line.option_precompiled_test = ''

            if line.ref_doc_id:
                field = 'line.ref_doc_id.with_context(self.env.context).%s' % line.option_precompiled
                # verify field
                field_array = line.option_precompiled.split('.')
                response = line.ref_doc_id

                try:
                    for ffield in field_array:
                        response = response[ffield]
                        if isinstance(response, (bool)):
                            if response:
                                response = 'SI'
                            else:
                                response = 'NO'
                    line.option_precompiled_test = response
                except:
                    line.option_precompiled_test = _('%s not available in %s') % (
                        line.option_precompiled, line.checklist_id.ref_doc_id)

                try:
                    # check sui field type
                    try:
                        tz = self.env.context.get('tz') or self.env.user.tz
                    except AttributeError:
                        tz = self._context.get('tz') or self.env.user.tz
                    
                    # Rimuovi i microsecondi se presenti per evitare errori di parsing
                    response_clean = str(response).split('.')[0] if '.' in str(response) else response
                    
                    line.option_precompiled_test = fields.Datetime.context_timestamp(
                        self.with_context(tz=tz),
                        fields.Datetime.from_string(response_clean)
                    )
                    if type(response) is datetime.date:
                        line.option_precompiled_test = format_date(
                            self.env, response)
                    else:
                        dformat = "%s %s" % (
                            get_lang(self.env).date_format,
                            get_lang(self.env).time_format
                        )
                        line.option_precompiled_test = fields.Datetime.context_timestamp(
                            self.with_context(tz=tz),
                            fields.Datetime.from_string(response_clean)
                        ).strftime(dformat)
                except:
                    pass

    @api.onchange('option_precompiled', 'ref_doc_id')
    def _onchange_option_precompiled(self):
        """
        Service onchange function for the chosen precompiled field preview
        """
        self._compute_option_precompiled_test()

    def open_form(self):
        """
        Open line in edit mode
        """
        self.ensure_one()
        context = dict(self.env.context)
        context['form_view_initial_mode'] = 'edit'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'checklist.line',
            'res_id': self.id,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'current',
            'context': context,
        }

    @api.onchange('type')
    def _onchange_type(self):
        """
        When change type reset some fields
        and fill ref_doc_id and option_ids if type is precompiled
        """
        self.option_ids = False
        self.option_min_char = 0
        self.option_max_char = 0
        self.option_selection_model = ''
        self.option_selection_string.sudo().unlink()
        self.option_precompiled = ''
        self.option_precompiled_test = ''
        self.ref_doc_id = False

        if self.type == 'precompiled':
            # if 'precompiled':
            #   - ref_doc_id is populated with
            #     the parent checklist ref_doc_id value
            #   - the readonly option is set
            ids = [self.env.ref('netcheck_2.option_readonly').id]
            self.option_ids = [(6, 0, ids)]
            if self.checklist_id.ref_doc_id:
                self.ref_doc_id = '%s,%s' % (
                    self.checklist_id.ref_doc_id._name,
                    self.checklist_id.ref_doc_id.id
                )
        if self.type == 'section':
            ids = [self.env.ref('netcheck_2.option_readonly').id]
            self.option_ids = [(6, 0, ids)]

    @api.constrains('type')
    def _constrains_type(self):
        for record in self:
            if record.type == 'precompiled':
                record._onchange_type()

    def _compute_registration(self):
        for record in self:
            record.registration_id = False
            res = self.env['checklist.registration'].search([
                ('checklist_line_id', '=', record.id),
                ('active', '=', True)
            ])
            if res:
                record.registration_id = res[0].id


class ChecklistLinesOption(models.Model):
    _name = "checklist.line.option"
    _description = "Checklist Option"

    name = fields.Char(
        string="Name",
        translate=True
    )
    code = fields.Char(
        string="Code"
    )
    available_types = fields.Char(
        string="Available Types"
    )


class ChecklistLinesOption(models.Model):
    _name = "checklist.line.option.selection"
    _description = "Checklist Option Selection"

    name = fields.Char(
        string="Value",
        translate=True
    )
    line_id = fields.Many2one(
        comodel_name='checklist.line',
        string='Checklist line'
    )


class ChecklistRegistration(models.Model):
    _name = "checklist.registration"
    _inherit = ['mail.thread']
    _description = "Registration"

    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True
    )
    checklist_line_id = fields.Many2one(
        string="Checklist Line",
        comodel_name="checklist.line",
        required=True,
        tracking=True,
        ondelete='cascade'
    )
    user_id = fields.Many2one(
        string="User",
        comodel_name="res.users",
        tracking=True,
        domain=[('share', '=', False)],
        default=_default_user,
        required=True,
    )
    raw_value = fields.Text(
        string="Raw Value",
        required=True,
        tracking=True
    )
    close = fields.Boolean(
        string="Close checklist",
        default=False
    )
    related_type = fields.Selection(
        string="Related Field Type",
        related="checklist_line_id.type"
    )
    additional_data = fields.Boolean(
        string="Additional data",
        default=False
    )
    position = fields.Integer(
        string="position",
        related="checklist_line_id.position"
    )

    @api.constrains('user_id', 'raw_value', 'checklist_line_id', 'close')
    def _constrains_user_id(self):

        if self.checklist_line_id:
            checklist = self.checklist_line_id.checklist_id
            checklist.check_availability()

            if not self.checklist_line_id.type:
                raise ValidationError(
                    _("You can't create or modify registrations with no type.")
                )
            if self.close:
                checklist.sudo().close()
            other_registrations = self.search([
                ('checklist_line_id', '=', self.checklist_line_id.id),
                ('id', '!=', self.id)
            ])
            if other_registrations and not self.additional_data:
                other_registrations.with_context(
                    {'no_check': True}).write({'active': False})

    @api.constrains('active')
    def _constrains_active(self):
        """
        Trigger when deactivate registration (cancel):
        no deactivate if checklist state is ready or done
        """
        for record in self:
            if record.checklist_line_id:
                checklist = record.checklist_line_id.checklist_id
                if not record.active:
                    if 'no_check' in self.env.context and self.env.context['no_check']:
                        continue
                    if checklist.state in ['ready', 'done']:
                        raise ValidationError(
                            _("You can't cancel registration on checklist in %s state.")
                            % dict(checklist._fields['state'].selection).get(checklist.state)
                        )
