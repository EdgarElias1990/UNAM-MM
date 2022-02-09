# -*- coding: utf-8 -*-
##############################################################################
#
#    Jupical Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Jupical Technologies(<http://www.jupical.com>).
#    Author: Jupical Technologies Pvt. Ltd.(<http://www.jupical.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, fields, api, _,tools

class IncomeAnnualReport(models.Model):
    
    _name = 'income.annual.report'
    _description = 'Income Annual Report'
    _order = 'year'
    _auto = False

    sub_origin_resource_id = fields.Many2one('sub.origin.resource', "Name")
    sub_origin_name = fields.Char("Name")
    sub_origin_name_group_by = fields.Char("Name Group")
    journal_id = fields.Many2one("account.journal","Accounting Account Description")
    bank_account_id = fields.Many2one(related="journal_id.bank_account_id",string="Bank Account")
    bank_account_name = fields.Char(related="sub_origin_resource_id.report_account_name",string="Bank Account")
    account_code = fields.Char(related="sub_origin_resource_id.report_account_code",string="Account")
    year = fields.Char('Year')
    january = fields.Float('January')
    february = fields.Float('February')
    march = fields.Float('March')
    april = fields.Float('April')
    may = fields.Float('May')
    june = fields.Float('June')
    july = fields.Float('July')
    august = fields.Float('August')
    september = fields.Float('September')
    october = fields.Float('October')
    november = fields.Float('November')
    december = fields.Float('December')
    total = fields.Float('Total')
    
    def get_header_year_list(self,docs):
        year_list = self.env['income.annual.report'].search([('id','>',0)]).mapped('year')
        max_year = max(year_list)
        min_year = min(year_list)
        str1 = ''
        if max_year == min_year:
            str1 = "ENERO-DICIEMBRE "+str(min_year)
        else:
            str1 = "ENERO "+str(min_year)+ " A " +"DICIEMBRE "+str(max_year)
            
        return str1
     
    def get_origin_records(self,records):
        return records.mapped('sub_origin_resource_id')
    
    def get_origin_records_data(self,origin_id,docs):
        records = docs.filtered(lambda x:x.sub_origin_resource_id.id==origin_id.id)
        journal_ids = records.mapped('journal_id')
        data_list = []
        for journal in journal_ids:
            inner_list = []
            if not data_list:
                inner_list.append(origin_id.report_name)
            else:
                inner_list.append('')
                
            inner_list.append(journal.bank_account_id.acc_number)
            inner_list.append(origin_id.report_account_code)
            inner_list.append(origin_id.report_account_name)
            
             
            inner_list.append(sum(x.january for x in records.filtered(lambda a:a.journal_id.id==journal.id)))
            inner_list.append(sum(x.february for x in records.filtered(lambda a:a.journal_id.id==journal.id)))
            inner_list.append(sum(x.march for x in records.filtered(lambda a:a.journal_id.id==journal.id)))
            inner_list.append(sum(x.april for x in records.filtered(lambda a:a.journal_id.id==journal.id)))
            inner_list.append(sum(x.may for x in records.filtered(lambda a:a.journal_id.id==journal.id)))
            inner_list.append(sum(x.june for x in records.filtered(lambda a:a.journal_id.id==journal.id)))
            inner_list.append(sum(x.july for x in records.filtered(lambda a:a.journal_id.id==journal.id)))
            inner_list.append(sum(x.august for x in records.filtered(lambda a:a.journal_id.id==journal.id)))
            inner_list.append(sum(x.september for x in records.filtered(lambda a:a.journal_id.id==journal.id)))
            inner_list.append(sum(x.october for x in records.filtered(lambda a:a.journal_id.id==journal.id)))
            inner_list.append(sum(x.november for x in records.filtered(lambda a:a.journal_id.id==journal.id)))
            inner_list.append(sum(x.december for x in records.filtered(lambda a:a.journal_id.id==journal.id)))
            inner_list.append(sum(x.total for x in records.filtered(lambda a:a.journal_id.id==journal.id)))
            data_list.append(inner_list)
            
        return data_list
        
    def init(self):
        tools.drop_view_if_exists(self.env.cr,self._table)
        self.env.cr.execute('''
            CREATE OR REPLACE VIEW %s AS (
                select max(ap.id) as id,ap.sub_origin_resource_id as sub_origin_resource_id,
                ap.journal_id as journal_id, 
                s0.report_name as sub_origin_name,s0.name as sub_origin_name_group_by,    
                Cast((extract(year from payment_date)) as Text) as year,
                sum(case when extract(month from payment_date) = 1 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) january,
                sum(case when extract(month from payment_date) = 2 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) february,
                sum(case when extract(month from payment_date) = 3 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) march,
                sum(case when extract(month from payment_date) = 4 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) april,
                sum(case when extract(month from payment_date) = 5 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) may,
                sum(case when extract(month from payment_date) = 6 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) june,
                sum(case when extract(month from payment_date) = 7 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) july,
                sum(case when extract(month from payment_date) = 8 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) august,
                sum(case when extract(month from payment_date) = 9 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) september,
                sum(case when extract(month from payment_date) = 10 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) october,
                sum(case when extract(month from payment_date) = 11 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) november,
                sum(case when extract(month from payment_date) = 12 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) december,
                sum((select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id))) as total
                from account_payment ap,sub_origin_resource s0
                where s0.id=ap.sub_origin_resource_id and ap.sub_origin_resource_id IS NOT NULL and ap.state in ('posted','reconciled') 
                and ap.partner_type='customer' and ap.payment_type = 'inbound'
                and s0.name in ('Servicios de educación Bancos (INS-RINS)','Servicios de educación Caja Gral.','Aspirantes',
                                'D.B.I.N.','D.P.Y.D.','Venta almacén','Licenciatarios','DEP en garantia',
                                'DGIRE-bancos','DGIRE-caja')
                group by year,sub_origin_resource_id,sub_origin_name,sub_origin_name_group_by,journal_id
                
                UNION ALL
                select -1 as id,NULL as sub_origin_resource_id,NULL as journal_id,
                '1) INGRESOS POR SERVICIOS DE EDUCACIÓN' as sub_origin_name,
                'Resumen' as sub_origin_name_group_by,
                'Resumen' as year,
                sum(case when extract(month from payment_date) = 1 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) january,
                sum(case when extract(month from payment_date) = 2 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) february,
                sum(case when extract(month from payment_date) = 3 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) march,
                sum(case when extract(month from payment_date) = 4 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) april,
                sum(case when extract(month from payment_date) = 5 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) may,
                sum(case when extract(month from payment_date) = 6 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) june,
                sum(case when extract(month from payment_date) = 7 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) july,
                sum(case when extract(month from payment_date) = 8 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) august,
                sum(case when extract(month from payment_date) = 9 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) september,
                sum(case when extract(month from payment_date) = 10 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) october,
                sum(case when extract(month from payment_date) = 11 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) november,
                sum(case when extract(month from payment_date) = 12 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) december,
                sum((select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id))) as total
                from sub_origin_resource s1,account_payment ap 
                where ap.sub_origin_resource_id = s1.id and ap.state in ('posted','reconciled')
                and s1.name in ('Servicios de educación Bancos (INS-RINS)','Servicios de educación Caja Gral.')

                UNION ALL
                select -2 as id,NULL as sub_origin_resource_id,NULL as journal_id,
                '2) ASPIRANTES' as sub_origin_name,
                'Resumen' as sub_origin_name_group_by,
                'Resumen' as year,
                sum(case when extract(month from payment_date) = 1 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) january,
                sum(case when extract(month from payment_date) = 2 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) february,
                sum(case when extract(month from payment_date) = 3 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) march,
                sum(case when extract(month from payment_date) = 4 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) april,
                sum(case when extract(month from payment_date) = 5 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) may,
                sum(case when extract(month from payment_date) = 6 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) june,
                sum(case when extract(month from payment_date) = 7 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) july,
                sum(case when extract(month from payment_date) = 8 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) august,
                sum(case when extract(month from payment_date) = 9 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) september,
                sum(case when extract(month from payment_date) = 10 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) october,
                sum(case when extract(month from payment_date) = 11 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) november,
                sum(case when extract(month from payment_date) = 12 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) december,
                sum((select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id))) as total
                from sub_origin_resource s1,account_payment ap 
                where ap.sub_origin_resource_id = s1.id and ap.state in ('posted','reconciled')
                and s1.name in ('Aspirantes')   

                UNION ALL
                select -3 as id,NULL as sub_origin_resource_id,NULL as journal_id,
                '   SUBTOTAL 1) +2)' as sub_origin_name,
                'Resumen' as sub_origin_name_group_by,
                'Resumen' as year,
                sum(case when extract(month from payment_date) = 1 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) january,
                sum(case when extract(month from payment_date) = 2 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) february,
                sum(case when extract(month from payment_date) = 3 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) march,
                sum(case when extract(month from payment_date) = 4 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) april,
                sum(case when extract(month from payment_date) = 5 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) may,
                sum(case when extract(month from payment_date) = 6 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) june,
                sum(case when extract(month from payment_date) = 7 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) july,
                sum(case when extract(month from payment_date) = 8 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) august,
                sum(case when extract(month from payment_date) = 9 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) september,
                sum(case when extract(month from payment_date) = 10 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) october,
                sum(case when extract(month from payment_date) = 11 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) november,
                sum(case when extract(month from payment_date) = 12 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) december,
                sum((select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id))) as total
                from sub_origin_resource s1,account_payment ap 
                where ap.sub_origin_resource_id = s1.id and ap.state in ('posted','reconciled')
                and s1.name in ('Aspirantes','Servicios de educación Bancos (INS-RINS)','Servicios de educación Caja Gral.')   

                UNION ALL
                select -4 as id,NULL as sub_origin_resource_id,NULL as journal_id,
                '3) DGIRE' as sub_origin_name,
                'Resumen' as sub_origin_name_group_by,
                'Resumen' as year,
                sum(case when extract(month from payment_date) = 1 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) january,
                sum(case when extract(month from payment_date) = 2 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) february,
                sum(case when extract(month from payment_date) = 3 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) march,
                sum(case when extract(month from payment_date) = 4 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) april,
                sum(case when extract(month from payment_date) = 5 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) may,
                sum(case when extract(month from payment_date) = 6 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) june,
                sum(case when extract(month from payment_date) = 7 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) july,
                sum(case when extract(month from payment_date) = 8 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) august,
                sum(case when extract(month from payment_date) = 9 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) september,
                sum(case when extract(month from payment_date) = 10 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) october,
                sum(case when extract(month from payment_date) = 11 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) november,
                sum(case when extract(month from payment_date) = 12 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) december,
                sum((select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id))) as total
                from sub_origin_resource s1,account_payment ap 
                where ap.sub_origin_resource_id = s1.id and ap.state in ('posted','reconciled')
                and s1.name in ('DGIRE-bancos','DGIRE-caja')   

                UNION ALL
                select -5 as id,NULL as sub_origin_resource_id,NULL as journal_id,
                '4) PATRIMONIALES' as sub_origin_name,
                'Resumen' as sub_origin_name_group_by,
                'Resumen' as year,
                sum(case when extract(month from payment_date) = 1 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) january,
                sum(case when extract(month from payment_date) = 2 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) february,
                sum(case when extract(month from payment_date) = 3 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) march,
                sum(case when extract(month from payment_date) = 4 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) april,
                sum(case when extract(month from payment_date) = 5 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) may,
                sum(case when extract(month from payment_date) = 6 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) june,
                sum(case when extract(month from payment_date) = 7 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) july,
                sum(case when extract(month from payment_date) = 8 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) august,
                sum(case when extract(month from payment_date) = 9 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) september,
                sum(case when extract(month from payment_date) = 10 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) october,
                sum(case when extract(month from payment_date) = 11 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) november,
                sum(case when extract(month from payment_date) = 12 then (select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id)) else 0 end) december,
                sum((select sum(amount_untaxed_signed) as amount from account_move where id in(select invoice_id from account_invoice_payment_rel where payment_id=ap.id))) as total
                from sub_origin_resource s1,account_payment ap 
                where ap.sub_origin_resource_id = s1.id and ap.state in ('posted','reconciled')
                and s1.name in ('D.B.I.N.','D.P.Y.D.','Venta almacén','Licenciatarios','DEP en garantia')                   
                            )'''% (self._table,) 
        )    

# group by item_id_first,item_id_second