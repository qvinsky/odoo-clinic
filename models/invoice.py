from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
from odoo.addons import decimal_precision as dp
# from odoo.tools import amount_to_text
from odoo.tools import float_is_zero, float_compare

class AccountInvoice(models.Model):
    _name = "clinic.invoice"
    _description = "Invoice"
    _order = "number_invoice desc"

    @api.one
    @api.depends('invoice_line_ids.price_subtotal')
    def _compute_amount(self):
        self.amount_total_signed = self.amount_total
        self.amount_total = sum(line.price_subtotal for line in self.invoice_line_ids)

    @api.onchange('amount_total')
    def _onchange_amount_total(self):
        for inv in self:
            if float_compare(inv.amount_total, 0.0, precision_rounding=inv.currency_id.rounding) == -1:
                raise Warning(_('You cannot validate an invoice with a negative total amount. You should create a credit note instead.'))

    @api.onchange('amount_total')
    def _no_negatip(self):
        if self.amount_total < 0:
            raise Warning('negatip')

    user_id = fields.Many2one('res.users', string='Salesperson', track_visibility='onchange',
        readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env.user, copy=False)
    number_invoice = fields.Char(string="Number", readonly=True)
    state = fields.Selection([
            ('draft','Draft'),
            ('open', 'Open'),
            ('paid', 'Paid'),
            ('cancel', 'Cancelled'),
        ], string='Status', index=True, readonly=True, default='draft')
    sent = fields.Boolean(readonly=True, default=False)
    type = fields.Selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Vendor Bill'),
            ('out_refund','Customer Credit Note'),
            ('in_refund','Vendor Credit Note'),
        ], readonly=True, index=True, change_default=True,
        default=lambda self: self._context.get('type', 'out_invoice'),
        track_visibility='always')
    date_invoice = fields.Date(string='Invoice Date', readonly=True, states={'draft': [('readonly', False)]}, index=True, copy=False, default=lambda self: fields.datetime.now())
    date_due = fields.Date(string='Due Date', readonly=True, states={'draft': [('readonly', False)]}, index=True, copy=False, default=lambda self: fields.datetime.now())
    partner_id = fields.Many2one('res.partner', string='Patient', change_default=True,
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        track_visibility='always')
    invoice_line_ids = fields.One2many('account.invoice.line', 'invoice_id', string='Invoice Lines', oldname='invoice_line',
        readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_compute_amount')
    currency_id = fields.Many2one('res.currency', string='Currency')
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position', oldname='fiscal_position',
        readonly=True, states={'draft': [('readonly', False)]})

    _sql_constraints = [
        ('number_uniq', 'unique(number_invoice)', 'Invoice Number must be unique!'),
    ]

    # @api.multi
    # def amount_to_text(self, amount):
    #     return amount_to_text(amount)

    # @api.multi
    # def _get_printed_report_name(self):
    #     self.ensure_one()
    #     return  self.state == 'draft' and _('Draft Invoice') or \
    #             self.state in ('open','paid') and _('Invoice - %s') % (self.number_invoice)

    @api.model
    def create(self, vals):
        vals['number_invoice'] = self.env['ir.sequence'].next_by_code('clinic.invoice.sequence')
        return super(AccountInvoice, self).create(vals)

    @api.multi
    def action_invoice_open(self):
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state != 'draft'):
            raise UserError(_("Invoice must be in draft state in order to validate it."))
        if to_open_invoices.filtered(lambda inv: float_compare(inv.amount_total, 0.0, precision_rounding=inv.currency_id.rounding) == -1):
            raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead."))
        return to_open_invoices.invoice_validate()

    @api.multi
    def action_invoice_paid(self):
        to_pay_invoices = self.filtered(lambda inv: inv.state != 'paid')
        if to_pay_invoices.filtered(lambda inv: inv.state != 'open'):
            raise UserError(_('Invoice must be validated in order to set it to register payment.'))
        if to_pay_invoices.filtered(lambda inv: not inv.reconciled):
            raise UserError(_('You cannot pay an invoice which is partially paid. You need to reconcile payment entries first.'))
        return to_pay_invoices.write({'state': 'paid'})

    @api.multi
    def action_invoice_re_open(self):
        if self.filtered(lambda inv: inv.state != 'paid'):
            raise UserError(_('Invoice must be paid in order to set it to register payment.'))
        return self.write({'state': 'open'})

    @api.multi
    def action_invoice_cancel(self):
        if self.filtered(lambda inv: inv.state not in ['draft', 'open']):
            raise UserError(_("Invoice must be in draft or open state in order to be cancelled."))
        return self.action_cancel()

    @api.multi
    def invoice_validate(self):
        return self.write({'state': 'paid'})

    @api.multi
    def name_get(self):
        result = []
        for me in self :
            result.append((me.id, "%s - %s" % (me.number_invoice, me.partner_id.name)))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name :
            recs = self.search([
                '|',
                ('number_invoice', operator, name),
                ('partner_id.name', operator, name),
            ] + args, limit=limit)
        else :
            recs = self.search([] + args, limit=limit)
        return recs.name_get() 

    @api.multi
    def unlink(self):
        for me_id in self :
            if me_id.state != 'draft':
                raise Warning('Cannot delete data')
        return super(AccountInvoice, self).unlink()


