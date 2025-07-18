from odoo import models, fields, Command, _
from odoo.exceptions import UserError


class HREmployeeGroups(models.Model):
    _name = 'hr.employee.groups'
    _description = 'Employee Groups'

    name = fields.Char(string='Group Name', required=True)
    description = fields.Text(string='Description')
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    template_id = fields.Many2one('sign.template', string="Template", required=True)
    document_id = fields.Many2many(
        'documents.document',
        string='Documents',
        help='Select documents related to this group'
    )

    def action_open_share_dialog(self):
        self.ensure_one()

        partner_ids = []
        portal_employees = []
        non_portal_employees = []
        
        # Categorize employees by portal access
        for emp in self.employee_ids:
            if emp.user_id and emp.user_id.partner_id:
                partner = emp.user_id.partner_id
                
                # Check if partner has portal access
                if partner.user_ids and any(user.has_group('base.group_portal') for user in partner.user_ids):
                    partner_ids.append(partner.id)
                    portal_employees.append(emp.name)
                else:
                    non_portal_employees.append(emp.name)
            else:
                non_portal_employees.append(emp.name)

        return {
            'type': 'ir.actions.client',
            'tag': 'open_documents_share_dialog',
            'params': {
                'document_ids': self.document_id.ids,
                'partner_ids': partner_ids,
                'is_single_document': len(self.document_id.ids) == 1,
                'portal_employees': portal_employees,
                'non_portal_employees': non_portal_employees,
            }
        }


    def action_send_signature(self):
        self.ensure_one()
    
        # Create sign request for each employee
        for emp in self.employee_ids:
            if not emp.work_email:
                continue
            
            partner = self.env['res.partner'].search([('email', '=', emp.work_email)], limit=1)
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': emp.name,
                    'email': emp.work_email,
                })
    
            sign_request = self.env['sign.request'].create({
                'template_id': self.template_id.id,
                'request_item_ids': [(0, 0, {
                    'partner_id': partner.id,
                    'role_id': self.template_id.sign_item_ids[0].role_id.id,
                })],
            })
    
            sign_request._send_signature_request()
    
    
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
        employees = self.employee_ids.filtered(lambda e: e.work_contact_id)
        if not employees:
            raise UserError(_("No employees with a work contact (partner) found in this group."))
        roles = self.template_id.sign_item_ids.mapped('responsible_id').filtered(lambda r: r)
        if not roles or len(roles) == 1:
            if not roles:
                role = self.env.ref('sign.sign_item_role_default')
            else:
                role = roles[0]
            request_items = [
                Command.create({
                    'partner_id': employee.work_contact_id.id,
                    'role_id': role.id,
                    'mail_sent_order': 1,
                })
                for employee in employees
            ]
            self.env['sign.request'].with_context(skip_role_validation=True).create({
                'template_id': self.template_id.id,
                'request_item_ids': request_items,
                'reference': self.template_id.name or self.template_id.attachment_id.name,
                'subject': _('Signature Request - %s', self.template_id.attachment_id.name or ''),
            })
        else:
            for employee in employees:
                request_items = [
                    Command.create({
                        'partner_id': employee.work_contact_id.id,
                        'role_id': role.id,
                        'mail_sent_order': 1,
                    })
                    for role in roles
                ]
                self.env['sign.request'].with_context(skip_role_validation=True).create({
                    'template_id': self.template_id.id,
                    'request_item_ids': request_items,
                    'reference': self.template_id.name or self.template_id.attachment_id.name,
                    'subject': _('Signature Request - %s', self.template_id.attachment_id.name or ''),
                })
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
    
class SignRequest(models.Model):
    _inherit = "sign.request"

    def _check_signers_roles_validity(self):
        if self.env.context.get('skip_role_validation'):
            return True
        return super()._check_signers_roles_validity()