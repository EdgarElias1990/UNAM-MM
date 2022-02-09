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
from odoo import models, fields,_
from odoo.exceptions import UserError, ValidationError
import base64
from datetime import datetime, timedelta
from odoo.tools.misc import formatLang, format_date, get_lang
from babel.dates import format_datetime, format_date

class GenerateBankLayoutEmployee(models.TransientModel):

    _name = 'generate.bank.layout.employee'
    _description = 'Generate Bank Layout Employee'

    journal_id = fields.Many2one('account.journal','Select the file to generate')
    employee_ids = fields.Many2many('hr.employee','hr_employee_bank_layout_rel','bank_layout_id','emp_id','Employee')
    file_name = fields.Char('Filename')
    file_data = fields.Binary('Download')

    def action_generate_bank_layout(self):
        active_ids = self.env.context.get('active_ids')
        if not active_ids:
            return ''
        
        return {
            'name': _('Generate Bank Layout'),
            'res_model': 'generate.bank.layout.employee',
            'view_mode': 'form',
            'view_id': self.env.ref('jt_payroll_payment.view_generate_bank_layout_employee').id,
            'context': {'default_employee_ids':[(6,0,active_ids)]},
            'target': 'new',
            'type': 'ir.actions.act_window',
        }    
        

    def banorte_file_format(self):
        file_data = ''
        file_name = 'NI2005201.txt'

        #==== Registration Type ======#
        file_data += 'H'
        #====== Service Code =======#
        file_data += 'NE'
        #===== Promoter ======#
        file_data += '00000000'
        #===== Company Identification ======#
        file_data += '20052'
        #==== Company name =======#
        file_data += "".ljust(40)
        #===== Consecutive ======#
        file_data += "01"
        #===== Total Emp =====#
        total_emp = len(self.employee_ids)
        file_data += str(total_emp).zfill(6)
        #===== Filler =======#
        file_data += "".ljust(283)
        file_data += "\r\n"
        for emp in self.employee_ids:
            #=====Type Record =====#
            file_data += 'D'
            #====== Emp Number =====#
            emp_number = ''
            if emp.worker_number:
                emp_number = emp.worker_number
            file_data += emp_number.zfill(10)  
            #==== Emp Name======#
            emp_name= ''
            if emp.name:
                emp_name = emp.name
            file_data += emp_name.ljust(60)  
            #===== Dependncy =======#
            file_data += '     '
            #==== occ_code =====#
            occ_code = '00'
            if emp.occ_code:
                if emp.occ_code =='commerce':
                    occ_code = '01'
                elif emp.occ_code =='drivers':
                    occ_code = '02'
                elif emp.occ_code =='admin_worker':
                    occ_code = '03'
                elif emp.occ_code =='edu_workers':
                    occ_code = '04'
                elif emp.occ_code =='trab_del':
                    occ_code = '05'
                elif emp.occ_code =='prot_serve':
                    occ_code = '06'
                elif emp.occ_code =='fab_worker':
                    occ_code = '08'
                elif emp.occ_code =='technician':
                    occ_code = '09'
                elif emp.occ_code =='salaried_proff':
                    occ_code = '10'
                elif emp.occ_code =='independent_proff':
                    occ_code = '11'
                elif emp.occ_code =='public_off':
                    occ_code = '12'
                elif emp.occ_code =='private_off':
                    occ_code = '13'
                elif emp.occ_code =='pensioner':
                    occ_code = '18'
            file_data += occ_code 
            #==== Empl Name =======#
            emp_name = ''
            if emp.name and len(emp.name) > 19:
                emp_name = emp.name[:19]
            elif emp.name:
                emp_name = emp.name
            file_data += emp_name.ljust(19)
            #=== road type =======#
            type_road = '  '
            if emp.road:
                if emp.road == 'old_road':
                    type_road = 'AC'
                elif emp.road == 'andador':
                    type_road = 'AN'
                elif emp.road == 'highway':
                    type_road = 'AU'
                elif emp.road == 'avenue':
                    type_road = 'AV'
                elif emp.road == 'boulevard':
                    type_road = 'BO'
                elif emp.road == 'street':
                    type_road = 'CA'
                elif emp.road == 'closed':
                    type_road = 'CD'
                elif emp.road == 'circuit':
                    type_road = 'CI'
                elif emp.road == 'alley_road':
                    type_road = 'CJ'
                elif emp.road == 'camino':
                    type_road = 'CM'
                elif emp.road == 'high_road':
                    type_road = 'CR'
                elif emp.road == 'calzada':
                    type_road = 'CZ'
                elif emp.road == 'glorieta':
                    type_road = 'GL'
                elif emp.road == 'Paseo':
                    type_road = 'PA'
                elif emp.road == 'prolongation':
                    type_road = 'PR'
                elif emp.road == 'private':
                    type_road = 'PV'
                elif emp.road == 'return':
                    type_road = 'RE'
                elif emp.road == 'valle':
                    type_road = 'VA'
                elif emp.road == 'via':
                    type_road = 'VI'
                elif emp.road == 'villa':
                    type_road = 'VL'
            file_data += type_road
            #====== Street ======#
            street1 = ''
            if emp.street:
                if len(emp.street) > 24:
                    street1 = emp.street[:24]
                else:    
                    street1 = emp.street
            file_data += street1.ljust(24)
            #======= Street2 =======#
            street2 = ''
            if emp.street2:
                if len(emp.street2) > 7:
                    street2 = emp.street2[:7]
                else:    
                    street2 = emp.street2
            file_data += street2.zfill(7)
            #====== housing =====#
            housing = '00'
            if emp.housing:
                if emp.housing == 'house':
                    housing = '01'
                elif emp.housing == 'building':
                    housing = '02'
                elif emp.housing == 'department':
                    housing = '03'
                elif emp.housing == 'housing_unit':
                    housing = '04'
                elif emp.housing == 'market':
                    housing = '05'
                    
            file_data += housing
            #===== Entry ======#
            file_data += '  ' 
            #===== Floor ======#
            file_data += '  ' 
            #===== Department ======#
            file_data += '    ' 
            #===== colonia=======#
            colonia = ''
            if emp.colonia:
                colonia = emp.colonia
            file_data += colonia.ljust(40)
            
            #==== City =======#
            city = ''
            if emp.city:
                if len(emp.city) > 3:
                    city = emp.city[:3]
                else:
                    city = emp.city
            file_data += city.ljust(3)
            #===== State =======#
            state_code = '00'
            if emp.state_id:
                if emp.state_id.code == 'DIF':
                    state_code = '01'
                elif emp.state_id.code == 'AGU':
                    state_code = '02'
                elif emp.state_id.code == 'BCN':
                    state_code = '03'
                elif emp.state_id.code == 'BCS':
                    state_code = '04'
                elif emp.state_id.code == 'CAM':
                    state_code = '05'
                elif emp.state_id.code == 'COA':
                    state_code = '06'
                elif emp.state_id.code == 'COL':
                    state_code = '07'
                elif emp.state_id.code == 'CHP':
                    state_code = '08'
                elif emp.state_id.code == 'DUR':
                    state_code = '10'
                elif emp.state_id.code == 'GUA':
                    state_code = '11'
                elif emp.state_id.code == 'GRO':
                    state_code = '12'
                elif emp.state_id.code == 'HID':
                    state_code = '13'
                elif emp.state_id.code == 'JAL':
                    state_code = '14'
                elif emp.state_id.code == 'MEX':
                    state_code = '15'
                elif emp.state_id.code == 'MIC':
                    state_code = '16'
                elif emp.state_id.code == 'MOR':
                    state_code = '17'
                elif emp.state_id.code == 'NAY':
                    state_code = '18'
                elif emp.state_id.code == 'NLE':
                    state_code = '19'
                elif emp.state_id.code == 'OAX':
                    state_code = '20'
                elif emp.state_id.code == 'PUE':
                    state_code = '21'
                elif emp.state_id.code == 'QUE':
                    state_code = '22'
                elif emp.state_id.code == 'ROO':
                    state_code = '23'
                elif emp.state_id.code == 'SLP':
                    state_code = '24'
                elif emp.state_id.code == 'SIN':
                    state_code = '25'
                elif emp.state_id.code == 'SON':
                    state_code = '26'
                elif emp.state_id.code == 'TAB':
                    state_code = '27'
                elif emp.state_id.code == 'TAM':
                    state_code = '28'
                elif emp.state_id.code == 'TLA':
                    state_code = '29'
                elif emp.state_id.code == 'VER':
                    state_code = '30'
                elif emp.state_id.code == 'YUC':
                    state_code = '31'
                elif emp.state_id.code == 'ZAC':
                    state_code = '32'
                else:
                    state_code = '33'
            file_data += state_code
            #=== Postal Code======#
            postal_code = ''
            if emp.zip_code:
                postal_code = emp.zip_code
            file_data += postal_code.ljust(5)
            #==== Telephone =========#
            file_data += "".ljust(12) 
            #=== Gender =======#
            gender = ' '
            if emp.gender and emp.gender=='male':
                gender = 'M'
            if emp.gender and emp.gender=='female':
                gender = 'F'    
            file_data += gender
            #==== Date of birth ======#
            dob = '        '
            if emp.birthday:
                currect_time = emp.birthday
                file_data +=str(currect_time.year)
                file_data +=str(currect_time.month).zfill(2)
                file_data +=str(currect_time.day)
            else:
                file_data += dob
                
            #======= Nationality =======#
            nationality = '   '
            if emp.nationality:
                if emp.nationality == 'mexican':
                    nationality = '001'
                elif emp.nationality == 'north_american':
                    nationality = '002'
                elif emp.nationality == 'lebanese':
                    nationality = '004'
                elif emp.nationality == 'south_american':
                    nationality = '005'
                elif emp.nationality == 'american_central':
                    nationality = '006'
                elif emp.nationality == 'europe':
                    nationality = '007'
                elif emp.nationality == 'israelite':
                    nationality = '008'
                elif emp.nationality == 'japanese':
                    nationality = '009'
                elif emp.nationality == 'canadian':
                    nationality = '010'
                elif emp.nationality == 'other':
                    nationality = '099'
            file_data += nationality
            #==== Marital status ======#
            marital_status = ' '
            if emp.marital:
                if emp.marital == 'single':
                    marital_status = 'S'
                elif emp.marital == 'married':
                    marital_status = 'C'
                elif emp.marital == 'divorced':
                    marital_status = 'D'
                elif emp.marital == 'free_union':
                    marital_status = 'U'
                elif emp.marital == 'widower':
                    marital_status = 'V'
                elif emp.marital == 'separate':
                    marital_status = 'X'
            file_data += marital_status
            #===== Marriage Regime ======#
            file_data += ' '
            #====== Schooling =======#
            schooling = '000'
            if emp.certificate:
                if emp.certificate == 'without_school':
                    schooling = '001'
                elif emp.certificate == 'primary':
                    schooling = '002'
                elif emp.certificate == 'secondary':
                    schooling = '003'
                elif emp.certificate == 'preparatory':
                    schooling = '004'
                elif emp.certificate == 'career_tech':
                    schooling = '005'
                elif emp.certificate == 'bachelor':
                    schooling = '006'
                elif emp.certificate == 'diploma':
                    schooling = '007'
                elif emp.certificate == 'master':
                    schooling = '008'
                elif emp.certificate == 'other':
                    schooling = '009'
                elif emp.certificate == 'not_school':
                    schooling = '099'
            file_data += schooling
            #===== Professional Title ======#
            professional_title = '   '
            if emp.certificate and emp.profession and emp.certificate == 'bachelor':
                if emp.profession =='phy_anthropologist':
                    professional_title = '605'
                elif emp.profession =='soc_anthropologist':
                    professional_title = '606'
                elif emp.profession =='architect':
                    professional_title = '701'
                elif emp.profession =='biologist':
                    professional_title = '604'
                elif emp.profession =='cardinal':
                    professional_title = '862'
                elif emp.profession =='dental':
                    professional_title = '406'
                elif emp.profession =='accountant':
                    professional_title = '502'
                elif emp.profession =='ethnologist':
                    professional_title = '603'
                elif emp.profession =='physicist':
                    professional_title = '602'
                elif emp.profession =='physicist_math':
                    professional_title = '601'
                elif emp.profession =='general':
                    professional_title = '870'
                elif emp.profession =='lieutenant':
                    professional_title = '871'
                elif emp.profession =='engineer':
                    professional_title = '156'
                elif emp.profession =='licensed':
                    professional_title = '315'
                elif emp.profession =='doctor':
                    professional_title = '410'
                elif emp.profession =='professor':
                    professional_title = '8140'
            file_data += professional_title
            #=== Type of Employee =====#
            type_of_emp = '00'
            if emp.worker_type and emp.worker_type == 'base':
                type_of_emp = '03'
            if emp.worker_type and emp.worker_type == 'trust':
                type_of_emp = '10'
            file_data += type_of_emp
            #===== RFC =========#
            rfc = ''
            if emp.rfc:
                rfc = emp.rfc
            file_data += rfc.ljust(13)
            #====== CURP=======# 
            file_data += ''.ljust(18)
            #===== Type Of Reg =======#
            file_data += '01'
            #===== Card Type =======#
            file_data += '1'
            #====== Debit Card Number=======# 
            file_data += ''.ljust(16)
            #===== Sccount Product Key =====#
            file_data += '0360'
            #===== Account Bank Code =====#
            file_data += '072'
            #==== Accont type =====#
            account_type = '00'
            if emp.bank_ids and emp.bank_ids[:1].account_type:
                if emp.bank_ids[:1].account_type =='checks':
                    account_type = '01'
                elif emp.bank_ids[:1].account_type =='card':
                    account_type = '03'
                elif emp.bank_ids[:1].account_type =='clabe_acc':
                    account_type = '40'
            file_data += account_type
            
            #==== Account Number ======#
            file_data += "".ljust(18)
            #=== CR Checkbook ======#
            file_data += "".ljust(4)
            #=== Contract Printing ======#
            file_data += "S"
            #==== Emp Salary ======#
            file_data += "".ljust(15)
            #==== Card Number ======#
            file_data += "".ljust(16)
            #==== Filler ======#
            file_data += "".ljust(10)
            
            file_data +="\r\n"
            
        gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
        self.file_data = gentextfile
        self.file_name = file_name
        
    def generate_bank_layout(self):
        if self.journal_id.payroll_beneficiaries_bank_format == 'BANORTE':
            self.banorte_file_format()

        return {
            'name': _('Generate Bank Layout'),
            'res_model': 'generate.bank.layout.employee',
            'res_id' : self.id,
            'view_mode': 'form',
            'target': 'new',
            'type': 'ir.actions.act_window',
        }    
        
