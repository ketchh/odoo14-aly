from odoo import models, fields, api, _

class ArvalIpat(models.Model):
    _inherit = "bloomup.ipat"
    
    def get_record_value(self, data=False, line=False):

        if line.model_id.model == 'fleet.vehicle':
            if line.field.name == 'optionals' or line.field.name == 'accessori':
                res = data[line.column_name]
                if isinstance(res, tuple) or isinstance(res, list):
                    data_text = data[line.column_name][0].split('|')
                else:
                    data_text = data[line.column_name].split('|')
                text = ''
                for d in data_text:
                    text += '- ' + d.strip() + '\n'
                return text
        return super(ArvalIpat, self).get_record_value(data=data,line=line)
            
            