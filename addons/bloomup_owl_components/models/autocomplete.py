from odoo import _, api, fields, models
import time

class AutocompleteResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def owl_autocomplete(self, model, text, 
        depends_model, depends_field, depends_value):
        """
        Effettua l'autocomplete sul field
        model: modello su cui fare la query
        text: stringa su cui fare =ilike
        """
        domain = [
            ('name', '=ilike', text+'%')
        ]
        if depends_model and depends_field and depends_value:
            results = self.env[depends_model].sudo().with_context({'lang':self.env.user.lang}).search([('name', '=ilike', depends_value)])
            if results:
                domain.append((depends_field, '=', results[0].id))
        results = self.env[model].sudo().with_context({'lang':self.env.user.lang}).search(domain)
        response = []
        for res in results:
            response.append(res.with_context({'lang':self.env.user.lang}).name.upper())
        return response