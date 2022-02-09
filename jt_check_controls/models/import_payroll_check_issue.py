from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError
from datetime import datetime, timedelta
from odoo.tools.misc import profile

class ImportPayrollCheckIssue(models.Model):

    _name = 'import.payroll.check.issue'
    _description = "Importación de reexpedición de cheques de nómina"
    _rec_name = 'case'

    case = fields.Selection([('R', 'R'), ('F', 'F'), ('H', 'H'), ('C', 'C')], string="Caso")
    original_check = fields.Char(string='Número de cheque original')
    original_check_id = fields.Many2one('check.log', string='Número de cheque original', compute='_compute_folio_clave')
    original_bank_code = fields.Char(string='Clave banco original')
    new_check = fields.Char(string='Nuevo número de cheque')
    new_check_id = fields.Many2one('check.log', string='Nuevo número de cheque', compute='_compute_folio_clave_nuevo')
    new_bank_code = fields.Char(string='Clave banco nuevo')
    employee_id = fields.Char(string='Número de trabajador')
    original_fortnight = fields.Char(string='Quincena original')
    new_fortnight = fields.Char(string='Quincena nueva')
    rfc = fields.Char('RFC')
    original_amount = fields.Float(string='Monto original')
    new_amount = fields.Float(string='Monto nuevo')
    upload_date = fields.Date(string='Fecha de carga de archivo', default=datetime.today())
    status = fields.Selection([('Borrador', 'Borrador'), ('Hecho', 'Hecho')],
                              required=True, readonly=True, copy=False, tracking=True, default='Borrador')

    _sql_constraints = [('original_check_id_new_check_id', 'unique(original_check_id,new_check_id)',
                         'El registro debe ser único')]

    @api.constrains('original_check', 'new_check')
    def folio_constraints(self):
        if not self.original_check:
            raise UserError(_("El campo Número de cheque original no debe estar vacío."))
        elif not self.new_check:
            raise UserError(_("El campo Nuevo número de cheque no debe estar vacío."))

    def _compute_folio_clave(self):
        if self.original_check and self.original_bank_code:
            cod = self.env['check.log'].search([('bank_id.bank_id.l10n_mx_edi_code','=',self.original_bank_code),
                                                ('folio','=',self.original_check)],limit=1)
            if cod:
                self.original_check_id = cod.id
        if not self.original_check:
            self.original_check = '1'

    def _compute_folio_clave_nuevo(self):
        if self.new_bank_code and self.new_check:
            cod_2 = self.env['check.log'].search([('bank_id.bank_id.l10n_mx_edi_code','=',self.new_bank_code),
                                                ('folio','=',self.new_check)],limit=1)
            if cod_2:
                self.new_check_id = cod_2.id
        if not self.new_check:
            self.new_check = '1'


    def action_update_check_and_amount(self):
        for rec in self:
            if rec.new_amount >= 0 and rec.status == 'Borrador':
                if rec.original_check_id:
                    move_id = self.env['account.move'].search([('check_folio_id','=',rec.original_check_id.id),
                                                               ('partner_id.vat','=',rec.rfc)],limit=1)
                    cheque_nomina = self.env['payment.batch.supplier'].search([
                        ('payment_issuing_bank_id.bank_id.l10n_mx_edi_code','=',rec.original_bank_code),
                        ('payment_req_ids.check_folio_id','=',rec.original_check_id.id)],limit=1)

                    if move_id.check_status == 'Charged':
                        raise UserError(_("No se puede reexpedir un cheque en estatus Cobrado"))
                    
                    if move_id: 
                        #move_id.action_draft()
                        #move_id.action_register()
                        if rec.new_check_id:
                            move_id.check_folio_id = rec.new_check_id.id
                            move_id.related_check_history = rec.original_check_id.folio
                            rec.new_check_id.status = 'Printed'
                            cheque_nomina.payment_req_ids.check_folio_id = rec.new_check_id.id
                        rec.original_check_id.status = 'Reissued'
                        rec.status = 'Hecho'
                        notification = {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': _('¡Realizado!'),
                                'message': _('Registro actualizado'),
                                'type': 'success',  # types: success,warning,danger,info
                                'sticky': True, # True/False will display for few seconds if false
                            },
                        }
                        return notification
                    else:
                        raise UserError(_("No existen coincidencias en las Solicitudes de Pago de Nómina"))

            # if rec.new_amount==0:
            #     if rec.original_check_id:
            #         move_id = self.env['account.move'].search([('check_folio_id','=',rec.original_check_id.id)],limit=1)
            #         if move_id:
            #             if rec.new_check_id:
            #                 move_id.check_folio_id = rec.new_check_id.id
            #                 move_id.related_check_history = rec.original_check_id.folio
            #                 rec.new_check_id.status = 'Printed'
            #         rec.original_check_id.status = 'Reissued'
            #         rec.status = 'Hecho'
            #         notification = {
            #             'type': 'ir.actions.client',
            #             'tag': 'display_notification',
            #             'params': {
            #                 'title': _('¡Realizado!'),
            #                 'message': _('Registro actualizado'),
            #                 'type': 'success',  # types: success,warning,danger,info
            #                 'sticky': True, # True/False will display for few seconds if false
            #             },
            #         }
            #         return notification

            if rec.status == 'Hecho':
                notification = {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                    'title': _('¡Error!'),
                    'message': _('Registro ya procesado'),
                    'type': 'danger',  # types: success,warning,danger,info
                    'sticky': True,  # True/False will display for few seconds if false
                    },
                }
            return notification

    def unlink(self):   #Creación de función para eliminar campos
        for rec in self:
            if rec.status == 'Hecho':
                raise UserError(_("El registro debe estar en borrador para ser eliminado"))

        return super(ImportPayrollCheckIssue, self).unlink()
