# The above class is an extension of the "res.users" and "res.partner" models in
# Odoo, adding functionality related to carrier management.
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

# The ResUsersPlanner class is a model that inherits from the res.users model and
# contains a constraint function that updates certain fields of a partner based on
# the user's group membership.
class ResUsersPlanner(models.Model):
    _inherit = "res.users"
    
    @api.constrains('groups_id')
    def _constrains_partner_id_company_carrier_check(self):
        """
        The function updates the company type and company carrier fields of a
        partner if the user has the 'group_carrier_planner' group but not the
        'group_carrier_manager_planner' group.
        
        tested
        """
        for user in self:
            if self.with_user(user).user_has_groups('bloomup_fleet_move_planner.group_carrier_planner') \
            and not self.with_user(user).user_has_groups('bloomup_fleet_move_planner.group_carrier_manager_planner'):
                user.partner_id.write({
                    'company_type': 'company',
                    'company_carrier': True
                })
            

# The ResPartnerPlanner class is an extension of the res.partner model in Odoo
# that adds functionality related to carriers and their employees.
class ResPartnerPlanner(models.Model):
    _inherit = "res.partner"
    
    company_carrier = fields.Boolean(
        string="Carrier",
        default=False,
        tracking=True
    )
    # type address = 'carrier' identify a carrier contact
    type = fields.Selection(
        selection_add=[('carrier',_('Carrier\'s Employee'))]
    ) 
    
    @api.constrains('user_ids')
    def _constrains_user_carrier(self):
        """
        The function checks if the associated user is a group carrier and sets the
        company_carrier field to true.
        
        tested
        """
        for record in self:
            for user in record.user_ids:
                if self.with_user(user).user_has_groups('bloomup_fleet_move_planner.group_carrier_planner') \
                and not self.with_user(user).user_has_groups('bloomup_fleet_move_planner.group_carrier_manager_planner'):
                    record.company_type = 'company'
                    record.company_carrier = True
                        
    @api.constrains('type')
    def _constrains_check_carrier(self):
        """
        The function checks if a partner can be a carrier's employee based on
        certain constraints:
        
        - You cannot select carrier as the address type if you are the parent
          or if the parent is not a carrier
        
        tested
        """
        for record in self:
            if not record.parent_id and record.type=='carrier':
                raise ValidationError(_("""Partner <%s> can't be carrier's employee if it is a parent partner.""") % record.name)
            if record.parent_id and not record.parent_id.company_carrier:
                raise ValidationError(_("""Contact <%s> can't be carrier's employee if it's parent is not carrier""") % record.name)
    
    @api.constrains('company_type')
    def _constrains_company_type_carrier(self):
        """
        This function checks if the company type is 'person' and if there are any
        contacts with the type 'carrier', and if so, it raises a validation error.
        
        Otherwhise company_carrir is set to False.
        
        tested
        """
        for record in self:
            if record.company_type == 'person' and record.company_carrier:
                res = record.child_ids.filtered(lambda x: x.type == 'carrier')
                if res:
                    raise ValidationError(_("Partner <%s> can't be a person because it is a carrier and there are some contact with type='carrier'" % record.name))
                record.company_carrier = False
    
    @api.constrains('company_carrier')
    def _check_carrier_person(self):
        """
        The function checks if a partner is a person and cannot be a carrier.
        
        tested
        """
        for record in self:
            if record.company_carrier and record.company_type == 'person':
                raise ValidationError(_("""Partner <%s> is a person and can't be a carrier""") % record.name)