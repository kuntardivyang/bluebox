from odoo import models, fields, Command, _
from odoo.exceptions import UserError


class HREmployeeGroups(models.Model):
    _name = 'hr.employee.groups'
    _description = 'Employee Groups'
    _inherit = ['mail.thread']

    name = fields.Char(string='Group Name', required=True)
    description = fields.Text(string='Description')
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    template_id = fields.Many2one('sign.template', string="Template", required=True)
    document_id = fields.Many2many(
        'ir.attachment',
        string='Documents',
        domain="[('mimetype', 'in', ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'])]",
        help='Select documents related to this group'
    )
  
    
    def action_share_documents_direct(self):
        self.ensure_one()
        Document = self.env['documents.document']
        for attachment in self.document_id:
            # Find or create the corresponding documents.document record
            document = Document.search([('attachment_id', '=', attachment.id)], limit=1)
            if not document:
                # Create a document if it doesn't exist
                document = Document.create({
                    'attachment_id': attachment.id,
                    'name': attachment.name,
                    'owner_id': self.env.user.id,
                })

            partners = {}
            for employee in self.employee_ids:
                partner = employee.user_id.partner_id if employee.user_id else False
                if not partner:
                    continue
                # Grant access as 'view'
                access = self.env['documents.access'].search([
                    ('document_id', '=', document.id),
                    ('partner_id', '=', partner.id)
                ], limit=1)
                if not access:
                    self.env['documents.access'].create({
                        'document_id': document.id,
                        'partner_id': partner.id,
                        'role': 'view',
                    })
                partners[partner] = 'view'
            # Send the share email
            # if partners:
            #     document._send_access_by_mail(partners)
    
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
        partner_ids = self.employee_ids.mapped('user_id.partner_id').filtered(lambda p: p).ids
        if not partner_ids:
            raise UserError(_("No related partners found through user_id for the employees in this group."))

        ctx = {
            'default_model': 'hr.employee.groups',
            'default_res_ids': [self.id],
            'default_partner_ids': partner_ids,
            'default_composition_mode': 'comment',
            'default_email_layout_xmlid': 'mail.mail_notification_light',
            'email_notification': True,
            'force_email': True,
        }
        return {
            'name': _('Send Email to Employees'),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }