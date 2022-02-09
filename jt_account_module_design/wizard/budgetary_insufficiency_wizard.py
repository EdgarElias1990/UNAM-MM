##############################################################################
from odoo import models, fields
from datetime import datetime

class BudegtInsufficiencWiz(models.TransientModel):

    _inherit = 'budget.insufficien.wiz'
    _description = 'Budgetary Insufficienc'

    provision_id = fields.Many2one('provision','Provision')

    def action_ok(self):
        res = super(BudegtInsufficiencWiz,self).action_ok()
        if self.move_ids and not self.move_id:
            for move in self.move_ids:
                move.provision_payment_state = 'rejected'
        else:
            self.move_id.provision_payment_state = 'rejected'
         
        return res
     
    def action_budget_allocation(self):
        res = super(BudegtInsufficiencWiz,self).action_budget_allocation()
        if self.move_ids and not self.move_id:
            for move in self.move_ids:
                move.set_provision_payment_state_provision()
        else:
            self.move_id.set_provision_payment_state_provision()
 
             
        return res