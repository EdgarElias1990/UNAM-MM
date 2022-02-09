from odoo import fields, models, api,_
from odoo.exceptions import ValidationError, UserError

class ConfirmCheckBook(models.TransientModel):
    _name = 'confirm.checkbook'
    _description = 'Confirm Checkbook'

    @api.depends('detail_box_ids', 'detail_box_ids.check_per_box', 'detail_box_ids.intial_folio','detail_box_ids.final_folio')
    def get_total_detail_box(self):
        if self.detail_box_ids:
            self.total_detail_box_check = sum(x.check_per_box for x in self.detail_box_ids)

    @api.depends('additional_check_ids', 'additional_check_ids.check_per_box', 'additional_check_ids.intial_folio','additional_check_ids.final_folio')
    def get_total_additional_check(self):
        if self.additional_check_ids:
            self.total_additional_check = sum(x.check_per_box for x in self.additional_check_ids)

    @api.depends('total_detail_box_check', 'total_additional_check')
    def get_total_check(self):
        for rec in self:
            rec.total_checks_received_cal = rec.total_detail_box_check+rec.total_additional_check


    checkbook_no = fields.Char("Checkbook No.")
    received_boxes = fields.Integer("Number of boxes received")
    check_per_box = fields.Integer("Checks per box")
    additional_checks = fields.Integer("Additional checks without cash")
    total_cash = fields.Integer("Total Checks", compute='calculate_total', store=True)

    bank_id = fields.Many2one("account.journal", string="Bank", domain=[('type', '=', 'bank')])
    bank_account_id = fields.Many2one("res.partner.bank", string="Bank Account")
    total_checks_received = fields.Integer("Total checks received")
    
    detail_box_ids= fields.One2many('confirm.checkbook.detail.of.boxes','confirm_check_wizard_id')
    additional_check_ids= fields.One2many('additional.checks.without.cash','confirm_check_wizard_id')
    
    total_detail_box_check = fields.Integer(compute='get_total_detail_box',string='Total checks', store=True)
    total_additional_check = fields.Integer(compute='get_total_additional_check',string='Total checks', store=True)
    total_checks_received_cal = fields.Integer(compute='get_total_check',string="Total checks received",store=True)
    is_click_register = fields.Boolean('Is Click',default=False)
    checkbook_id = fields.Many2one('checkbook.request','Checkbook')
    cost_per_check = fields.Float("Cost per check")
     
    @api.depends('received_boxes', 'check_per_box', 'additional_checks')
    def calculate_total(self):
        #total = (self.received_boxes * self.check_per_box) + self.additional_checks
        total = self.total_checks_received + self.additional_checks
        self.total_cash = total

        
#     def validation_check_folio(self,check_req):
#         bank_id = check_req.bank_id and check_req.bank_id.id or False 
#         other_checkbook_ids = self.env['checkbook.request'].search([('state','=','confirmed'),('bank_id','=',bank_id)])
#         for checkbook in other_checkbook_ids:
#             if check_req.intial_folio >= checkbook.intial_folio and  check_req.intial_folio <= checkbook.final_folio:
#                 raise UserError(_('Cannot register folios that are already registered'))
#             if check_req.final_folio >= checkbook.intial_folio and  check_req.final_folio <= checkbook.final_folio:
#                 raise UserError(_('Cannot register folios that are already registered'))
#             if  checkbook.intial_folio >= check_req.intial_folio and  checkbook.final_folio <= check_req.intial_folio:
#                 raise UserError(_('Cannot register folios that are already registered'))
#             if  checkbook.intial_folio >= check_req.final_folio and  checkbook.final_folio <= check_req.final_folio:
#                 raise UserError(_('Cannot register folios that are already registered'))

    def register_details_box(self):
        self.is_click_register = True
        return {
            'name': _('Check Reception'),
            'type': 'ir.actions.act_window',
            'res_model': 'confirm.checkbook',
            'view_mode': 'form',
            'res_id':self.id,
            'target': 'new',
        }                    
    def apply(self):
        #check_req = self.env['checkbook.request'].browse(self._context.get('active_id'))
        check_req = self.checkbook_id
        if check_req:
            if self.total_checks_received_cal != check_req.amount_checks:
                raise ValidationError(_('Check total does not match the number of checks requested'))
            
            if check_req.bank_id:
                check_req.bank_id.checkbook_no = self.checkbook_no
                check_req.checkbook_no = self.checkbook_no
            checklist = self.env['checklist'].create({
                'checkbook_no': self.checkbook_no,
                'received_boxes': self.received_boxes,
                'check_per_box': self.check_per_box,
                'additional_checks': self.additional_checks,
                'total_cash': self.total_cash,
                'checkbook_req_id': check_req.id
            })
            check_log_list = [] 
            for folio in range(check_req.intial_folio, check_req.final_folio + 1):
                check_log_list.append((0, 0, {
                    'folio': folio,
                    'status': 'Checkbook registration' if folio != int(check_req.print_sample_folio_number) else \
                            'Cancelled',
                    'bank_id': check_req.bank_id.id if check_req.bank_id else False,
                    'bank_account_id': check_req.bank_account_id.id if check_req.bank_account_id else False,
                    'checkbook_no': check_req.checkbook_no,
                    # 'dependence_id': check_req.dependence_id.id if check_req.dependence_id else False,
                    # 'subdependence_id': check_req.subdependence_id.id if check_req.subdependence_id else False
                }))
                if len(check_log_list) > 500000 and check_log_list:
                    checklist.checklist_lines = check_log_list
                    check_log_list = []
            if check_log_list:
                checklist.checklist_lines = check_log_list
                
