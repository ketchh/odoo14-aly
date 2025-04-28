# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ChecklistChecklist(models.Model):
    _inherit = "checklist.checklist"

    # ritorna un dizionario con chiave la variabile della registrazione e valore il valore della registrazione.
    # Si lavora sulle registration_ids della checklist
    def get_registrations_variable_value_dict(self):
        """
        The function `get_registrations_variable_value_dict` returns a dictionary mapping registration
        variables to their corresponding values.
        :return: a dictionary called `variable_value_dict` which contains the variable names as keys and
        their corresponding values as values.
        """
        self.ensure_one()
        variable_value_dict = {}
        if self.registration_ids:
            for registration in self.registration_ids:
                variable_value_dict[registration.variable] = "%s" % (
                    registration.raw_value)
        return variable_value_dict

    # dato un modello crea un record utilizzando le variabili delle registrazioni
    def create_model_record_from_registrations_variable(self, odoo_model):
        """
        The function creates a record in an Odoo model based on the registrations variable.

        :param odoo_model: The `odoo_model` parameter is the name of the Odoo model that you want to
        create records in. It should be a string representing the model name, such as "res.partner" or
        "product.template"
        """
        for record in self:
            if odoo_model and record.registration_ids:
                odoo_model_create_dict = {}
                for registration in record.registration_ids:
                    if registration.variable and registration.raw_value and registration.related_type:
                        # gestione delle date
                        if registration.related_type in ('date', 'datetime'):
                            raw_value = record.raw_value[:19]
                        else:
                            raw_value = record.raw_value
                        odoo_model_create_dict[registration.variable] = raw_value
                if odoo_model_create_dict:
                    self.env[odoo_model].create(odoo_model_create_dict)

    # dato un modello e un id di quel modello aggiorna un record utilizzando le variabili delle registrazioni
    def write_model_record_from_registrations_variable(self, odoo_model, odoo_id):
        """
        The function writes model records based on registrations variable, Odoo model, and Odoo ID.

        :param odoo_model: The `odoo_model` parameter is the name of the Odoo model that you want to
        write the record to. It should be a string representing the model name, such as "res.partner" or
        "sale.order"
        :param odoo_id: The `odoo_id` parameter is the ID of the record in the Odoo model that you want
        to update
        """
        for record in self:
            if odoo_model and record.registration_ids and odoo_id:
                odoo_model_write_dict = {}
                for registration in record.registration_ids:
                    if registration.variable and registration.raw_value and registration.related_type:
                        # gestione delle date
                        if registration.related_type in ('date', 'datetime'):
                            raw_value = record.raw_value[:19]
                        else:
                            raw_value = record.raw_value
                        odoo_model_write_dict[registration.variable] = raw_value
                if odoo_model_write_dict:
                    self.env[odoo_model].browse(
                        odoo_id).write(odoo_model_write_dict)


class ChecklistLine(models.Model):
    _inherit = "checklist.line"

    variable = fields.Char(
        string="Variable"
    )

    """
    This function checks if a variable is unique within a checklist and raises an error if it is not.
    """
    @api.constrains("variable")
    def check_unique_variable_for_line(self):
        for record in self:
            if record.variable and record.checklist_id:
                if self.search([("checklist_id", "=", record.checklist_id.id), ("id", "!=", record.id), ("variable", "=", record.variable)]):
                    raise UserError("There is another line in the checklist %s with the variable '%s' and this violates the uniqueness of the field" % (
                        record.checklist_id.name, record.variable))


class ChecklistRegistration(models.Model):
    _inherit = "checklist.registration"

    variable = fields.Char(
        string="Variable",
        related="checklist_line_id.variable",
        store=True
    )
