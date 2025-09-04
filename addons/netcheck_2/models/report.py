from decimal import Decimal
from odoo import api, models
from odoo.tools import format_datetime, format_date
import locale

class GenericChecklistReport(models.AbstractModel):
    _name = 'report.netcheck_2.report_checklist'

    def _get_report_values(self, docids, data=None):
        # get the report action back as we will need its data
        report = self.env['ir.actions.report']._get_report_from_name('netcheck_2.report_checklist')
        # get the records selected for this rendering of the report
        obj = self.env[report.model].browse(docids)
        lang = self.env['res.lang'].sudo().search([('code','=',self.env.context.get('lang'))])
        if lang:
            locale._override_localeconv["thousands_sep"] = lang.thousands_sep
            locale._override_localeconv["decimal_point"] = lang.decimal_point
            
        attrs = {}
        for o in obj:
            attrs[o.id] = {0:[]}
            section = 0
            for line in o.line_ids.sorted(key='position'):
                hidden = False
                if line.type == 'section' and line.name not in attrs[o.id].keys():
                    attrs[o.id][line.name] = []
                    section = line.name
                else:
                    for option in line.option_ids:
                        if option.code == 'option_report_hidden':
                            hidden = True
                    datas = {'name':line.name, 'value':''}
                    if line.type in ['string'] and line.registration_id:
                        datas['value'] = line.registration_id.raw_value
                    if line.type in ['integer','float'] and line.registration_id:
                        datas['value'] = locale.atof(line.registration_id.raw_value)
                    if line.type in ['datetime'] and line.registration_id:
                        datas['value'] = format_datetime(self.env, line.registration_id.raw_value.split('.')[0])
                    if line.type in ['date'] and line.registration_id:
                        datas['value'] = format_date(self.env, line.registration_id.raw_value.split('.')[0])
                    if line.type in ['precompiled']:
                        datas['value'] = line.option_precompiled_test
                    if line.type in ['boolean'] and line.registration_id:
                        if line.registration_id.raw_value == 'true':
                            datas['value'] = '<i class="fa fa-check-square-o"></i>'
                        else:
                            datas['value'] = '<i class="fa fa-square-o"></i>'
                    if line.type in ['signature', 'photo']:
                        datas['value'] = '<img src="%s"' % (line.registration_id.raw_value) + ' style="max-width:100% !important"/>' 
                    if line.type in ['selection'] and line.registration_id:
                        response = line.registration_id.raw_value.split(',') 
                        val = []
                        
                        for i in response:
                            for ll in line.option_selection_string:
                                if ll.id == int(i):
                                    val.append(ll.name)
                            for option in line.option_ids:
                                if option.code == 'option_selection_model':
                                    val.append(self.env[line.name_model.model].sudo().browse(int(i)).display_name)
                        datas['value'] = ','.join(val)
                    if not hidden:
                        attrs[o.id][section].append(datas)
        # return a custom rendering context
        return {
            'docs': obj,
            'attributes': attrs
        }