#                 checklist.checklist_lines = [(0, 0, {
#                     'folio': folio,
#                     'status': 'Checkbook registration' if folio != int(check_req.print_sample_folio_number) else \
#                             'Cancelled',
#                     'bank_id': check_req.bank_id.id if check_req.bank_id else False,
#                     'bank_account_id': check_req.bank_account_id.id if check_req.bank_account_id else False,
#                     'checkbook_no': check_req.checkbook_no,
#                     # 'dependence_id': check_req.dependence_id.id if check_req.dependence_id else False,
#                     # 'subdependence_id': check_req.subdependence_id.id if check_req.subdependence_id else False
#                 })]
            self.bank_id.cost_per_check =  self.cost_per_check
            for line in self.detail_box_ids:
                vals = {
                        'checkbook_id':self.checkbook_id and self.checkbook_id.id or False,
                        'box_no' : line.sequence,
                        'appliaction_date' : self.checkbook_id.appliaction_date,
                        'intial_folio':line.intial_folio,
                        'final_folio':line.final_folio,
                        'check_per_box' : line.check_per_box,
                        'cost_per_check' : self.bank_id and self.bank_id.cost_per_check or 0,
                        }
                self.env['check.per.box'].create(vals)
            for line in self.additional_check_ids:
                vals = {
                        'checkbook_id':self.checkbook_id and self.checkbook_id.id or False,
                        'appliaction_date' : self.checkbook_id.appliaction_date,
                        'intial_folio':line.intial_folio,
                        'final_folio':line.final_folio,
                        'check_per_box' : line.check_per_box,
                        'cost_per_check' : self.bank_id and self.bank_id.cost_per_check or 0,
                        }
                self.env['check.per.box'].create(vals)
            check_req.state = 'confirmed'

class DetailofBoxes(models.TransientModel):
    _name = 'confirm.checkbook.detail.of.boxes'
    _description = 'Detail of Boxes'
    
    @api.depends('intial_folio','final_folio')
    def get_check_per_box(self):
        for rec in self:
            if rec.final_folio and rec.intial_folio:
                rec.check_per_box = rec.final_folio - rec.intial_folio + 1
            else:
                rec.check_per_box = 0

    @api.depends('confirm_check_wizard_id.detail_box_ids')
    def _sequence_ref(self):
        for line in self:
            no = 0
            line.sequence = no
            for l in line.confirm_check_wizard_id.detail_box_ids:
                no += 1
                l.sequence = no
                         
    confirm_check_wizard_id = fields.Many2one('confirm.checkbook')
    sequence = fields.Integer(string="Box No.",compute="_sequence_ref")
    intial_folio = fields.Integer("Initial Check Folio")
    final_folio = fields.Integer("Final Check Folio")
    check_per_box = fields.Integer(compute='get_check_per_box',string="Checks Per Box",store=True)
    
class AdditionalChecksWithoutCash(models.TransientModel):
    _name = 'additional.checks.without.cash'
    _description = 'Additional Checks Without Cash'

    @api.depends('intial_folio','final_folio')
    def get_check_per_box(self):
        for rec in self:
            if rec.final_folio and rec.intial_folio:
                rec.check_per_box = rec.final_folio - rec.intial_folio + 1
            else:
                rec.check_per_box = 0
    
    confirm_check_wizard_id = fields.Many2one('confirm.checkbook')
    intial_folio = fields.Integer("Initial Check Folio")
    final_folio = fields.Integer("Final Check Folio")
    check_per_box = fields.Integer(compute='get_check_per_box',string="Checks Per Box",store=True)
            
