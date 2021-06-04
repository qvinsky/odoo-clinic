from odoo import api, fields, models, _
from odoo.exceptions import Warning
import unicodedata

class ClinicRegister(models.Model):
    _name = "clinic.register"
    _description = "Register"
    _order = "name desc"

    name = fields.Char(string='Register', default='/')
    state = fields.Selection([
        ('draft','Draft'),
        ('confirm','Confirmed'),
        ('cancel','Cancelled')
    ], string='State', default='draft')
    patient_id = fields.Many2one('res.partner', change_default=True, string='Patient', domain=[('patient', '!=','/')], store=True)
    poly_id = fields.Many2one('clinic.poly', string='Poly Destination')
    date = fields.Datetime(string='Date', default=lambda self: fields.datetime.now()) #using lambda
    note = fields.Text(string='Note')

    # @api.onchange('patient_id')
    # def onchange_patient(self):
        
    # @api.model
    # def default_get(self, fields):
    #     result = super(Form, self).default_get(fields)
    #     # XXX Override (ORM) default value 0 (zero) for Integer field.
    #     result['res_id'] = False
    #     return result


    @api.model
    def create(self,vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('clinic.register.sequence') #search for DFT and %(y)s , 5
        return super(ClinicRegister, self).create(vals)

    @api.multi
    def name_get(self):
        result = []
        for me_id in self :
            result.append((me_id.id, "%s - %s" % (me_id.name, me_id.patient_id.name)))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args= args or []
        if name :
            recs = self.search([
                '|',
                ('patient_id.name', operator, name),
                ('name', operator, name),
            ] + args, limit=limit)
        else :
            recs = self.search([] + args, limit=limit)
        return recs.name_get()

    @api.multi
    def action_confirm(self):
        clinic_checkup = self.env['clinic.checkup']
        for me_id in self:
            if me_id.state == 'draft' and me_id.patient_id and me_id.poly_id:  #remove .exists()
                clinic_checkup.create({'register_id':me_id.id})
                me_id.write({'state':'confirm'})

    # @api.multi
    # def create_patient(self):
    #     self.env['res.partner'].create({'patient_id'})

    @api.multi
    def create_patient(self):
        view_id = self.env.ref('v11_sample_kevin.clinic_patient_form_view')
        return {
            'name' : 'Create Patient',
            'type' : 'ir.actions.act_window',
            'view_type' : 'form',
            'view_mode' : 'form',
            'res_model' : 'res.partner',
            'domain'    : [('patient','=',True)],
            'context'   : {'default_patient':True},
            'views': [(view_id.id, 'form')],
            'view_id' :view_id.id,
            'target':'new',
        }

    # def action_assign_to_me(self):
    #     self.write({'user_id': self.env.user.id})
        

    @api.multi
    def action_cancel(self):
        for me_id in self:
            checkup_ids = self.env['clinic.checkup'].search([
                ('register_id', '=', me_id.id),
                ('state','!=','cancel')
            ])
            if checkup_ids :
                checkup_names = [unicodedata.normalize('NFKD', checkup.name).encode('ascii','ignore') for checkup in checkup_ids]
                raise Warning("Please cancel %s checkup first!"%checkup_names)
            me_id.write({'state':'cancel'})

    @api.multi
    def unlink(self):
        for me_id in self:
            if me_id.state != 'draft':
                raise Warning("Cannot delete data")
        return super(ClinicRegister, self).unlink()