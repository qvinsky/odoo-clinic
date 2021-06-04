from odoo import api, fields, models

class res_partner(models.Model):
    _inherit = "res.partner"

    patient = fields.Char(string='Patient', default='/')
    name = fields.Char(string='Name')
    job = fields.Char(string='Job')
    gender = fields.Selection([
        ('male','Male'),
        ('female','Female')
        ], string='Gender')
    birth_date = fields.Date('Birth Date')
    blood_type = fields.Selection([
        ('a','A'),
        ('b','B'),
        ('ab','AB'),
        ('o','O'),
    ], string='Blood Type')
    status = fields.Selection([
        ('single','Single'),
        ('married','Married'),
        ('divorce','Divorce'),
    ], string='Status')
    patient_history = fields.One2many('clinic.checkup', 'patient_id', 'Patient History')

    _sql_constraints = [
        ('unique_patient', 'unique(patient,name)', 'Combination of code and name has been recorded, please check again!'),
    ] #check again

    @api.model
    def create(self, vals):
        vals['patient'] = self.env['ir.sequence'].next_by_code('clinic.patient.sequence')
        return super(res_partner, self).create(vals)

    @api.multi
    def name_get(self):
        result = []
        for me_id in self:
            result.append((me_id.id, "%s - %s" % (me_id.patient, me_id.name)))
        return result
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            recs = self.search([
                '|',
                ('patient', operator, name),
                ('name', operator, name),
            ] + args, limit=limit)
        else :
            recs = self.search([] + args, limit=limit)
        return recs.name_get()

class res_partner_doctor(models.Model):
    _name = "res.partner.doctor"

    doctor = fields.Char(string='Doctor', default='/')
    name = fields.Char(string='Name')
    comment = fields.Text(string='Comment')
    doctor_history = fields.One2many('clinic.checkup', 'doctor_id', 'Doctor History')

    _sql_constraints = [
        ('unique_doctor', 'unique(doctor,name)', 'Combination of code and name has been recorded, please check again!'),
    ] #check again

    @api.model
    def create(self, vals):
        vals['doctor'] = self.env['ir.sequence'].next_by_code('clinic.doctor.sequence')
        return super(res_partner_doctor, self).create(vals)

    @api.multi
    def name_get(self):
        result = []
        for me_id in self:
            result.append((me_id.id, "%s - %s" % (me_id.doctor, me_id.name)))
        return result
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            recs = self.search([
                '|',
                ('doctor', operator, name),
                ('name', operator, name),
            ] + args, limit=limit)
        else :
            recs = self.search([] + args, limit=limit)
        return recs.name_get()