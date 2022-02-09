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
import base64
import csv
import io
import os
from datetime import datetime
from odoo import fields, models, _

class SupplierRegistration(models.TransientModel):
    _name = 'supplier.registration'
    _description = 'Supplier Registration'

    
    journal_id = fields.Many2one('account.journal',string='Layout')
    
    fec_data = fields.Binary('FEC File', readonly=True, attachment=False)
    filename = fields.Char(string='Filename', size=256, readonly=True)

    def generate(self):
        partners = self.env['res.partner'].search(
            [('id', 'in', self._context.get('active_ids'))])
        if self.journal_id.supplier_registration_layout == 'banamex':
            filename = 'Banamex.txt'
            name = 'Banamex'
            contents = "1"
            contents += datetime.now().date().strftime('%d/%m/%Y')
            contents += "4198566"
            contents += "UNIVERSIDAD AUTONOMA DE MEXICO"
            contents += "\r\n"
            for partner in partners:
                if self.env.user.lang == 'es_MX':
                    contents += "Alta"
                else:    
                    contents += "High"
                if partner.bank_ids[:1].branch_number:
                    contents += str(partner.bank_ids[:1].branch_number).zfill(4)
                else:
                    contents += "    "
                if partner.bank_ids:
                    contents += partner.bank_ids[:1].acc_number.zfill(29)
                if partner.person_type:
                    if partner.person_type == 'physics':
                        contents += 'Fisica'
                    elif partner.person_type == 'moral':
                        contents += 'Moral '
                else:
                    contents += '      '
                partner_name = ''
                if partner.name:
                    partner_name = partner.name[:55]
                contents += partner_name.ljust(55) 
                contents += "999999999999"
                if self.env.user.lang == 'es_MX':
                    contents += "Diario"
                else:
                    contents += "daily"
                if partner.email:
                    if len(partner.email) > 30:
                        contents += partner.email[:30]
                    else:
                        contents += partner.email.ljust(30)
                else : 
                    contents += ''.ljust(30)
                if partner.phone:
                    if len(partner.phone) > 12:
                        contents += partner.phone[:12]
                    else:
                        contents += partner.phone.ljust(12)
                else : 
                    contents += ''.ljust(12)
                contents += "\r\n"

            gentextfile = base64.b64encode(bytes(contents, 'utf-8'))
            self.fec_data = gentextfile
            self.filename = filename
