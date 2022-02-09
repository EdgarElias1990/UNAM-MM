from odoo import models, fields, api

class SubOriginResource(models.Model):

    _name = 'sub.origin.resource'
    _description = "Sub origin of Resource"

    name = fields.Char("Sub origin of Resource")
    resource_id = fields.Many2one('resource.origin', "Source of Resource")
    key = fields.Selection(related="resource_id.key_origin",string='Key origin of the resource')
    is_it_enabled_for_agreement = fields.Boolean("Is it enabled for agreement?")
    income_type = fields.Selection([('extra', 'Extraordinary'),
                                    ('own', 'Own')], string="Income Type")
    report_name = fields.Char(string="Report",compute="get_report_display_name",store=True,copy=False)
    report_account_code = fields.Char(string="Account Code",compute="get_report_display_name",store=True,copy=False)
    report_account_name = fields.Char(string="Account Name",compute="get_report_display_name",store=True,copy=False)
    
    @api.depends('name')
    def get_report_display_name(self):
        for rec in self:
            if rec.name:
                if rec.name=='Servicios de educación Bancos (INS-RINS)':
                    rec.report_name = 'SERV. EDUC. BANCOS (INS-RINS)'
                    rec.report_account_code = "411.004.001"
                    rec.report_account_name = "DEPOSITO EN BANCOS"
                elif rec.name=='Servicios de educación Caja Gral.':
                    rec.report_name = 'SERV. EDUC. CAJA GRAL.'
                    rec.report_account_code = "411.004.002"
                    rec.report_account_name = "DEPOSITOS EN CAJA GENERAL"
                elif rec.name=='Aspirantes':
                    rec.report_name = 'ASPIRANTES-LIC.'
                    rec.report_account_code = "411.004.003"
                    rec.report_account_name = "DERECHO EXAMEN ADMISION LICEN"
                elif rec.name=='D.B.I.N.':
                    rec.report_name = 'D.B.I.N.'
                    rec.report_account_code = "411.005.002"
                    rec.report_account_name = "RENTAS"
                elif rec.name=='D.P.Y.D.':
                    rec.report_name = 'D.P.Y.D.'
                    rec.report_account_code = "411.005.001.001"
                    rec.report_account_name = "CONCESIONES Y AUTORIZACIONES"
                elif rec.name=='Venta almacén':
                    rec.report_name = 'VTA. ALMAC.'
                    rec.report_account_code = "411.005.003.001"
                    rec.report_account_name = "VENTAS BAJAS ALMACEN"
                elif rec.name=='Licenciatarios':
                    rec.report_name = 'LICENCIATARIOS'
                    rec.report_account_code = "411.005.001.002"
                    rec.report_account_name = "DERECHO DE MARCA DGP"
                elif rec.name=='DEP en garantia':
                    rec.report_name = 'DEP EN GARANTIA'
                    rec.report_account_code = "221.008.001"
                    rec.report_account_name = "DEPOSI. EN GARANTÍA DE CONCESI"
                elif rec.name=='DGIRE-bancos':
                    rec.report_name = 'DGIRE-BANCOS'
                    rec.report_account_code = "411.004.004"
                    rec.report_account_name = "INCORPORACIONES"
                elif rec.name=='DGIRE-caja':
                    rec.report_name = 'DGIRE-CAJA'
                    rec.report_account_code = "411.004.005"
                    rec.report_account_name = "DGIRE"
                else:
                    rec.report_name = rec.name
                    rec.report_account_code = ""
                    rec.report_account_name = ""
    
    

class ResourceOrigin(models.Model):
    
    _inherit = 'resource.origin'
    
    def name_get(self):
        result = []
        for rec in self:
            name = rec.key_origin or ''
            if rec.desc and self.env.context and self.env.context.get('show_desc_name',False): 
                name = dict(rec._fields['desc'].selection).get(rec.desc)
                if self.env.user.lang == 'es_MX':
                    if name=='Federal Subsidy':
                        name = 'Subsidio Federal'
                    elif name=='Extraordinary Income':
                        name = 'Ingresos Extraordinarios'
                    elif name=='Education Services':
                        name = 'Servicios de Educación'
                    elif name=='Financial':
                        name = 'Rendimientos Financieros'
                    elif name=='Other Products':
                        name = 'Otros Productos'
                    elif name=='Returns Reassignment PEF':
                        name = 'Reasignación PEF'
                        
            result.append((rec.id, name))
        return result    