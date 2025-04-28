from odoo import fields, http, SUPERUSER_ID, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression
import base64

class ChecklistCSVExport(http.Controller):
    @http.route('/web/export/csv_export', type='http', auth="user")
    def download_csv(self, model, data, filename, **kw):
        csv_data = base64.b64decode(data)
        
        # Imposta gli header per il download
        headers = [
            ('Content-Type', 'text/csv'),
            ('Content-Disposition', f'attachment; filename="{filename}"'),
            ('charset', 'utf-8'),
        ]
        
        # Restituisci la risposta HTTP
        return http.request.make_response(csv_data, headers=headers)

class CustomerPortal(CustomerPortal):
    @http.route(['/my/checklist/<int:checklist_id>'], type='http', auth="public", website=True)
    def checklist_page(self, checklist_id, access_token=None, **kw):
        values = {'access_error': False}
        try:
            checklist_sudo = self._document_check_access('checklist.checklist', checklist_id, access_token=access_token)
            if checklist_sudo.state != 'done':
                raise AccessError('')
            else:
                values['datas'] = checklist_sudo._get_public_data()
                values['name'] = checklist_sudo.display_name
        except (AccessError, MissingError):
            raise AccessError('')
        return request.render('netcheck_2.my_checklist', values)
    
