from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EmployeeGroupEmailWizard(models.TransientModel):
    _name = 'hr.employee.group.email.wizard'
    _description = 'Send Custom Email to Employee Group'

    group_id = fields.Many2one('hr.employee.groups', required=True, readonly=True)
    employee_ids = fields.Many2many(
        'hr.employee', string="To", readonly=True,)
    subject = fields.Char(string="Subject", required=True)
    body = fields.Html(string="Body", required=True)


    def action_send_email(self):
        self.ensure_one()
        employees = self.employee_ids.filtered(lambda e: e.work_email)
        if not employees:
            raise UserError(_("No recipients with valid work emails."))

        for employee in employees:
            self.env['mail.mail'].create({
                'email_from': self.env.user.email_formatted,
                'email_to': employee.work_email,
                'subject': self.subject,
                'body_html': self.body,
                'auto_delete': True,
            }).send()

        return {
    'type': 'ir.actions.client',
    'tag': 'display_notification',
        'params': {
            'title': _('Success!'),
            'message': _('Emails were sent to employees.'),
            'type': 'success',  
            'sticky': False,
        }
}
