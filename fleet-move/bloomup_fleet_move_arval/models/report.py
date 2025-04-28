from odoo import api, models
from odoo.tools import format_datetime, format_date
import locale

class ARvalReport(models.AbstractModel):
    _name = 'report.bloomup_fleet_move_arval.report_arval_checklist'

    def _get_report_values(self, docids, data=None):
        # get the report action back as we will need its data
        report = self.env['ir.actions.report']._get_report_from_name('bloomup_fleet_move_arval.report_arval_checklist')
        # get the records selected for this rendering of the report
        obj = self.env[report.model].browse(docids)
        user = self.env['res.users'].sudo().browse([self.env.context.get('uid')])
        tz = 'UTC'
        if user:
            tz = user.tz
        lang = self.env['res.lang'].sudo().search([('code','=',self.env.context.get('lang'))])
        
        if lang:
            locale._override_localeconv["thousands_sep"] = lang.thousands_sep
            locale._override_localeconv["decimal_point"] = lang.decimal_point
            
        attrs = {}
        readonly = self.env.ref('netcheck_2.option_readonly').id
        for o in obj:
            attrs[o.id] = {0:{'name': False, 'lines': []},'other_lines': {}}
            section = 0
            for line in o.line_ids.sorted(key='position'):
                hidden = False
                if line.type == 'section':
                    if not line.report_block:
                        section = 0
                    else:
                        if line.report_block not in attrs[o.id].keys():
                            attrs[o.id][line.report_block] = {'name': line.name, 'lines': []}
                            section = line.report_block
                else:
                    for option in line.option_ids:
                        if option.code == 'option_report_hidden':
                            hidden = True
                    datas = {'name':'- '+ line.name +':', 'value':'', 'type':line.type}
                    if line.type in ['string'] and line.registration_id:
                        datas['value'] = line.registration_id.raw_value
                    if line.type in ['integer','float'] and line.registration_id:
                        datas['value'] = locale.atof(line.registration_id.raw_value)
                    if line.type in ['datetime'] and line.registration_id:
                        datas['value'] = format_datetime(self.env, line.registration_id.raw_value.split('.')[0],tz='UTC')
                    if line.type in ['date'] and line.registration_id:
                        datas['value'] = format_date(self.env, line.registration_id.raw_value.split('.')[0])
                    if line.type in ['precompiled']:
                        datas['value'] = line.option_precompiled_test
                    if line.type in ['boolean'] and line.registration_id:
                        if line.registration_id.raw_value == 'true':
                            datas['value'] = '<span>SI</span>'
                        else:
                            datas['value'] = '<span>NO</span>'
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
                    if line.type == 'damage' and line.registration_id:
                        datas['name'] = ''
                        html ="""<img class="image w-100 mt-2 border-top 
                        pt-2 pb-2 border-dark" src="%s"/>""" % \
                        (line.registration_id.raw_value)
                        if line.number_of_damages > 0:
                            damages_ = self.env['checklist.damage'].sudo().search([
                                ('registration_id','=',line.registration_id.id)
                            ])
                            damages = ""
                            for im in damages_:
                                damages += im.type +'<br/>'
                            html += """
                            <div class="border-bottom border-dark ">
                            %s
                            </div>
                            """ % damages
                        else:
                            html += """
                            <div class="border-bottom border-dark ">
                            Nessuna anomalia riscontrata
                            </div>
                            """
                        datas['value'] = html
                    if not hidden and not line.report_block:
                        attrs[o.id][section]['lines'].append(datas)
                    if not hidden and line.report_block:
                        attrs[o.id]['other_lines'][line.report_block] = {'name':line.name, 'datas':datas}
        # return a custom rendering context
        return {
            'docs': obj,
            'attributes': attrs
        }
    
class SRReport(models.AbstractModel):
    _name = 'report.bloomup_fleet_move_arval.report_sr_checklist'

    def _get_report_values(self, docids, data=None):
        # get the report action back as we will need its data
        report = self.env['ir.actions.report']._get_report_from_name('bloomup_fleet_move_arval.report_sr_checklist')
        # get the records selected for this rendering of the report
        obj = self.env[report.model].browse(docids)
        lang = self.env['res.lang'].sudo().search([('code','=',self.env.context.get('lang'))])
        user = self.env['res.users'].sudo().browse([self.env.context.get('uid')])
        tz = 'UTC'
        if user:
            tz = user.tz
        if lang:
            locale._override_localeconv["thousands_sep"] = lang.thousands_sep
            locale._override_localeconv["decimal_point"] = lang.decimal_point
            
        attrs = {}
        readonly = self.env.ref('netcheck_2.option_readonly').id
        for o in obj:
            attrs[o.id] = {0:{'name': False, 'lines': []},'other_lines': {}}
            section = 0
            for line in o.line_ids.sorted(key='position'):
                hidden = False
                if line.type == 'section':
                    if not line.report_block:
                        section = 0
                    else:
                        if line.report_block not in attrs[o.id].keys():
                            attrs[o.id][line.report_block] = {'name': line.name, 'lines': []}
                            section = line.report_block
                else:
                    for option in line.option_ids:
                        if option.code == 'option_report_hidden':
                            hidden = True
                    datas = {'name':'- '+ line.name +':', 'value':'', 'type':line.type}
                    if line.type in ['string'] and line.registration_id:
                        datas['value'] = line.registration_id.raw_value
                    if line.type in ['integer','float'] and line.registration_id:
                        datas['value'] = locale.atof(line.registration_id.raw_value)
                    if line.type in ['datetime'] and line.registration_id:
                        datas['value'] = format_datetime(self.env, line.registration_id.raw_value.split('.')[0],tz=tz)
                    if line.type in ['date'] and line.registration_id:
                        datas['value'] = format_date(self.env, line.registration_id.raw_value.split('.')[0])
                    if line.type in ['precompiled']:
                        datas['value'] = line.option_precompiled_test
                    if line.type in ['boolean'] and line.registration_id:
                        if line.registration_id.raw_value == 'true':
                            datas['value'] = '<span>SI</span>'
                        else:
                            datas['value'] = '<span>NO</span>'
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
                    if line.type == 'damage' and line.registration_id:
                        datas['name'] = ''
                        html ="""<img class="image w-100 mt-2 border-top 
                        pt-2 pb-2 border-dark" src="%s"/>""" % \
                        (line.registration_id.raw_value)
                        if line.number_of_damages > 0:
                            damages_ = self.env['checklist.damage'].sudo().search([
                                ('registration_id','=',line.registration_id.id)
                            ])
                            damages = ""
                            for im in damages_:
                                damages += im.type +'<br/>'
                            html += """
                            <div class="border-bottom border-dark ">
                            %s
                            </div>
                            """ % damages
                        else:
                            html += """
                            <div class="border-bottom border-dark ">
                            Nessuna anomalia riscontrata
                            </div>
                            """
                        datas['value'] = html
                    if not hidden and not line.report_block:
                        attrs[o.id][section]['lines'].append(datas)
                    if not hidden and line.report_block:
                        attrs[o.id]['other_lines'][line.report_block] = {'name':line.name, 'datas':datas}
        # return a custom rendering context
        return {
            'docs': obj,
            'attributes': attrs
        }