#                 if partner.bank_ids[:1].account_type:
#                     if partner.bank_ids[:1].account_type == 'checks':
#                         contents += "01"
#                         if partner.bank_ids[:1].branch_number:
#                             contents += str(partner.bank_ids[:1].branch_number).zfill(4)
#                     if partner.bank_ids[:1].account_type == 'card':
#                         contents += "03"
#                         if partner.bank_ids[:1].branch_number:
#                             contents += "0000"
#                     if partner.bank_ids[:1].account_type == 'master_acc':
#                         contents += "06"
#                         if partner.bank_ids[:1].branch_number:
#                             contents += "0000"
#                 if partner.bank_ids:
#                     contents += partner.bank_ids[:1].acc_number.zfill(20)
#                 if partner.currency_id:
#                     if partner.currency_id.name == 'MXN':
#                         contents += "001"
#                     if partner.currency_id.name == 'USD':
#                         contents += "005"
#                 contents += "000"
#                 contents += datetime.now().date().strftime('%d%m%y')
#                 contents += datetime.now().time().strftime('%H%M')
#                 contents += '\n\n'

        if self.journal_id.supplier_registration_layout == 'bbva':
            filename = 'BBVA Bancomer SIT.txt'
            name = 'BBVA Bancomer SIT'
            contents = 'H'
            contents += "001480758"
            contents += datetime.now().date().strftime('%d/%m/%Y')
            #====== Group ======#
            high_rec = partners.filtered(lambda x:x.instruction == 'high')
            low_rec = partners.filtered(lambda x:x.instruction == 'low')
            changes_rec = partners.filtered(lambda x:x.instruction == 'change')
            if high_rec:
                if self.env.user.lang == 'es_MX':
                    contents += 'ALTAS'.ljust(10)
                else:
                    contents += 'HIGH'.ljust(10)
            elif low_rec:
                if self.env.user.lang == 'es_MX':
                    contents += 'BAJAS'.ljust(10)
                else:
                    contents += 'LOW'.ljust(10)
            elif changes_rec:
                if self.env.user.lang == 'es_MX':
                    contents += 'CAMBIOS'.ljust(10)
                else:
                    contents += 'CHANGES'.ljust(10)
            else:
                contents += ''.ljust(10)

            if high_rec:
                if self.env.user.lang == 'es_MX':
                    contents += 'ALTAPROVEEDOR'.ljust(20)
                else:
                    contents += 'HIGH SUPPLIER'.ljust(20)
            elif low_rec:
                if self.env.user.lang == 'es_MX':
                    contents += 'BAJAPROVEEDOR'.ljust(20)
                else:
                    contents += 'LOW SUPPLIER'.ljust(20)
            elif changes_rec:
                if self.env.user.lang == 'es_MX':
                    contents += 'CAMBIOPROVEEDOR'.ljust(20)
                else:
                    contents += 'CHANGES SUPPLIER'.ljust(20)
            else:
                contents += ''.ljust(20)
                
            #====== Response Code =====#
            contents += '00'
            #====== Description Code Replay =====#
            contents +=  ''.ljust(20)
            #====== Filler =====#
            contents +=  ''.ljust(564)
            contents += "\r\n"
            
            no_of_record_high = 0
            no_of_record_low = 0
            no_of_record_change = 0
            
            for partner in partners:
                contents += 'D'
                
                if partner.instruction and partner.instruction=='high':
                    contents += 'A'
                    no_of_record_high+=1
                elif partner.instruction and partner.instruction=='low':
                    contents += 'B'
                    no_of_record_low += 1 
                elif partner.instruction and partner.instruction=='change':
                    contents += 'C'
                    no_of_record_change += 1
                else:
                    contents += ' '

                if partner.password_beneficiary:
                    if len(partner.password_beneficiary) > 30:
                        contents += partner.password_beneficiary[:30]
                    else:
                        contents += partner.password_beneficiary.ljust(30)
                else:
                    contents += ''.ljust(30)
                contents += 'N    '
                contents += 'MXP'
                contents += '99'
                if partner.bank_ids and partner.bank_ids[:1].acc_number:
                    contents += partner.bank_ids[:1].acc_number.zfill(35)
                else:
                    contents += ''.zfill(35)
                contents += '   '
                contents += '  '
                contents += ''.ljust(35)
                contents += '    '    
                contents += ''.ljust(11)
                contents += ''.ljust(9)
                contents += ''.ljust(20)
                contents += ''.ljust(15)
                contents += ''.ljust(10)
                contents += datetime.now().date().strftime('%Y-%m-%d')    
                if partner.person_type and partner.person_type=='physics':
                    contents += 'F'
                    contents += ''.ljust(50)
                    contents += ''.ljust(10)
                elif partner.person_type and partner.person_type=='moral':
                    contents += 'M'
                    if partner.name:
                        if len(partner.name) > 50:
                            contents += partner.name[:50]
                        else:
                            contents += partner.name.ljust(50)
                    else:
                        contents += ''.ljust(50)
                    contents += datetime.now().date().strftime('%Y-%m-%d')
                else:  
                    contents += ' '
                    contents += ''.ljust(50)
                    contents += ''.ljust(10)

                contents += ''.ljust(10)
                
                #=========Name of the partner =========

                if partner.person_type and partner.person_type=='physics':
                    #contents += partner.name.ljust(60)
                    if len(partner.name) > 60:
                        contents += partner.name[:60]
                    else:
                        contents += partner.name.ljust(60)
                elif partner.person_type and partner.person_type=='moral':
                    contents += ''.ljust(60)
                    # if len(partner.name) > 50:
                    #     contents += partner.name[:50]
                    # else:
                    #     contents += partner.name.ljust(50)
                else:
                    contents += ''.ljust(60)

                #=========Date Of birth =========

                if partner.person_type and partner.person_type=='physics':
                    if partner.dob:
                        contents += partner.dob.strftime('%Y-%m-%d')
                    else:
                        contents += ''.ljust(10)
                elif partner.person_type and partner.person_type=='moral':
                    contents += ''.ljust(10)
                elif not partner.person_type:
                    contents += ''.ljust(10)
                
                if partner.vat:
                    if len(partner.vat) > 15:
                        contents += partner.vat[:14]
                    else:
                        contents += partner.vat.ljust(14)
                else:
                    contents += ''.ljust(14)
                #===== Address=======#
                contents += ''.ljust(50)
                #===== Filler=======#
                contents += ''.ljust(8)
                #===== City=======#
                contents += ''.ljust(30)
                #===== Country=======#
                contents += ''.ljust(30)
                #===== Filler=======#
                contents += ''.ljust(35)
                #===== Key to company telephone=======#
                contents += ' '
                #===== Filler=======#
                contents += ''.ljust(39)
                
                #===== Confrimation Type=======#
                contents += '02'
                #======= Email =========#
                if partner.email:
                    if len(partner.email) > 50:
                        contents += partner.email[:50]
                    else:
                        contents += partner.email.ljust(50)
                else : 
                    contents += ''.ljust(50)
                #===== Code of replay =======#
                contents += '  '
                #=====Description of code=======#
                contents += ''.ljust(30)
                #===== Filler=======#
                contents += ''.ljust(8)
                contents += "\r\n"
            #====== Summary Data ===========#
            
            contents += 'T'
            #== Number of Records High ====#
            contents += str(no_of_record_high).zfill(10)
            #== Number of Records Low ====#
            contents += str(no_of_record_low).zfill(10)
            #== Number of Records Changes ====#
            contents += str(no_of_record_change).zfill(10)
            #== Number of Records rejected High ====#
            contents += '0000000000'
            #== Number of Records rejected Low ====#
            contents += '0000000000'
            #== Number of Records rejected Changes ====#
            contents += '0000000000'
            #=== Filler =====#
            contents += ''.ljust(575)
            contents += "\r\n"
            gentextfile = base64.b64encode(bytes(contents, 'utf-8'))
            self.fec_data = gentextfile
            self.filename = filename
