from odoo import api, fields, models

class CancelFields(models.Model):
    _name = "cancel.fields"
    _description = "Cancelled"


    checkup_id = fields.Many2one('clinic.checkup', 'Checkup', track_visibility='onchange')
    register_id = fields.Many2one('clinic.register', 'Register', track_visibility='onchange')
    note = fields.Text(related='register_id.note', string="Note")