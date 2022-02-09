from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang, format_date, get_lang
from babel.dates import format_datetime, format_date


class EmployeePayroll(models.Model):

    _inherit = 'employee.payroll.file'
    
    check_folio_id = fields.Many2one('check.log', "Check Number")
    check_final_folio_id = fields.Many2one('check.log', "Check final number")

    def action_reviewed(self):
        result = super(EmployeePayroll,self).action_reviewed()
        for rec in self:
            if rec.check_folio_id and not rec.check_final_folio_id:
                if rec.check_folio_id.status != 'Cancelled':
                    rec.check_folio_id.status = 'Assigned for shipping'
                    rec.check_folio_id.general_status = 'assigned'
            elif rec.check_folio_id and rec.check_final_folio_id and rec.check_folio_id.id != rec.check_final_folio_id.id:
                if rec.check_final_folio_id.status != 'Cancelled':
                    rec.check_final_folio_id.status = 'Assigned for shipping'
                    rec.check_final_folio_id.general_status = 'assigned'
                    rec.check_folio_id.status = 'Cancelled'
            elif rec.check_folio_id and rec.check_final_folio_id and rec.check_folio_id.id == rec.check_final_folio_id.id:
                if rec.check_final_folio_id.status != 'Cancelled':
                    rec.check_final_folio_id.status = 'Assigned for shipping'
                    rec.check_final_folio_id.general_status = 'assigned'
            for pension_pay in rec.pension_payment_line_ids:
                if pension_pay.check_folio_id:
                    if pension_pay.check_folio_id.status != 'Cancelled':
                        pension_pay.check_folio_id.status = 'Assigned for shipping'
                        pension_pay.check_folio_id.general_status = 'assigned'
        return result
    
    def action_done(self):
        result = super(EmployeePayroll,self).action_done()
        for rec in self.filtered(lambda x:x.check_final_folio_id):
            rec.check_final_folio_id.status = 'Printed'
            rec.check_final_folio_id.general_status = 'assigned'
        return result
        
    def get_payroll_payment_vals(self):
        vals = super(EmployeePayroll,self).get_payroll_payment_vals() 
        if self.check_final_folio_id:
            vals.update({'check_folio_id':self.check_final_folio_id.id})
        elif self.check_folio_id:
            vals.update({'check_folio_id':self.check_folio_id.id})
        return vals
    
    def get_pension_payment_request_vals(self,line):
        vals = super(EmployeePayroll,self).get_pension_payment_request_vals(line)
        if line.check_folio_id:
            vals.update({'check_folio_id':line.check_folio_id.id})
        return vals
      
    @api.model
    def create(self,vals):
        res = super(EmployeePayroll,self).create(vals)
        check_payment_method = self.env.ref('l10n_mx_edi.payment_method_cheque').id
        if res.check_number and res.check_number.isnumeric() and res.l10n_mx_edi_payment_method_id and res.l10n_mx_edi_payment_method_id.id==check_payment_method:
            rec_check_number = int(res.check_number)  
            
            check_id = self.env['check.log'].search([('bank_id.bank_id.l10n_mx_edi_code','=',res.bank_key),('folio','=',rec_check_number)],limit=1)
            
            if check_id and check_id.general_status != 'available' and check_id not in ('Checkbook registration','Assigned for shipping','Available for printing'):
                raise UserError(_('El cheque '+ str(rec_check_number) +' no se encuentra disponible'))
            
            if check_id:
                res.check_folio_id = check_id.id
            else:
                raise UserError(_('Some check '+ str(rec_check_number) +' are not discharged within the check log'))
            
        return res
    
    def write(self,vals):
        result = super(EmployeePayroll,self).write(vals)
        if 'check_number' in vals or 'l10n_mx_edi_payment_method_id' in vals:
            check_payment_method = self.env.ref('l10n_mx_edi.payment_method_cheque').id
            for res in self:
                if res.check_number and res.check_number.isnumeric() and res.l10n_mx_edi_payment_method_id and res.l10n_mx_edi_payment_method_id.id==check_payment_method:
                    rec_check_number = int(res.check_number)  
                                  
                    check_id = self.env['check.log'].search([('bank_id.bank_id.l10n_mx_edi_code','=',res.bank_key),('folio','=',rec_check_number)],limit=1)
                    
                    if check_id and check_id.general_status != 'available' and check_id not in ('Checkbook registration','Assigned for shipping','Available for printing'):
                        raise UserError(_('El cheque '+ str(rec_check_number) +' no se encuentra disponible'))
                    
                    if check_id:
                        if not res.check_folio_id:
                            res.check_folio_id = check_id.id
                        elif res.check_folio_id.id != check_id.id:
                            res.check_final_folio_id = check_id.id

                    else:
                        raise UserError(_('Some check '+ str(rec_check_number) +' are not discharged within the check log'))

                            