#                 contents += "H000747289"
#                 contents += datetime.now().date().strftime('%Y-%m-%d')
#                 contents += "01"
#                 contents += "00                       "
#                 if partner.bank_ids[:1].acc_number:
#                     contents += partner.bank_ids[:1].acc_number.zfill(35)
#                 contents += "   "
#                 contents += "                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   "
#                 contents += "DAP"
#                 if partner.password_beneficiary:
#                     contents += partner.password_beneficiary
#                 contents += "PDA"
#                 contents += "00000000000000000000"
#                 contents += "000000000000000"
#                 contents += "               "
#                 contents += "                         "
#                 contents += "                                     "
#                 contents += "N          "
#                 contents += "                                  "
#                 contents += "                                       "
#                 contents += "                              "
#                 contents += "                                      "
#                 contents += "                            "
#                 if partner.currency_id:
#                     if partner.currency_id.name == 'MXN':
#                         contents += "MXN"
#                         if partner.bank_ids[:1].bic_swift:
#                             contents += partner.bank_ids[:1].bic_swift.zfill(11)
#                         
#                     if partner.currency_id.name == 'USD':
#                         contents += "USD"
#                         if partner.bank_ids[:1].aba:
#                             contents += partner.bank_ids[:1].aba.zfill(9)
#                     if partner.currency_id.name == 'EUR':
#                         contents += "EUR"
#                         if partner.bank_ids[:1].aba:
#                             contents += partner.bank_ids[:1].aba.zfill(9)
#                     if partner.currency_id.name == "CAD":
#                         contents += "CAD"
#                         if partner.bank_ids[:1].aba:
#                             contents += partner.bank_ids[:1].aba.zfill(9)
#                     if partner.currency_id.name == "CHF":
#                         contents += "CHF"
#                         if partner.bank_ids[:1].aba:
#                             contents += partner.bank_ids[:1].aba.zfill(9)
#                     if partner.currency_id.name == "SEK":
#                         contents += "SEK"
#                         if partner.bank_ids[:1].aba:
#                             contents += partner.bank_ids[:1].aba.zfill(9)
#                     if partner.currency_id.name == "GBP":
#                         contents += "GBP"
#                         if partner.bank_ids[:1].aba:
#                             contents += partner.bank_ids[:1].aba.zfill(9)
#                     if partner.currency_id.name == "JPY":
#                         contents += "JPY"
#                         if partner.bank_ids[:1].aba:
#                             contents += partner.bank_ids[:1].aba.zfill(9)
#                 contents += "FA"
#                 contents += "00000000000000001"
#                 if partner.email and len(partner.email) < 50:
#                     contents += partner.email.ljust(50)
#                 contents += "N000000000000"
#                 contents += "0001-01-010001-01-010001-01-01"
#                 contents += "N 0001-01-01700"
#                 contents += "                      "
#                 contents += "                              0001-01-01"
#                 contents += '\n\n'

        if self.journal_id.supplier_registration_layout == 'hsbc':
            name = 'HSBC'
            # with open('HSBC.csv', mode='w',newline='') as file:
            #     writer = csv.writer(file, delimiter=',',
            #                         quotechar='\"', quoting=csv.QUOTE_MINIMAL, lineterminator='\r\n')
            #     total_partner = len(partners)
            #     lst = []
            #     lst.append('AUTHBENEH')
            #     lst.append('ABCXXXXXXXX')
            #     date_today = 'MX-'+datetime.now().date().strftime('%d%m%Y')
            #     lst.append(date_today)
            #     file_sub_date = datetime.now().date().strftime('%Y:%m:%d')
            #     lst.append(file_sub_date)
            #     file_sub_time = datetime.now().time().strftime('%H:%M:%S')
            #     lst.append(file_sub_time)
            #     lst.append('             ')
            #     lst.append(total_partner+1)
            #     lst.append(total_partner)
            #     writer.writerow(tuple(lst))
            #
            #     for partner in partners:
            #         lst = []
            #         lst.append("BENEDET")
            #         if partner.password_beneficiary:
            #             lst.append(partner.password_beneficiary)
            #         else:
            #             lst.append("     ")
            #         lst.append(partner.name or '     ')
            #         lst.append('     ')
            #         lst.append('     ')
            #         lst.append('     ')
            #         lst.append('PPMX_MXOP')
            #         if partner.instruction and partner.instruction=='high':
            #             lst.append('A')
            #         elif partner.instruction and partner.instruction=='low':
            #             lst.append('D')
            #         else:
            #             lst.append(' ')
            #         lst.append('MX')
            #         if partner.bank_ids[:1].acc_number:
            #             lst.append(partner.bank_ids[:1].acc_number)
            #         else:
            #             lst.append(' ')
            #         lst.append('L')
            #         f_str= '021'
            #         lst.append(f_str)
            #         lst.append('BID')
            #         lst.append(' ')
            #         lst.append(' ')
            #         writer.writerow(tuple(lst))

            file_data = ''
            file_data +=str('AUTHBENEH')
            file_data += ','
            file_data +=str('ABCXXXXXXXX')
            file_data += ','
            total_partner = len(partners)
            date_today = 'MX-' + datetime.now().date().strftime('%d%m%Y')
            file_data +=str(date_today)
            file_data += ','
            file_sub_date = datetime.now().date().strftime('%Y:%m:%d')
            file_data +=str(file_sub_date)
            file_data += ','
            file_sub_time = datetime.now().time().strftime('%H:%M:%S')
            file_data +=str(file_sub_time)
            file_data += ','
            file_data +=str('             ')
            file_data += ','
            file_data +=str(total_partner + 1)
            file_data += ','
            file_data +=str(total_partner)
            file_data += ','
            file_data += "\r\n"

            for partner in partners:
                file_data +=str("BENEDET")
                file_data += ','
                if partner.password_beneficiary:
                    file_data +=str(partner.password_beneficiary)
                    file_data += ','
                else:
                    file_data +=str("     ")
                    file_data += ','
                file_data +=str(partner.name or '     ')
                file_data += ','
                file_data +=str('     ')
                file_data += ','
                file_data +=str('     ')
                file_data += ','
                file_data +=str('     ')
                file_data += ','
                file_data +=str('PPMX_MXOP')
                file_data += ','
                if partner.instruction and partner.instruction=='high':
                    file_data +=str('A')
                    file_data += ','
                elif partner.instruction and partner.instruction=='low':
                    file_data +=str('D')
                    file_data += ','
                else:
                    file_data +=str(' ')
                    file_data += ','
                file_data +=str('MX')
                file_data += ','
                if partner.bank_ids[:1].acc_number:
                    file_data +=str(partner.bank_ids[:1].acc_number)
                    file_data += ','
                else:
                    file_data +=str(' ')
                    file_data += ','
                file_data +=str('L')
                file_data += ','
                f_str= '021'
                file_data +=str(f_str)
                file_data += ','
                file_data +=str('BID')
                file_data += ','
                file_data +=str(' ')
                file_data += ','
                file_data +=str(' ')
                file_data += ','
                file_data += "\r\n"

            gentextfile = base64.b64encode(bytes(file_data,'utf-8'))
            print('file_data',file_data )

            self.write({
                'fec_data': gentextfile,
                'filename': 'HSBC.csv',
            })

        if self.journal_id.supplier_registration_layout == 'santander':
            filename = 'Santander.txt'
            name = 'Santander'
            contents = ""
            for partner in partners:
                contents += "SANTAN"
                acc_number = ''
                if partner.bank_ids[:1].acc_number:
                    acc_number = partner.bank_ids[:1].acc_number
                contents += acc_number.zfill(20)
                partner_name = ''
                if partner.name:
                    partner_name = partner.name
                contents += partner_name[:40].ljust(40)
                contents += '\r\n'

            gentextfile = base64.b64encode(bytes(contents, 'utf-8'))
            self.fec_data = gentextfile
            self.filename = filename

        if self.journal_id.supplier_registration_layout != 'hsbc':
            file_data = base64.b64decode(open(os.path.dirname(
                os.path.abspath(__file__)) + "/newfile.txt", "rb").read())
            content = io.StringIO(file_data.decode("utf-8")).read()
            content += contents
            self.fec_data = base64.b64encode(bytes(content, 'utf-8'))
            self.filename = self.filename

            self.write({
                'fec_data': base64.b64encode(content.encode('utf-8')),
                'filename': self.filename,
            })
        return {
            'name': (_('Supplier Registration')),
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.registration',
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': self.env.ref('jt_contact_base.supplier_registration_form_view').id,
            'target': 'new',
            'res_id': self.id,
        }

        # return {
        #     'name': name,
        #     'type': 'ir.actions.act_url',
        #     'url': "web/content/?model=supplier.registration&id=" + str(self.id) + "&filename_field=filename&field=fec_data&download=true&filename=" + self.filename,
        #     'target': 'self',
        # }
