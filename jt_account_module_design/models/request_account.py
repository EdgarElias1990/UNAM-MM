from odoo import models, fields, api,_


class RequestAccounts(models.Model):

    _inherit = 'request.accounts'
    _description = "Request to open account"
    
    bank_id = fields.Many2one('res.bank','Bank')

    @api.onchange('project_id')
    def onchange_project_id_bank(self):
        if self.project_id:
            self.bank_id = self.project_id and self.project_id.bank_account_id and self.project_id.bank_account_id and self.project_id.bank_account_id.bank_id and self.project_id.bank_account_id.bank_id.id or False 
    @api.constrains('ministrations_amount')
    def check_ministrations_amount(self):
        return True

    @api.constrains('authorized_amount')
    def check_authorized_amount(self):
        return True
    

class AccountJournal(models.Model):

    _inherit = 'account.journal'

    def name_get(self):
        if 'from_account_design' in self._context:
            res = []
            for journal in self:
                bank_acc = journal.name
                if journal.bank_account_id:
                    bank_acc = journal.bank_account_id.acc_number
                res.append((journal.id, bank_acc))
        else:
            res = super(AccountJournal, self).name_get()
        return res
    
class AccountMove(models.Model):

    _inherit = 'account.move'

    programatic_code = fields.Boolean('Programmatic Code')
    ie_account = fields.Boolean('IEAccount')
    program_code_id = fields.Many2one('program.code','Program Code')
    account_ie_id = fields.Many2one('association.distribution.ie.accounts','I.E. Accounts')

    date_year_program = fields.Char(string='Program Code Search Year',compute='get_year_for_program_search',store=True)
    
    @api.depends('date')
    def get_year_for_program_search(self):
        for rec in self:
            if rec.date:
                rec.date_year_program = rec.date.year
            else:
                rec.date_year_program = ''
                
    @api.model
    def create(self,vals):
        res = super(AccountMove,self).create(vals)
        if res.line_ids:
            program_code_id = res.line_ids.filtered(lambda x:x.program_code_id)
            if program_code_id:
                res.programatic_code = True
            account_ie_id = res.line_ids.filtered(lambda x:x.account_ie_id)
            if account_ie_id:
                res.ie_account = True
        return res
        
class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    is_programatic_code = fields.Boolean(related="move_id.programatic_code",store=True)
    is_ie_account = fields.Boolean(related="move_id.ie_account",store=True)


class Dependency(models.Model):

    _inherit = 'dependency' 
    
    def name_get(self):
        result = []
        if self.env.context and self.env.context.get('model','') and self.env.context.get('model','')=='account.general.ledger':
            for rec in self:
                name = rec.dependency or ''
                if rec.description:
                    name += ' ' + rec.description
                result.append((rec.id, name))
        else:
            result = super(Dependency,self).name_get()
            
        return result

class SubDependency(models.Model):

    _inherit = 'sub.dependency'

    def name_get(self):
        result = []
        if self.env.context and self.env.context.get('model','') and self.env.context.get('model','')=='account.general.ledger':
            for rec in self:
                name = rec.sub_dependency or ''
                if rec.description: 
                    name += ' ' + rec.description
                result.append((rec.id, name))
        else:
            result = super(SubDependency,self).name_get()
        return result
   
        