from odoo import _, api, fields, models
from uuid import uuid4

class FastApiToken(models.Model):
    _name="fastapi.token"
    _description="Fast Api Token"
    
    token = fields.Char(
        string="Fast Api Token",
    )
    user_id = fields.Many2one(
        string="User",
        comodel_name="res.users"
    )

class ResUsers(models.Model):
    _inherit = "res.users"
    
    def _generate_fastapi_token(self):
        self.ensure_one()
        token = uuid4()
        res = self.env['fastapi.token'].sudo().search([('user_id','in',self.ids)])
        print('####', res)
        if res:
            res.sudo().unlink()
        self.env['fastapi.token'].sudo().create(
            {'token': token, 'user_id': self.id}
        )
        return str(token)
        
        
    
        