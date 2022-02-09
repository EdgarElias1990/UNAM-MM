from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError, UserError

class CheckPerBox(models.Model):

    _name = 'check.per.box'
    _description = "Check Per Box"
    
    @api.depends('check_per_box','cost_per_check')
    def get_total_check_cost(self):
        for rec in self:
            rec.total_cost_for_checks = rec.check_per_box * rec.cost_per_check
            
    checkbook_id = fields.Many2one('checkbook.request','CheckBook')
    bank_id = fields.Many2one(related='checkbook_id.bank_id',store=True)
    bank_account_id = fields.Many2one(related='checkbook_id.bank_account_id',store=True)
    checkbook_no = fields.Char(related='checkbook_id.checkbook_no',store=True)
    check_receipt_date = fields.Date(srting="Check Receipt Date",default=datetime.today())
    box_no = fields.Integer(string="Box No.",group_operator=False)
    appliaction_date = fields.Date("Checkbook Request Date")
    intial_folio = fields.Integer(string="Initial Folio",group_operator='min')
    final_folio = fields.Integer(string="Final Folio",group_operator='max')
    check_per_box = fields.Integer(string="Checks Per Box")
    cost_per_check = fields.Float(string="Cost per check",group_operator='avg')
    total_cost_for_checks = fields.Float(compute='get_total_check_cost',string="Total cost for checks",store=True)
    
    
    
    def print_pdf_report(self):
        return self.env.ref('jt_check_controls.checkbook_request_id').report_action(self)        
