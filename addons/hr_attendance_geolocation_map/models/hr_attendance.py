# Copyright 2025
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, _


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    def action_show_attendance_map(self):
        """Action to show attendance locations on a map"""
        # Prepare data for the map
        locations = []
        
        # Check-in location (red marker)
        if self.check_in_latitude and self.check_in_longitude:
            locations.append({
                'latitude': self.check_in_latitude,
                'longitude': self.check_in_longitude,
                'type': 'check_in',
                'color': 'red',
                'title': _('Check-in'),
                'time': self.check_in.strftime('%d/%m/%Y %H:%M:%S') if self.check_in else '',
                'employee': self.employee_id.name,
            })
        
        # Check-out location (blue marker)
        if self.check_out_latitude and self.check_out_longitude:
            locations.append({
                'latitude': self.check_out_latitude,
                'longitude': self.check_out_longitude,
                'type': 'check_out',
                'color': 'blue',
                'title': _('Check-out'),
                'time': self.check_out.strftime('%d/%m/%Y %H:%M:%S') if self.check_out else '',
                'employee': self.employee_id.name,
            })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'hr_attendance_map',
            'name': _('Attendance Locations'),
            'params': {
                'locations': locations,
                'attendance_id': self.id,
            }
        }
