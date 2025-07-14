from odoo import models, fields

class HREmployeeGroups(models.Model):
    _name = 'hr.employee.groups'
    _description = 'Employee Groups'

    name = fields.Char(string='Group Name', required=True)
    description = fields.Text(string='Description')
    employee_ids = fields.Many2many('hr.employee', string='Employees')