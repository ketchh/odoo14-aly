# Copyright 2025
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "HR Attendance Geolocation Map",
    "summary": """
        Adds a map button to show check-in/check-out locations with differentiated colors""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Your Company",
    "website": "https://github.com/yourusername/hr-attendance-geolocation-map",
    "depends": ["hr_attendance_geolocation"],
    "data": [
        "views/hr_attendance_views.xml",
        "views/assets.xml",
        "views/templates.xml",
    ],
    "installable": True,
    "auto_install": False,
}
