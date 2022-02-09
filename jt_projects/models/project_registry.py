from odoo import models, fields, api,_
from datetime import date
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

class ProjectProgramCode(models.Model):
    
    _name = 'custom.project.programcode'
    
    project_id = fields.Many2one('project.project', string='Project',ondelete='cascade')
    program_code_id = fields.Many2one('program.code','Program Code')

    total_assigned_amt = fields.Float(
        string="Assigned Total Annual", compute="_compute_amt")
    total_per_exercise = fields.Float(
        string="Per Exercise", compute="_compute_amt")
    total_paid = fields.Float(
        string="Paid", compute="_compute_amt")

    @api.depends('program_code_id')
    def _compute_amt(self):
        for rec in self:
            total_assigned_amt = 0
            total_paid = 0
            total_per_exercise = 0
            
            if rec.program_code_id:
                total_assigned_amt = rec.program_code_id.total_authorized_amt
                
#                 self.env.cr.execute("select coalesce(sum(ebl.assigned),0) from expenditure_budget_line ebl where ebl.program_code_id = %s ", (rec.program_code_id.id,))
#                 my_datas = self.env.cr.fetchone()
#                 if my_datas:
#                     total_assigned_amt = my_datas[0]

                if rec.project_id and rec.project_id.is_papiit_project:
                    #total_per_exercise = rec.program_code_id.total_authorized_amt

                    self.env.cr.execute("select coalesce(sum(ebl.available),0) from expenditure_budget_line ebl where ebl.program_code_id = %s", (rec.program_code_id.id,))
                    my_datas = self.env.cr.fetchone()
                    if my_datas:
                        total_per_exercise = my_datas[0]
                    
                    self.env.cr.execute("select coalesce(sum(ebl.assigned),0) from expenditure_budget_line ebl where ebl.program_code_id = %s",(rec.program_code_id.id,))
                    my_datas = self.env.cr.fetchone()
                    if my_datas:
                        total_assigned_amt = my_datas[0]
    
                    self.env.cr.execute("""(select coalesce(sum(abs(line.balance)+abs(line.tax_price_cr)),0) from account_move_line line,account_move amove,account_payment apay 
                                        where  line.program_code_id = %s and amove.id=line.move_id and amove.payment_state=%s and apay.payment_request_id = amove.id)""", (rec.program_code_id.id,'paid',))
                    
                    my_datas = self.env.cr.fetchone()
                    if my_datas:
                        total_paid = my_datas[0]
                else:
                    verification_lines = self.env['verification.expense.line'].search([('program_code','=',rec.program_code_id.id),('verification_expense_id.status','=','approve')])
                    total_paid = sum(x.subtotal for x in verification_lines)
                    total_per_exercise = total_assigned_amt - total_paid
                    
            rec.total_assigned_amt = total_assigned_amt
            rec.total_paid = total_paid
            rec.total_per_exercise = total_per_exercise
                
    @api.constrains('program_code_id')
    def _project_program_unique(self):
        for record in self:
            if record.program_code_id:
                line = self.env['custom.project.programcode'].search([('id', '!=', record.id),('program_code_id','=',record.program_code_id.id)],limit=1)
                if line:
                    raise ValidationError(_('This Program Code Already Link To Project ')+ str(line.project_id.number))

    
class ProjectRegistry(models.Model):
    _inherit = 'project.project'
    _description = "CONACYT Project Registry"

    project_type = fields.Selection([('conacyt', 'CONACYT'),
                                     ('concurrent', 'Concurrent'),
                                     ('other', 'Other projects with checkbook')], "Project Type")
    project_type_identifier_id = fields.Many2one(
        'project.type', string="PTI")

    proj_start_date = fields.Date("Start Date")
    proj_end_date = fields.Date("End Date")
    visibility = fields.Selection(
        [('due', 'due'), ('expire', 'expire')], 'visibility')
    program_code = fields.Many2one('program.code', string='Program Code')
    rfc = fields.Char("RFC of the person in charge",related="responsible_name.rfc")
    allocated_amount = fields.Monetary("Allocated Amount")
    approved_amount = fields.Monetary("Approved Amount")
    trade_number = fields.Char("Trade Number")
    status = fields.Selection([('open', 'Open'),
                               ('closed', 'Closed')], "Status", default='open')
    check_counts = fields.Integer(compute='compute_count')
    bank_account_id = fields.Many2one("account.journal", "Bank")
    bank_acc_number_id = fields.Many2one(
        "res.partner.bank", related='bank_account_id.bank_account_id', string="Bank Key")
    branch_office = fields.Char(
        related='bank_acc_number_id.branch_number', string="Square")
    ministrations = fields.Integer("Number of ministrations")
    ministering_amount = fields.Monetary("Ministering amount")
    check_project_due = fields.Boolean(
        "Check Project Due", default=True, compute="get_project_due", store=True)
    check_project_expire = fields.Boolean(
        "Check Project expire", default=True, compute="get_project_due", store=True)

    is_papiit_project = fields.Boolean(
        'PAPIIT project', default=False, copy=False)

    is_related_agreement = fields.Boolean(
        'Is It related to agreement?', default=False)

    is_code_create = fields.Boolean('Code Created',copy=False,default=False)
    
    #agreement_type = fields.Char("Agreement Type", related="base_id.agreement_type_id.code")
    agreement_type_id = fields.Many2one(related="base_id.agreement_type_id",string="AT")

    resource_type = fields.Selection(
        [('R', 'R (Remnant)'), ('P', 'P (Budget)')], string="Resource Type")
    pre_account_id = fields.Many2one('account.account', 'Previous')
    PAPIIT_project_type = fields.Selection(
        [('PAPIIT', 'PAPIIT'), ('PAPIME', 'PAPIME'), ('INFOCAB', 'INFOCAB')], string="PAPIIT Project Type")
    dependency_id = fields.Many2one('dependency', "Dependency")    
    subdependency_id = fields.Many2one('sub.dependency', "Sub Dependency")
    technical_support_id = fields.Many2one('hr.employee', 'Technical support')
    administrative_manager_id = fields.Many2one(
        'hr.employee', 'Administrative Manager')
    exercised_amount = fields.Monetary("Amount exercised")
    final_amount = fields.Monetary(
        string="Final amount", compute='get_final_amount', store=True)
    co_responsible_id = fields.Many2one('hr.employee', 'Co-responsible Name')
    co_responsible_rfc = fields.Char(
        related='co_responsible_id.rfc', string='Co-responsible RFC')
    responsible_name = fields.Many2one('hr.employee', 'Responsible name')
    stage_identifier_id = fields.Many2one('stage', string="S")

    project_ministrations_ids = fields.One2many(
        'project.ministrations', 'project_id', string='Project Ministrations')

    custom_stage_id = fields.Many2one('project.custom.stage','Stage')
    custom_stage_description = fields.Text(related='custom_stage_id.description',string="Description Stage")
    custom_project_type_id = fields.Many2one('project.type.custom','Project Type Identifier')
    
    program_code_ids = fields.Many2many('program.code','program_code_project_rel','program_id','project_id',compute="get_program_ids")
    project_status = fields.Selection(
        [('open', 'Open'), ('close', 'Close')], string="Project Status")

    base_id = fields.Many2one('bases.collaboration','TOA')

    project_programcode_ids = fields.One2many('custom.project.programcode', 'project_id', string='Program Code')
    
   
#     @api.constrains('number')
#     def _project_number_unique(self):
#         for record in self:
#             project_id = self.env['project.project'].search([('id', '!=', record.id),('number','=',record.number)],limit=1)
#             if project_id:
#                 raise ValidationError(_('The Project Number Value Must Be Unique'))

#     @api.constrains('number_agreement','agreement_type')
#     def _project_number_agreement_type_unique(self):
#         for record in self:
#             if record.number_agreement and record.agreement_type:
#                 project_id = self.env['project.project'].search([('id', '!=', record.id),('agreement_type','=',record.agreement_type),('number_agreement','=',record.number_agreement)],limit=1)
#                 if project_id:
#                     raise ValidationError(_('The combination of the Agreement Type and Agreement Number fields must be unique'))

    @api.constrains('number','custom_project_type_id','custom_stage_id')
    def _project_number_project_type_unique(self):
        for record in self:
            if record.custom_stage_id and record.number and record.custom_project_type_id:
                project_id = self.env['project.project'].search([('id', '!=', record.id),('custom_stage_id','=',record.custom_stage_id.id),('custom_project_type_id','=',record.custom_project_type_id.id),('number','=',record.number)],limit=1)
                if project_id:
                    raise ValidationError(_('The combination of the Project Type Identifier,Stage and Project Number fields must be unique'))

    @api.model
    def create(self, vals):
        if vals.get('custom_stage_id',False):
            custom_stage_id = self.env['project.custom.stage'].browse(vals.get('custom_stage_id',False))
            if custom_stage_id:
                vals.update({'stage_identifier':custom_stage_id.name,'desc_stage':custom_stage_id.description})

        if vals.get('custom_project_type_id',False):
            custom_project_type_id = self.env['project.type.custom'].browse(vals.get('custom_project_type_id',False))
            if custom_project_type_id:
                vals.update({'project_type_identifier':custom_project_type_id.name})
                
        res = super(ProjectRegistry,self).create(vals)
        for r in res:
            if r.base_id:
                budget_type_agreement_id = self.env['agreement.type'].search([('project_id','=',r.id)],limit=1)
                if budget_type_agreement_id:
                    budget_type_agreement_id.base_id = r.base_id.id 
        return res 
    @api.onchange('custom_stage_id')
    def onchange_custom_stage_id(self):
        if self.custom_stage_id:
            self.stage_identifier = self.custom_stage_id.name
            self.desc_stage = self.custom_stage_id.description
        else:
            self.stage_identifier = ''
            self.desc_stage = ''

    @api.onchange('custom_project_type_id')
    def onchange_custom_project_type_id(self):
        if self.custom_project_type_id:
            self.project_type_identifier = self.custom_project_type_id.name
        else:
            self.project_type_identifier = ''

    @api.onchange('base_id')
    def onchange_base_id(self):
        if self.base_id:
            self.name_agreement = self.base_id.name
            self.number_agreement = self.base_id.convention_no
            self.agreement_type = self.base_id and self.base_id.agreement_type_id and self.base_id.agreement_type_id.code or ''
        else:
            self.name_agreement = ''
            self.number_agreement = ''
            self.agreement_type = ''
                 
#     agreement_type = fields.Char(related='base_id.name',stringname='Agreement Type', size=2)
#     name_agreement = fields.Text(related='base_id.name',string='Name Agreement')
#     number_agreement = fields.Char(related='base_id.convention_no',string='Number Agreement', size=6)
        
    @api.depends('is_papiit_project')
    def get_program_ids(self):
        for rec in self:
            lines = self.env['adequacies.lines'].search([('line_type','=','increase'),('adequacies_id.state','=','accepted'),('adequacies_id.is_from_project','=',True)])
            if lines:
                rec.program_code_ids = [
                    (6, 0, lines.mapped('program').ids)]
            else:
                rec.program_code_ids = [(6, 0, [])]
    
    # @api.onchange('project_type_identifier_id')
    # def onchange_project_type_identifier_id(self):
    #     if self.project_type_identifier_id:
    #         self.number = self.project_type_identifier_id.number

    @api.constrains('allocated_amount')
    def check_allocated_amount(self):
        if self.allocated_amount == 0 and self.project_type:
            raise UserError(_('Please add allocated amount'))

#         if self.allocated_amount == 0 and self.is_papiit_project:
#             raise UserError(_('Please add allocated amount'))


    @api.constrains('approved_amount')
    def check_approved_amount(self):
        if self.approved_amount == 0 and self.project_type=='conacyt':
            raise UserError(_('Please add approved amount'))


#     @api.constrains('exercised_amount')
#     def check_exercised_amount(self):
#         if self.exercised_amount == 0 and self.is_papiit_project:
#             raise UserError(_('Please add Amount exercised'))

    @api.onchange('stage_identifier_id')
    def onchange_stage_identifier_id(self):
        if self.stage_identifier_id:
            self.desc_stage = self.stage_identifier_id.desc

    @api.onchange('program_code')
    def onchange_program_code(self):
        if self.program_code:
            
            self.custom_stage_id = self.program_code.stage_id and self.program_code.stage_id.project_id and self.program_code.stage_id.project_id.custom_stage_id and self.program_code.stage_id.project_id.custom_stage_id.id or False 
            self.desc_stage = self.program_code.desc_stage
            self.number = self.program_code.project_number
            self.custom_project_type_id = self.program_code.project_type_id and self.program_code.project_type_id.project_id and self.program_code.project_type_id.project_id.custom_project_type_id and self.program_code.project_type_id.project_id.custom_project_type_id.id or False
            #self.agreement_type_id = self.program_code.agreement_type_id.id
            self.name_agreement = self.program_code.name_agreement
            self.number_agreement = self.program_code.number_agreement
            self.dependency_id = self.program_code.dependency_id.id
            self.subdependency_id = self.program_code.sub_dependency_id

    @api.depends('exercised_amount', 'allocated_amount')
    def get_final_amount(self):
        for rec in self:
            rec.final_amount = rec.allocated_amount - rec.exercised_amount

    def compute_count(self):
        for record in self:
            record.check_counts = self.env['expense.verification'].search_count(
                [('project_number_id', '=', self.number)])

    def get_project_due_records(self):
        open_project = self.env['project.project'].search(
            [('status', '=', 'open')])
        if open_project:
            open_project.get_project_due()

    @api.depends('proj_end_date', 'status')
    def get_project_due(self):
        for rec in self:                
            if rec.proj_end_date and rec.status:
                end_date = rec.proj_end_date
                today = date.today()
                diff = (end_date - today).days
                if end_date < today and rec.status == 'open':
                    rec.check_project_due = True
                else:
                    rec.check_project_due = False
                if diff <= 21 and diff >= 0 and rec.status == 'open':
                    rec.check_project_expire = True
                else:
                    rec.check_project_expire = False
            else:
                rec.check_project_expire = False
                rec.check_project_due = False

    # def calculate_project_next_to_expire(self):

    #     end_date = self.proj_end_date
    #     today = date.today()
    #     days = end_date
    #     diff = (days - today).days
    #     if diff >= 21:
    #         self.visibility = 'expire'

    def calculate_project_overdue(self):
        print("calll")

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('number', operator, name), ('name', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        project_ids = self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
        return models.lazy_name_get(self.browse(project_ids).with_user(name_get_uid))

    def name_get(self):
        result = []
        for project in self:
            if 'from_conacyt' in self._context:
                name = ''
                if project.number:
                    name = project.number
            else:
                name = project.name
            result.append((project.id, name))
        return result

    # @api.onchange('user_id')
    # def onchnage_user_id(self):
    #     if self.user_id:
    #         self.rfc = self.user_id.partner_id.vat

    @api.onchange('bank_account_id')
    def onchnage_bank_account_id(self):
        if self.bank_account_id and self.bank_account_id.bank_account_id:
            self.bank_acc_number_id = self.bank_account_id.bank_account_id
            self.branch_office = self.bank_account_id.branch_number

    def close_project(self):
        #self.status = 'closed'
        return {
            'name': _('Project Close'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': False,
            'res_model': 'project.close',
            'domain': [],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_current_id': self.id,
                        'default_project_id':self.id,
                        'default_is_papiit_project' : self.is_papiit_project,
                        'active_ids': self.ids}
        }

    def show_attachment(self):
        attachment_action = self.env.ref('base.action_attachment')
        action = attachment_action.read()[0]
        action['context'] = {
            'default_res_model': self._name,
            'default_res_id': self.ids[0]
        
        }
        action['domain'] = [
            ('res_model', '=', 'project.project'),('res_id', 'in', self.ids)]

        return action

    def count_expense_checks(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Checks',
            'view_mode': 'tree,form',
            'res_model': 'expense.verification',
            'domain': [('project_number_id', '=', self.number)],
            'context': "{'create': False}"
        }

    def create_program_code(self):

        #Creating master of agreement catelog that is used in program code
        agreement_type_obj = self.env['agreement.type']
        agreement = agreement_type_obj.search([('project_id','=',self.id),
                                                ('base_id','=',self.base_id.id)], limit=1)
        if not agreement:
            self.env['agreement.type'].create({'project_id':self.id,'base_id':self.base_id.id})

        stage_id = False
        type_id = False
        stage = self.env['stage'].search([('project_id','=',self.id)],limit=1)
        if stage:
            stage_id = stage.id
            
        project_type_id = self.env['project.type'].search([('project_id','=',self.id)],limit=1)
        if project_type_id:
            type_id = project_type_id.id
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Program Code'),
            'view_mode': 'form',
            'res_model': 'project.program.code',
            'target':'new',
            #'domain': [('project_number_id', '=', self.number)],
            'context': {'default_conacyt_project_id': self.id,
                        'default_stage_id':stage_id,
                        'default_project_type_id':type_id,
                        },
        }
        
class ProjectMinistrations(models.Model):

    _name = 'project.ministrations'
    _description = "Project Ministrations"

    project_id = fields.Many2one('project.project', 'Project')
    ministrations = fields.Integer("Number of ministrations")
    ministering_amount = fields.Float("Ministering amount")


    
    
    