from odoo import _, api, fields, models
import time

class AutocompleteResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def get_badge(self, model, field):
        """
        Ritorna il numero di righe per model
        - model: nome modello
        - field: campo OWNER che rappresente il proprietario (esempio: partner_id)
        """
        partner = self.env.user.partner_id
        owner = partner.id
        if partner.parent_id:
            owner = partner.parent_id.id
        domain = [
            (field, '=', owner)
        ]
        count = self.env[model].sudo().search_count(domain)
        return count
    

    #creare tabella di backup
    #
    #'sterilizzare' la macchina
    #posso aggionare la macchina usando l'odoo-bin
    #ma devo usare service odoo14 per gestire il servizio
    #service odoo14 restart
    #