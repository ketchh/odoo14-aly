from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import datetime
import json

class ChecklistLines(models.Model):
    _inherit = "checklist.line"
    
    type = fields.Selection(
        selection_add=[('damage',_('Damage')),('rating','Rating')]
    )
    number_of_damages = fields.Integer(
        string="Number of damages",
        compute="_compute_number_of_damages"
    )
    
    def _compute_number_of_damages(self):
        for record in self:
            results = self.env['checklist.damage'].search([
                ('checklist_line_id','=',record.id),
                ('active', '=', True)
            ])
            record.number_of_damages = len(results)

class Damage(models.Model):
    _name = "checklist.damage"
    _description = "Damage"
    
    @api.model
    def _default_user(self):
        return self.env.context.get('user_id', self.env.user.id)

    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
        related="registration_id.active"
    )
    checklist_line_id = fields.Many2one(
        string="Checklist Line",
        comodel_name="checklist.line",
        required=True,
        ondelete='cascade'
    ) 
    registration_id = fields.Many2one(
        string="Registration",
        comodel_name="checklist.registration"
    )
    type = fields.Char(
        string="Type",
        tracking=True
    )
    note = fields.Text(
        string="Note",
        tracking=True
    )
    images = fields.One2many(
        string="Images",
        comodel_name="checklist.damage.image",
        inverse_name="damage_id"
    )
    coordinate_x = fields.Char(
        string="Coordinate X",
        tracking=True
    )
    coordinate_y = fields.Char(
        string="Coordinate Y",
        tracking=True
    )
    user_id = fields.Many2one(
        string="User",
        comodel_name="res.users",
        tracking=True,
        domain=[('share', '=', False)],
        default=_default_user,
        required=True,
    )
    
    @api.constrains('checklist_line_id')
    def _constrains_checklist_line_id(self):
        for record in self:
            if record.checklist_line_id:
                checklist = record.checklist_line_id.checklist_id
                checklist.check_availability()
                
    @api.model
    def save_damage(self, line_id, type, note, x, y, images):
        """
        line_id : checklist line id
        type : type of damage (string),
        note: note
        x,y : damage coordinates
        images: list of base64 images
        """
        if not line_id or not type or not x or not y:
            raise ValidationError(_('Line_id, type, x or y are missing.'))
        registration = self.env['checklist.registration'].search([
            ('checklist_line_id', '=', int(line_id))
        ])
        if registration:
            attrs = {
                'checklist_line_id': int(line_id),
                'registration_id': registration[0].id,
                'type': type,
                'note': note,
                'coordinate_x': x,
                'coordinate_y': y,
                'images': [
                    (0, 0, {
                        'raw_value': raw,
                    }) for raw in images
                ]            
            }
            damage_id = self.create(attrs)
            return damage_id.id
        return False
    
class DamageImage(models.Model):
    _name = "checklist.damage.image"
    _description = "Damage Image"

    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True
    )
    field_type = fields.Char(
        string="Field Type",
        default="photo"
    )
    raw_value = fields.Text(
        string="Raw Value",
        required=True,
        tracking=True
    )   
    damage_id = fields.Many2one(
        string="Damage",
        comodel_name="checklist.damage"
    )
    user_id = fields.Many2one(
        string="User",
        comodel_name="res.users",
        related="damage_id.user_id"
    )

class AutomotiveChecklist(models.Model):
    _inherit = "checklist.checklist"
    
    @api.model
    def get_my_checklists(self):
        checklists = super(AutomotiveChecklist, self).get_my_checklists()
        for check in checklists:
            for line in check['lines']:
                if line['type'] == 'damage':
                    line['damage_config'] = [
                        {"title": "Cofano", "posX": 133, "posY": 146, "dimX": 165, "dimY": 200},
                        {
                            "title": "Vetro Anteriore", "posX": 272, "posY": 145, "dimX": 125, "dimY": 190},
                        {
                            "title": "Vetro Posteriore", "posX": 630, "posY": 168, "dimX": 130, "dimY": 155},
                        {
                            "title": "Parafango Anteriore dx",
                            "posX": 123,
                            "posY": 28,
                            "dimX": 88,
                            "dimY": 46},
                        {
                            "title": "Parafango Anteriore sx",
                            "posX": 123,
                            "posY": 405,
                            "dimX": 88,
                            "dimY": 46},
                        {
                            "title": "Parafango Posteriore dx",
                            "posX": 680,
                            "posY": 28,
                            "dimX": 115,
                            "dimY": 46},
                        {
                            "title": "Parafango Posteriore sx",
                            "posX": 680,
                            "posY": 405,
                            "dimX": 115,
                            "dimY": 46},
                        {
                            "title": "Ruota Anteriore dx", "posX": 210, "posY": 0, "dimX": 70, "dimY": 70},
                        {
                            "title": "Ruota Anteriore sx", "posX": 210, "posY": 405, "dimX": 70, "dimY": 70},
                        {
                            "title": "Ruota Posteriore dx", "posX": 605, "posY": 0, "dimX": 70, "dimY": 70},
                        {
                            "title": "Ruota Posteriore sx", "posX": 605, "posY": 405, "dimX": 70, "dimY": 70},
                        {
                            "title": "Porta Anteriore dx", "posX": 325, "posY": 38, "dimX": 150, "dimY": 120},
                        {
                            "title": "Porta Anteriore sx",
                            "posX": 325,
                            "posY": 315,
                            "dimX": 150,
                            "dimY": 120},
                        {
                            "title": "Porta Posteriore dx",
                            "posX": 485,
                            "posY": 38,
                            "dimX": 150,
                            "dimY": 132},
                        {
                            "title": "Porta Posteriore sx",
                            "posX": 485,
                            "posY": 315,
                            "dimX": 150,
                            "dimY": 132},
                        {
                            "title": "Paraurti Anteriore", "posX": 5, "posY": 135, "dimX": 130, "dimY": 215},
                        {
                            "title": "Paraurti Posteriore",
                            "posX": 780,
                            "posY": 135,
                            "dimX": 130,
                            "dimY": 215},
                        {
                            "title": "Foto esterna Anteriore",
                            "posX": 0,
                            "posY": 0,
                            "dimX": 464,
                            "dimY": 485},
                        {
                            "title": "Foto esterna Posteriore",
                            "posX": 465,
                            "posY": 0,
                            "dimX": 464,
                            "dimY": 485},
                    ]
        return checklists
    
    def _get_public_data(self):
        nodes = super(AutomotiveChecklist, self)._get_public_data()
        section = 0
        lines = self.line_ids.filtered(lambda x: x.is_visible)
        attrs = {}
        for line in lines.sorted(key='position'):
            hidden = False
            if line.type == 'section':
                section = line.name
            else:
                if line.type == 'damage':
                    for ll in nodes[section]:
                        if ll['name'] == line.name:
                            if line.registration_id.raw_value:
                                # qua va la roba dei danni
                                ll['value'] = '<img src="%s"' % (line.registration_id.raw_value) + ' style="max-width:100% !important"/>' 
                                
                                damages = self.env['checklist.damage'].sudo().search([('registration_id','=',line.registration_id.id)])
                                for damage in damages:
                                    ll['value'] += '<br/><smal>%s-%s</small><br/>' % (damage.type, damage.note)
                                    for image in damage.images:
                                        ll['value'] += '<a href="#" data-toggle="modal" data-target="#modal%s"/><img src="%s"' % (image.id,image.raw_value) + ' style="max-width:100% !important"/></a>'
                                        ll['value'] += """
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
                                        """.format(image.id, image.raw_value)
        return nodes