# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    days_before_reminder = fields.Integer("Number of days before to send the summary email to the agreed parties",
                                          config_parameter="bloomup_ars_reminders.days_before_reminder")


class FleetMoveInher(models.Model):
    _inherit = 'fleet.move.status'
    is_agreed = fields.Boolean(string='Agreed', tracking=True)


class FleetMoveInher(models.Model):
    _inherit = 'fleet.move'

    reminder_sent = fields.Boolean(string='Reminder sent', tracking=True)

    # metodo che invia una mail  x giorni prima della data di concordato
    def _send48reminder(self):

        def date_by_adding_business_days(from_date, add_days):
            business_days_to_add = add_days
            current_date = from_date
            while business_days_to_add > 0:
                current_date += datetime.timedelta(days=1)
                weekday = current_date.weekday()
                if weekday >= 5:  # sunday = 6
                    continue
                business_days_to_add -= 1
            return current_date
        days_before_reminder = int(self.env["ir.config_parameter"].sudo().get_param(
            'bloomup_ars_reminders.days_before_reminder'))

        def ulify(elements):
            string = "<ul>\n"
            string += "\n".join(["<li>" + str(s) + "</li>" for s in elements])
            string += "\n</ul>"
            return string

        if days_before_reminder != 0:
            day_report = date_by_adding_business_days(
                datetime.date.today(), days_before_reminder)
            records = self.env['fleet.move'].search(
                [('state.is_agreed', '=', True), ('reminder_sent', '=', False), ('confirmed_date', '!=', False)])
            recipients = {}
            move_ids = {}
            records_tosend = records.filtered(
                lambda x: x.confirmed_date.date() == day_report)
            for record in records_tosend:
                if record.pickup_address and record.pickup_address.email and record.vehicle_id:
                    if record.pickup_address.email not in recipients:
                        recipients[record.pickup_address.email] = [
                            'TARGA: %s - NUM TELAIO: %s - MODELLO: %s - TIPO: %s - INDIRIZZO: %s-%s%s' % 
                            (
                                record.vehicle_id.license_plate,
                                record.vehicle_id.vin_sn,
                                record.vehicle_id.model_id.name,
                                record.vehicle_id.fuel_type,
                                record.pickup_address.name,
                                record.pickup_address.street,
                                record.pickup_address.city
                            )
                        ]
                        move_ids[record.pickup_address.email] = [record]
                    else:
                        recipients[record.pickup_address.email].append(
                            'TARGA: %s - NUM TELAIO: %s - MODELLO: %s - TIPO: %s - INDIRIZZO: %s-%s%s' % 
                            (
                                record.vehicle_id.license_plate,
                                record.vehicle_id.vin_sn,
                                record.vehicle_id.model_id.name,
                                record.vehicle_id.fuel_type,
                                record.pickup_address.name,
                                record.pickup_address.street,
                                record.pickup_address.city
                            )
                        )
                        move_ids[record.pickup_address.email].append(record)
           

            for recipient in recipients.keys():
                vehicles = ulify(recipients[recipient])
                body = "Gentile, <br/> di seguito la lista dei veicoli concordati per la data {}: <br/> {} <br/> Si prega di prestare la massima attenzione alla pulizia degli interni ed esterni ad alla preparazione della vettura per la consegna. <br/> Inoltre preghiamo di prestare la massima attenzione alle ricarica delle vetture elettriche.Vi preghiamo di comunicarci qualora il veicolo non risulti presente sui vs piazzali.<br/> ARS SERVICE SRL <br/> NOTA BENE! NON RISPONDERE A QUESTA MAIL, ma per segnalazioni scrivere a rit_dea.arval@ars-altmann.it".format(
                    day_report.strftime("%d/%m/%Y"), vehicles)
                post_vars = {
                    'subject': ("Notifica vetture per il {} - ARS SERVICE SRL").format(
                        day_report.strftime("%d/%m/%Y")),
                    'body_html': body,
                    'email_to': recipient,
                    'email_from': 'concordati@arsservice.it',
                    'email_cc':'concordati.arval@ars-altmann.it',
                    # 'email_cc': cc_list,

                }
                mail_obj = self.env['mail.mail']
                msg_id = mail_obj.create(post_vars)
                for element in move_ids[recipient]:
                    element.reminder_sent = True

            return True
