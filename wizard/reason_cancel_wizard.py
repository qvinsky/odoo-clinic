from odoo import fields, api, models

class ClinicReasonCancelWizard(models.TransientModel):
    _name = "clinic.reason.cancel.wizard"
    _description = "Reason Cancel"

    name = fields.Text(string="Reason", required=True)

    @api.one
    def action_cancel(self):
        active_ids = self._context.get('active_ids')
        if not active_ids :
            return False
        checkup_id = self.env['clinic.checkup'].browse(active_ids[:1])
        checkup_id.register_id.note = self.name
        checkup_id.state = 'cancel'