class AccountInvoiceLine(models.Model):
    _name = "account.invoice.line"
    _description = "Invoice Line"

    @api.one
    @api.depends('price_unit','quantity', 'product_id')
    def _compute_price(self):
        price = self.price_unit
        self.price_subtotal_signed = self.price_total
        self.price_subtotal = self.quantity * price
        self.price_total = self.price_subtotal

    uom_id = fields.Many2one('product.uom', string='Unit of Measure',
        ondelete='set null', index=True, oldname='uos_id')
    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(default=10)
    invoice_id = fields.Many2one('clinic.invoice', string='Invoice Reference', ondelete='cascade', index=True)
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', index=True)
    price_unit = fields.Float(string='Unit Price', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    price_subtotal = fields.Monetary(string='Amount',
        store=True, readonly=True, compute='_compute_price')
    price_total = fields.Monetary(string='Amount',
        store=True, readonly=True, compute='_compute_price')
    quantity = fields.Float(string='Quantity', required=True, default=1)
    type = fields.Selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Vendor Bill'),
            ('out_refund','Customer Credit Note'),
            ('in_refund','Vendor Credit Note'),
        ], readonly=True, index=True, change_default=True,
        default=lambda self: self._context.get('type', 'out_invoice'),
        track_visibility='always')
    partner_id = fields.Many2one('res.partner', string='Partner',
        related='invoice_id.partner_id', store=True, readonly=True, related_sudo=False)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        domain = {} # self._onchange_price        
        if not self.invoice_id:
            return

        # fpos = self.invoice_id.fiscal_position_id
        part = self.invoice_id.partner_id
        # currency = self.invoice_id.currency_id
        # type = self.invoice_id.type

        if not part:
            warning = {
                    'title': _('Warning!'),
                    'message': _('You must first select a partner!'),
                }
            return {'warning': warning}

        # if not self.product_id:
        #     if type not in ('in_invoice', 'in_refund'):
        #         self.price_unit = 0.0
        #     domain['uom_id'] = []
        # else:
        #     if part.lang:
        #         product = self.product_id.with_context(lang=part.lang)
        #     else:
        #         
        product = self.product_id
        self.name = product.partner_ref
        self._set_taxes()
        print(self.price_total, self.invoice_id.amount_total)

        # if not self.product_id:
        #     if type not in ('in_invoice', 'in_refund'):
        #         self.price_unit = 0.0
        #     domain['uom_id'] = []
        # else:
        #     if part.lang:
        #         product = self.product_id.with_context(lang=part.lang)
        #     else:
        #         product = self.product_id

        #     self.name = product.partner_ref

        #     if not self.uom_id or product.uom_id.category_id.id != self.uom_id.category_id.id:
        #         self.uom_id = product.uom_id.id
        #     domain['uom_id'] = [('category_id', '=', product.uom_id.category_id.id)]

        #     if currency:

        #         if self.uom_id and self.uom_id.id != product.uom_id.id:
        #             self.price_unit = product.uom_id._compute_price(self.price_unit, self.uom_id)
        # return {'domain': domain}

    # def _onchange_price(self):
    #     self.price_unit = self.product_id.lst_price
    #     print(self.product_id.lst_price)

    @api.v8
    def _set_taxes(self):
        """ Used in on_change to set taxes and price."""
        # if self.invoice_id.type in ('out_invoice', 'out_refund'):
        #     taxes = self.product_id.taxes_id or self.account_id.tax_ids
        # else:
        #     taxes = self.product_id.supplier_taxes_id or self.account_id.tax_ids

        # Keep only taxes of the company
        # company_id = self.company_id or self.env.user.company_id
        # taxes = taxes.filtered(lambda r: r.company_id == company_id)

        # self.invoice_line_tax_ids = fp_taxes = self.invoice_id.fiscal_position_id.map_tax(taxes, self.product_id, self.invoice_id.partner_id)

        # fix_price = self.env['account.tax']._fix_tax_included_price
        # if self.invoice_id.type in ('in_invoice', 'in_refund'):
        #     prec = self.env['decimal.precision'].precision_get('Product Price')
        #     if not self.price_unit or float_compare(self.price_unit, self.product_id.standard_price, precision_digits=prec) == 0:
        #         self.price_unit = self.product_id.standard_price
        # else:
        self.price_unit = self.product_id.lst_price


