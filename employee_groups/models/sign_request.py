from odoo import models
    
class SignRequest(models.Model):
    _inherit = "sign.request"

    def _check_signers_roles_validity(self):
        if self.env.context.get('skip_role_validation'):
            return True
        return super()._check_signers_roles_validity()