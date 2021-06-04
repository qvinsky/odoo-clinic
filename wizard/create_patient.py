from odoo import models, fields, api, _

class CreatePatient(models.TransientModel):
    _name ='create.patient'

    patient_id = fields.Many2one('clinic.patient', string="Patient")
