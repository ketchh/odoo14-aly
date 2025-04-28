from odoo import _, api, fields, models

class FleetMoveCarpentum(models.Model):
    _inherit = "fleet.move"
    
    """ 
    Aggiunti i campi nuovi
    """
    
    codice_incarico = fields.Char(
        string="Codice Incarico",
        tracking=True
    )
    
    code_tipo_entrata_veicolo = fields.Char(
        string="Tipo Entrata Veicolo",
        tracking=True
    )
    
    stato_incarico = fields.Char(
        string="Stato incarico",
        tracking=True
    )
    move_type = fields.Many2one(
        string="Tipologia",
        comodel_name="fleet.move.arval.type"
    )
    n_tasks = fields.Integer(
        string="N Tasks",
        compute="_compute_n_tasks"
    )
    date_dealer_availability = fields.Date(
        string="Data disponibilità Dealer",
        tracking=True
    )
    assigned_to = fields.Many2one(
        string="Assegnato a",
        comodel_name="res.users"
    ) # user_id esiste già ed è il richiedente 
    
    #Letizia
    personal_customer_insurance = fields.Boolean(
        string="Assicurazione personale cliente",
        tracking=True
    )

    cert_insurance = fields.Boolean(
        string="Tipologia certificato assicurativo",
        tracking=True
    )
    
    def assign_to_me(self):
        for record in self:
            record.assigned_to = self.env.user.id
    
    def _compute_n_tasks(self):
        for record in self:
            record.n_tasks=0
            if record.vehicle_id:
                results = self.env['project.task'].search([('vehicle_id','=',record.vehicle_id.id)])
                record.n_tasks=len(results)
    
    def open_tasks(self):
        return {
            'name': _('Tasks for %s') % self.name,
            'res_model': 'project.task',
            'type': 'ir.actions.act_window',
            'context': {},
            'view_mode': 'kanban,tree,form',
            'view_type': 'kanban,tree,form',
            'domain': [('vehicle_id','=', self.vehicle_id.id)]
        }
    
    @api.model
    def create(self, vals):
        """ 
        Assegnazione tipo
        
        e creazione task per RIT DEA
        """
        ttype = False
        stato_incarico = vals.get('stato_incarico', False)
        code_tipo_entrata_veicolo = vals.get('code_tipo_entrata_veicolo', False)
        ttype = self.env['carpentum.api'].sudo().get_type(code_tipo_entrata_veicolo, stato_incarico)
        if ttype:
            vals['move_type'] = ttype
        #LETIZIA
        resttype = self.env['fleet.move.arval.type'].search([('name','=','Fase zero')])
        if resttype and ttype == resttype[0].id:
            return True
        return super(FleetMoveCarpentum, self).create(vals)
    
    @api.constrains('move_type')
    def _create_task(self):
        """ 
        Cerca delle tipologie di task in cui è assegnata al tipologia di incarico
        
        - 17/07/2023: nel caso specifico serve per rit-dea ma può essere utilizzato
        per tutti i sistemi.
        
        ATTENZIONE: se viene modificato il move_type rifà il calcolo e aggiunge il task 
        """
        res = self
        if res.move_type:
            typologies = self.env['task.typology'].search([('move_type','=',res.move_type.id)])
            project_id = self.env['project.project'].search([('is_hub','=',True)])
            if project_id:
                project_id = project_id[0]
            for task_type in typologies:
                attrs = {
                    'task_typology_id': task_type.id,
                    'vehicle_id': res.vehicle_id.id,
                    'partner_id': project_id.partner_id.id,
                    'project_id': project_id.id,
                    'name': task_type.name,
                    'user_id':False
                    #'date_deadline': datetime.datetime.now() + datetime.timedelta(days=delay_days)
                }
                self.env['project.task'].create(attrs)
        return 
        
    @api.model
    def _read_group_state_ids(self, stages, domain,order):
        """
        Serve per mostrare tutti i record dell'oggetto quando
        vai nella kanban view.
        
        CHANGE LOG:
        - 03/07/23 controlla se il tipo è nella fase corretta. viene messo un contesto
        nell'azione del menu e in base a quello fa la query per prendere tutte le fasi
        assegnate a quella tipologia.
        - il contesto è l'identificativo esterno della tipologia
        """
        ttype = self.env.context.get('type', False)
        domain = []
        if ttype:
            # arriva il context e cerco il riferimento 
            record = self.env.ref(ttype)
            if record:
                domain = [('move_type','in',record.ids)]
        stage_ids = self.env['fleet.move.status'].search(domain, order="sequence asc")
        return stage_ids