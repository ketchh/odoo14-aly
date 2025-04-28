from decimal import Decimal
from odoo import api, models
from odoo.tools import format_datetime, format_date
import locale
class GenericChecklistReportAutomotive(models.AbstractModel):
    _inherit = 'report.netcheck_2.report_checklist'

    def _get_report_values(self, docids, data=None):
        # get the report action back as we will need its data
        report = self.env['ir.actions.report']._get_report_from_name('netcheck_2.report_checklist')
        # get the records selected for this rendering of the report
        obj = self.env[report.model].browse(docids)
        results = super(GenericChecklistReportAutomotive, self)._get_report_values(docids,data=data)
        for o in obj:
            section = 0
            for line in o.line_ids:
                if line.type == 'section':
                    section = line.name
                if line.type == 'damage':
                    for ll in results['attributes'][o.id][section]:
                        if ll['name'] == line.name:
                            # qua va la roba dei danni
                            ll['value'] = '<img src="%s"' % (line.registration_id.raw_value) + ' style="max-width:100% !important"/>' 
                            
                            damages = self.env['checklist.damage'].sudo().search([('registration_id','=',line.registration_id.id)])
                            for damage in damages:
                                ll['value'] += '<br/><smal>%s-%s</small><br/>' % (damage.type, damage.note)
                                for image in damage.images:
                                    ll['value'] += '<img src="%s"' % (image.raw_value) + ' style="max-width:50% !important"/>' 
                                    
        return results
        