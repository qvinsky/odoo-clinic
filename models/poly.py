from odoo import fields, api, models

class ClinicPoly(models.Model):
    _name = "clinic.poly"
    _description = "Poly"

    name = fields.Char ("Poly", requiered=True)
    code = fields.Char ("Poly's Code", required=True)
    
    # _sql_constraints = [
    #     ('unique_code', 'unique(code)', 'Poly Code duplicated!')
    # ]

    def _check_name(self):
        for val in self.read(['name']):
            if val['name']:
                if len(val['name']) < 4:
                    return False
        return True

    _constraints = [
        (_check_name, 'Name must have at least 4 characters.', ['name'])
    ]  #update this constraint

    @api.model
    def create(self, vals):
        if vals.get('name', False):
            vals['code'] = self.env['ir.sequence'].next_by_code('clinic.poly.sequence')
        return super(ClinicPoly, self).create(vals)

    @api.multi
    def name_get(self):
        result = []
        for me in self :
            result.append((me.id, "%s - %s" % (me.code, me.name)))
        return result
    
    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name :
            recs = self.search([
                '|',
                ('code', operator, name),
                ('name', operator, name),
            ] + args, limit=limit)
        else :
            recs = self.search([] + args, limit=limit)
        return recs.name_get() 