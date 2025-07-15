from odoo import models, fields

class HREmployeeGroups(models.Model):
    _name = 'hr.employee.groups'
    _description = 'Employee Groups'

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
    