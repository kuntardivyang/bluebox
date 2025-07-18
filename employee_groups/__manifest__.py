# Copyright 2018-22 ForgeFlow <http://www.forgeflow.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    "name": "Employee Groups",
    "version": "18.0.0.0.1",
    "author": "RdFlex",
    "license": "LGPL-3",
    "website": "https://rdflex.com",
    "depends": ["hr", "documents",'sign','mail'],
    "data": [
        "security/ir.model.access.csv",
        "data/mail_templates.xml",
        "views/hr_employee_groups_views.xml",
        "views/menu.xml",
    ],
    'assets': {
    'web.assets_backend': [
        'employee_groups/static/src/js/open_documents_share_dialog.js',
    ],
},
}