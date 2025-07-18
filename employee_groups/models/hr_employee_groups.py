from odoo import models, fields, Command, _
from odoo.exceptions import UserError


class HREmployeeGroups(models.Model):
    _name = 'hr.employee.groups'
    _description = 'Employee Groups'
    _inherit = ['mail.thread']

    name = fields.Char(string='Group Name', required=True)
    description = fields.Text(string='Description')
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    template_id = fields.Many2one('sign.template', string="Template")
    document_id = fields.Many2many(
        'documents.document',
        string='Documents',
        help='Select documents related to this group'
    )
    
    def action_open_share_dialog(self):
        """Open document sharing dialog"""
        self.ensure_one()
        if not self.document_id:
            raise UserError(_("Please select documents to share."))
        partner_ids = []
        valid_employees = []
        invalid_employees = []
        # Categorize employees by user and partner availability
        for emp in self.employee_ids:
            if emp.user_id and emp.user_id.partner_id:
                partner_ids.append(emp.user_id.partner_id.id)
                valid_employees.append(emp.name)
            else:
                invalid_employees.append(emp.name)
        return {
            'type': 'ir.actions.client',
            'tag': 'open_documents_share_dialog',
            'params': {
                'document_ids': self.document_id.ids,
                'partner_ids': partner_ids,
                'is_single_document': len(self.document_id.ids) == 1,
                'valid_employees': valid_employees,
                'invalid_employees': invalid_employees,
            }
        }
    
    def action_send_sign_request(self):
        self.ensure_one()
        if not self.template_id:
            raise UserError(_("Please set a signature template for this group."))
        
        employees = self.employee_ids.filtered(lambda e: e.user_id.partner_id)
        if not employees:
            raise UserError(_("No employees with a work contact (partner) found in this group."))

        roles = self.template_id.sign_item_ids.mapped('responsible_id').filtered(lambda r: r)
        roles = roles or [self.env.ref('sign.sign_item_role_default')]
        multiple_roles = len(roles) > 1

        for employee in employees:
            request_items = [
                Command.create({
                    'partner_id': employee.user_id.partner_id.id,
                    'role_id': role.id,
                    'mail_sent_order': 1,
                }) for role in (roles if multiple_roles else [roles[0]])
            ]
            self.env['sign.request'].with_context(skip_role_validation=True).create({
                'template_id': self.template_id.id,
                'request_item_ids': request_items,
                'reference': self.template_id.name or self.template_id.attachment_id.name,
                'subject': _('Signature     Request - %s', self.template_id.attachment_id.name or ''),
            })
            employee.message_post(
            body=_("A signature request has been sent using template %s.") % self.template_id.name,
            message_type="notification",
            subtype_xmlid="mail.mt_note"
        )

        employee_names = ", ".join(employee.name for employee in employees)
        message = _("Signature requests have been sent to the following employees: %s") % employee_names

        self.message_post(
            body=message,
            message_type="notification",
            subtype_xmlid="mail.mt_note",
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Signature Requests Sent'),
                'message': _('Signature requests have been sent to the selected employees.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_open_custom_email_wizard(self):
        self.ensure_one()
        if not self.employee_ids:
            raise UserError(_("Please select employees to send the email."))
        partner_ids = self.employee_ids.mapped('user_id.partner_id').filtered(lambda p: p).ids
        if not partner_ids:
            raise UserError(_("No related partners found through user_id for the employees in this group."))

        # Load your default template
        template = self.env.ref('employee_groups.mail_template_employee_group', raise_if_not_found=False)

        ctx = {
            'default_model': 'hr.employee.groups',
            'default_res_ids': [self.id],
            'default_partner_ids': partner_ids,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': 'mail.mail_notification_light',
            'email_notification': True,
            'force_email': True,
        }

        if template:
            ctx['default_template_id'] = template.id

        return {
            'name': _('Send Email to Employees'),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }
