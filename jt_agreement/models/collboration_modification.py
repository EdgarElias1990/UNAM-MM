from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
from odoo.exceptions import ValidationError,UserError

class BasesCollabrationModification(models.Model):

    _name = 'bases.collaboration.modification'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Bases Collaboration Modification"
    _rec_name = 'folio'

    @api.model
    def create(self, vals):
        res = super(BasesCollabrationModification, self).create(vals)
        if res.bases_collaboration_id and res.bases_collaboration_id.state in ('cancelled','to_be_cancelled'):
            raise ValidationError(_("Can't create Modifications for Cancelled Bases of Collabration!"))
        
        name = self.env['ir.sequence'].next_by_code('collaboration.modification')
        res.folio = name
        return res

    @api.model
    def default_get(self, fields):
        res = super(BasesCollabrationModification, self).default_get(fields)
        if 'bases_collaboration_id' in res.keys():
            collaboration = self.env['bases.collaboration'].browse(res.get('bases_collaboration_id'))
            committee_vals = []
            for committee in collaboration.committe_ids:
                committee_vals.append({
                    'column_id': committee.column_id and committee.column_id.id or False,
                    'column_position_id': committee.column_position_id and committee.column_position_id.id or False,
                })
            res.update({
                'committe_ids': [(0, 0, val) for val in committee_vals]
            })
        return res

    folio = fields.Char("Amendment folio")
    bases_collaboration_id = fields.Many2one('bases.collaboration', 'Collaboration Databse Name')
    date = fields.Date("Modification Date")
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed')], string="State", default="draft")
    change_of = fields.Selection([('committee', 'Technical Committee'),
                                  ('goals', 'Goals'),
                                  ('dependency', 'Dependence')], string="Change Of")
    dependency_id = fields.Many2one('dependency', string="Dependence")
    new_dependency_id = fields.Many2one('dependency', string="New Dependence")
    current_target = fields.Text('Current Target')
    new_objective = fields.Text("New Objective")
    bc_modification_format = fields.Binary("BC Modification Format")
    committe_ids = fields.One2many('committee', 'collaboration_modi_id', string="Committees")
    new_committe_ids = fields.One2many('committee', 'new_collaboration_modi_id', string="Committees")

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_('You cannot delete an entry which has been confirmed.'))
        return super(BasesCollabrationModification, self).unlink()


    def confirm(self):
        if self.change_of == 'goals' and self.new_objective and self.bases_collaboration_id:
            self.bases_collaboration_id.goals = self.new_objective
        if self.change_of == 'committee' and self.bases_collaboration_id:
            self.bases_collaboration_id.committe_ids = [(5, 0)]
            vals = []
            for committee in self.new_committe_ids:
                vals.append({
                    'column_id': committee.column_id and committee.column_id.id or False,
                    'column_position_id': committee.column_position_id and committee.column_position_id.id or False,
                })
            self.bases_collaboration_id.committe_ids = [(0, 0, val) for val in vals]
        if self.change_of == 'dependency' and self.bases_collaboration_id:
            collaboration = self.bases_collaboration_id
            withdrawal_req = self.env['request.open.balance'].create({
                'name': collaboration.name,
                'bases_collaboration_id': collaboration.id,
                'agreement_number':collaboration.convention_no,
                #'agreement_number_id': collaboration.agreement_type_id and collaboration.agreement_type_id.id or False,
                'type_of_operation': 'withdrawal',
                'apply_to_basis_collaboration': True,
                'opening_balance': collaboration.available_bal,
                'user_id': self.env.user.id,
                'supporting_documentation': self.bc_modification_format,
                'liability_account_id': collaboration.liability_account_id.id if collaboration.liability_account_id
                else False,
                'interest_account_id': collaboration.interest_account_id.id if collaboration.interest_account_id
                else False,
                'investment_account_id': collaboration.investment_account_id.id if collaboration.investment_account_id
                else False,
                'availability_account_id': collaboration.availability_account_id.id if collaboration.availability_account_id
                else False
            })
            #withdrawal_req.action_confirmed()
            collaboration.state = 'to_be_cancelled'
        self.state = 'confirmed'

class Committee(models.Model):
    _inherit = 'committee'

    collaboration_modi_id = fields.Many2one('bases.collaboration.modification', "Collaboration Modification")
    new_collaboration_modi_id = fields.Many2one('bases.collaboration.modification', "Collaboration Modification")