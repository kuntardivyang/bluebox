# Copyright 2018-22 ForgeFlow <http://www.forgeflow.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    "name": "Empire Groups",
    "version": "18.0.0.0.1",
    "author": "ForgeFlow, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "website": "https://rdflex.com",
    "depends": ["hr"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_employee_groups_views.xml",
        "views/menu.xml",
        # "wizard/sign_send_request_wizard_views.xml",
    ],
}