#                 else:
#                     res.check_final_folio_id = False     
        return result

class PensionPaymentLine(models.Model):
    
    _inherit = 'pension.payment.line'

    check_folio_id = fields.Many2one('check.log', "Check Number")

    @api.model
    def create(self,vals):
        res = super(PensionPaymentLine,self).create(vals)
        check_payment_method = self.env.ref('l10n_mx_edi.payment_method_cheque').id
        if res.check_number and res.check_number.isnumeric() and res.l10n_mx_edi_payment_method_id and res.l10n_mx_edi_payment_method_id.id==check_payment_method:
            rec_check_number = int(res.check_number)  
            
            check_id = self.env['check.log'].search([('bank_id.bank_id.l10n_mx_edi_code','=',res.bank_key),('folio','=',rec_check_number)],limit=1)
            if check_id and check_id.general_status != 'available' and check_id not in ('Checkbook registration','Assigned for shipping','Available for printing'):
                raise UserError(_('El cheque '+ str(rec_check_number) +' no se encuentra disponible'))
            
            if check_id:
                res.check_folio_id = check_id.id
            else:
                raise UserError(_('Some check '+ str(rec_check_number) +' are not discharged within the check log'))
        return res

    def write(self,vals):
        result = super(PensionPaymentLine,self).write(vals)
        if 'check_number' in vals or 'l10n_mx_edi_payment_method_id' in vals:
            check_payment_method = self.env.ref('l10n_mx_edi.payment_method_cheque').id
            for res in self:
                if res.check_number and res.check_number.isnumeric() and res.l10n_mx_edi_payment_method_id and res.l10n_mx_edi_payment_method_id.id==check_payment_method:
                    rec_check_number = int(res.check_number)  
                                  
                    check_id = self.env['check.log'].search([('bank_id.bank_id.l10n_mx_edi_code','=',res.bank_key),('folio','=',rec_check_number)],limit=1)
                    if check_id and check_id.general_status != 'available' and check_id not in ('Checkbook registration','Assigned for shipping','Available for printing'):
                        raise UserError(_('El cheque '+ str(rec_check_number) +' no se encuentra disponible'))
                    
                    if check_id:
                        #if res.check_folio_id:
                        res.check_folio_id = check_id.id
#                         elif res.check_folio_id.id != check_id.id:
#                             res.check_final_folio_id = check_id.id

                    else:
                        raise UserError(_('Some check '+ str(rec_check_number) +' are not discharged within the check log'))
                            
#                 else:
#                     res.check_final_folio_id = False     
        return result

class CustomPayrollProcessing(models.Model):

    _inherit = 'custom.payroll.processing'

    def get_perception_check_log(self,rec_check_number,rec_bank_key):
        
        log = self.env['check.log'].search([('folio', '=', rec_check_number),
                ('status', 'in', ('Checkbook registration', 'Assigned for shipping',
                'Available for printing')), ('general_status', '=', 'available'),
                            ('bank_id.bank_id.l10n_mx_edi_code', '=', rec_bank_key)], limit=1)            
        from_check = True
        
        return log,from_check
    
