from odoo import fields, models, api, Command,_
from odoo.exceptions import UserError


class SignSendRequest(models.TransientModel):
    _inherit = "sign.send.request"

    hr_employee_group_id = fields.Many2one(
        "hr.employee.groups",
        string="Employee Group",
        help="If set, the request will be sent to all employees in this group.",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get("employee_group_send"):
            res["hr_employee_group_id"] = self.env.context.get("active_id")
            res["has_default_template"] = False
        return res

    def send_request(self):
        self.ensure_one()

        if not self.hr_employee_group_id:
            return super().send_request()

        group = self.hr_employee_group_id
        if not group.employee_ids:
            raise UserError(_("The selected group has no employees."))
        template = self.template_id
        template._check_send_ready()
        roles = template.sign_item_ids.responsible_id.sorted()
        if not roles:
            raise UserError(_("No roles defined in the selected template."))

        signer_vals_list = []
        default_role = self.env.ref('sign.sign_item_role_default')
        email_field = 'work_email'

        mail_order = 1
        for employee in group.employee_ids:
            partner = employee.user_id.partner_id if employee.user_id else None
            email = getattr(employee, email_field, None)

            if not partner or not email:
                continue  # Skip if no partner/email

            signer_vals_list.append({
                'partner_id': partner.id,
                'role_id': roles[0].id if roles else default_role.id,
                'mail_sent_order': mail_order,
            })
            mail_order += 1

        if not signer_vals_list:
            raise UserError(_("No valid email addresses found in the group."))

        request = self.env['sign.request'].create({
            'template_id': template.id,
            'request_item_ids': [Command.create(vals) for vals in signer_vals_list],
            'reference': self.filename,
            'subject': self.subject,
            'message': self.message,
            'message_cc': self.message_cc,
            'attachment_ids': [Command.set(self.attachment_ids.ids)],
            'validity': self.validity,
            'reminder': self.reminder,
            'reminder_enabled': self.reminder_enabled,
            'reference_doc': self.reference_doc,
        })

        request.message_subscribe(partner_ids=self.cc_partner_ids.ids)

        if self.activity_id:
            self._activity_done()
            return {'type': 'ir.actions.act_window_close'}

        return request.go_to_document()