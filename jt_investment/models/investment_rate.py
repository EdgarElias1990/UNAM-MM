from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import requests
import urllib.request
import json
from odoo.exceptions import ValidationError,UserError
from odoo.tools.misc import ustr

class InvestmentPeriodRate(models.Model):

    _name = 'investment.period.rate'
    _description = "Investment Rate"
    _rec_name = 'rate_date'
    _order = 'rate_date'
    
    rate_date = fields.Date(string='Date',default=datetime.today())
    product_type = fields.Selection([('TIIE','TIIE'),('CETES','CETES'),('UDIBONOS','UDIBONOS'),('BONUS','BONUS'),
                                     ('PAGARE','PAGARE')],string="Product Type")
    rate_daily = fields.Float(string="Daily Rate",digits=0)
    rate_days_28 = fields.Float(string="28 Days",digits='CETES')
    term_days_28 = fields.Integer(string="Term 28 Days")
    rate_days_91 = fields.Float(string="91 Days",digits='CETES')
    term_days_91 = fields.Integer(string="Term 91 Days")
    rate_days_182 = fields.Float(string="182 Days",digits='CETES')
    term_days_182 = fields.Integer(string="Term 182 Days")
    rate_days_364 = fields.Float(string="364 Days",digits='CETES')
    term_days_364 = fields.Integer(string="Term 364 Days")

    #=====UDIBONOS=====#    
    rate_year_3 = fields.Float(string="3 Year Rate",digits='UDIBONOS')
    term_year_3 = fields.Integer(string="3 Year Term")
    rate_year_5 = fields.Float(string="5 Year Rate",digits='UDIBONOS')
    term_year_5 = fields.Integer(string="5 Year Term")
    rate_year_10 = fields.Float(string="10 Year Rate",digits='UDIBONOS')
    term_year_10 = fields.Integer(string="10 Year Term")
    rate_year_20 = fields.Float(string="20 Year Rate",digits='UDIBONOS')
    term_year_20 = fields.Integer(string="20 Year Term")
    rate_year_30 = fields.Float(string="30 Year Rate",digits='UDIBONOS')
    term_year_30 = fields.Integer(string="30 Year Term")
    
    #========BONUS=====#
    rate_year_7 = fields.Float(string="7 Year Rate",digits='BONDS')
    term_year_7 = fields.Integer(string="7 Year Term")
    
    _sql_constraints = [('rate_date_product_type', 'unique(rate_date,product_type)',
                         'Rate already register for this date')]
    
#     def get_rates(self):
#         domain = []
#         views = []
#         
#         if self.env.context and self.env.context.get('default_product_type',False):
#             if self.env.context.get('default_product_type',False) == 'CETES':
#                 domain = [('product_type', '=', 'CETES')]
#                 views = [(self.env.ref("jt_investment.investment_period_rate_cetes_tree").id, 'tree'), (self.env.ref("jt_investment.investment_period_rate_cetes_form").id, 'form')]
#                 
#  
#         return {
#                 'name': 'Rates',
#                 'view_type': 'form',
#                 'view_mode': 'tree,form',
#                 'views': views,
#                 'res_model': 'investment.period.rate',
#                 'domain': domain,
#                 'type': 'ir.actions.act_window',
#             }

        
    def set_blank_fields(self):
        self.rate_daily = 0
        self.rate_days_28 = 0
        self.term_days_28 = 0
        self.rate_days_91 = 0
        self.term_days_91 = 0
        self.rate_days_182 = 0
        self.term_days_182 = 0
        self.rate_days_364 = 0
        self.term_days_364 = 0
    
        #=====UDIBONOS=====#    
        self.rate_year_3 = 0
        self.term_year_3 = 0
        self.rate_year_5 = 0
        self.term_year_5 = 0
        self.rate_year_10 = 0
        self.term_year_10 = 0
        self.rate_year_20 = 0
        self.term_year_20 = 0
        self.rate_year_30 = 0
        self.term_year_30 = 0
        
        #========BONUS=====#
        self.rate_year_7 = 0
        self.term_year_7 = 0

    @api.onchange('rate_date')
    def onchange_rate_date(self):
        self.set_blank_fields()
        if self.rate_date and self.product_type:
            token = 'fccfd1e45c7e54ef7a6896f25f7dcf01d51cfa033424abd345707b6a8d2b59c3'
            url = 'https://www.banxico.org.mx/SieAPIRest/service/v1/series/'
            
            # url +=  series_str+"/datos/oportuno?token=%s"%token
            date_range = self.rate_date
            date_range = datetime.strftime(date_range,'%Y-%m-%d')
            date_range = date_range+"/"+date_range
            
            if self.product_type=='TIIE':
                self.with_context(call_from_onchange=True).get_investment_product_rate(token,url,date_range)
            elif self.product_type=='CETES':
                self.with_context(call_from_onchange=True).get_cetes_product_rate(token,url,date_range)
            elif self.product_type=='UDIBONOS':
                self.with_context(call_from_onchange=True).get_UDIBONOS_product_rate(token,url,date_range)
            elif self.product_type=='BONUS':
                self.with_context(call_from_onchange=True).get_BONUS_product_rate(token,url,date_range)
            elif self.product_type=='PAGARE':    
                self.with_context(call_from_onchange=True).get_PAGARE_product_rate(token,url,date_range)

            
    def create_update_product_rate(self,product_type,series_fields_map,series_fields_type_map,data):
        idSerie = data.get('idSerie',False)
        date_data = data.get('datos',[])
        if idSerie and date_data:
            field_name = series_fields_map.get(idSerie,False)
            field_type = series_fields_type_map.get(idSerie,False)
            
            for line in date_data:
                rec_date = line.get('fecha',False)
                rec_date = datetime.strptime(rec_date, '%d/%m/%Y')
                rate = line.get('dato',0.0)
                if rate.isnumeric():
                    rate = float(rate)
                if rate == 'N/E':
                    rate = str(0)
                if isinstance(rate,str):
                    rate = rate.replace(',','')
                if field_type=='int':
                    rate = int(rate)
                elif field_type=='float':
                    rate = float(rate)
                else:
                    rate = 0
                
                if self.env.context and self.env.context.get('call_from_onchange'):
                    self.write({field_name : rate})
                else:
                    exist_rec = self.env['investment.period.rate'].search([('product_type','=',product_type),('rate_date','=',rec_date)],limit=1)
                    if exist_rec:
                        exist_rec.write({field_name : rate})
                    else:
                        vals = {'product_type':product_type,
                                'rate_date':rec_date,
                                field_name : rate,
                                }
                        self.env['investment.period.rate'].create(vals)
                    
                  
    def get_investment_product_rate(self,token,url,date_range):
        series_fields_map = {'SF331451':'rate_daily','SF43783':'rate_days_28','SF43878':'rate_days_91','SF111916':'rate_days_182'}
        series_fields_type_map = {'SF331451':'float','SF43783':'float','SF43878':'float','SF111916':'float'}
        series_str = 'SF331451,SF43783,SF43878,SF111916'
        url +=  series_str+"/datos/%s?token=%s"%(date_range,token)

        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req).read()
        response = json.loads(response.decode('utf-8'))
        if response.get('bmx',False):
            series_dict = response.get('bmx',False)
            for data in series_dict.get('series',[]):
                self.create_update_product_rate('TIIE', series_fields_map,series_fields_type_map, data)

    def get_cetes_product_rate(self,token,url,date_range):
        #=======link=======#
        #=====  https://www.banxico.org.mx/SieAPIRest/service/v1/doc/catalogoSeries#    ====#
        series_fields_map = {'SF43935':'term_days_28','SF43936':'rate_days_28',
                             'SF43938':'term_days_91','SF43939':'rate_days_91',
                             'SF43941':'term_days_182','SF43942':'rate_days_182',
                             'SF43944':'term_days_364','SF43945':'rate_days_364'
                             }

        series_fields_type_map = {'SF43935':'int','SF43936':'float',
                             'SF43938':'int','SF43939':'float',
                             'SF43941':'int','SF43942':'float',
                             'SF43944':'int','SF43945':'float'
                             }
        
        series_str = 'SF43935,SF43936,SF43938,SF43939,SF43941,SF43942,SF43944,SF43945'
        
        url +=  series_str+"/datos/%s?token=%s"%(date_range,token)

        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req).read()
        response = json.loads(response.decode('utf-8'))
        if response.get('bmx',False):
            series_dict = response.get('bmx',False)
            for data in series_dict.get('series',[]):
                self.create_update_product_rate('CETES', series_fields_map,series_fields_type_map, data)
        

    def get_UDIBONOS_product_rate(self,token,url,date_range):
        #=======link=======#
        #=====  https://www.banxico.org.mx/SieAPIRest/service/v1/doc/catalogoSeries#    ====#

        series_fields_map = {'SF61593':'term_year_3','SF61592':'rate_year_3',
                             'SF43926':'term_year_5','SF43927':'rate_year_5',
                             'SF43923':'term_year_10','SF43924':'rate_year_10',
                             'SF46957':'term_year_20','SF46958':'rate_year_20',
                             'SF46960':'term_year_30','SF46961':'rate_year_30',
                             }
        series_fields_type_map = {'SF61593':'int','SF61592':'float',
                             'SF43926':'int','SF43927':'float',
                             'SF43923':'int','SF43924':'float',
                             'SF46957':'int','SF46958':'float',
                             'SF46960':'int','SF46961':'float',
                             }
        
        series_str = 'SF61593,SF61592,SF43926,SF43927,SF43923,SF43924,SF46957,SF46958,SF46960,SF46961'
        
        url +=  series_str+"/datos/%s?token=%s"%(date_range,token)

        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req).read()
        response = json.loads(response.decode('utf-8'))
        if response.get('bmx',False):
            series_dict = response.get('bmx',False)
            for data in series_dict.get('series',[]):
                self.create_update_product_rate('UDIBONOS', series_fields_map,series_fields_type_map, data)

    def get_BONUS_product_rate(self,token,url,date_range):
        #=======link=======#        
        #=====  https://www.banxico.org.mx/SieAPIRest/service/v1/doc/catalogoSeries#    ====#

        series_fields_map = {'SF43882':'term_year_3','SF43883':'rate_year_3',
                             'SF43885':'term_year_5','SF43886':'rate_year_5',
                             'SF44945':'term_year_7','SF44946':'rate_year_7',
                             'SF44070':'term_year_10','SF44071':'rate_year_10',
                             'SF45383':'term_year_20','SF45384':'rate_year_20',
                             'SF60689':'term_year_30','SF60696':'rate_year_30',
                             }
        series_fields_type_map = {'SF43882':'int','SF43883':'float',
                             'SF43885':'int','SF43886':'float',
                             'SF44945':'int','SF44946':'float',
                             'SF44070':'int','SF44071':'float',
                             'SF45383':'int','SF45384':'float',
                             'SF60689':'int','SF60696':'float',
                             }
        
        series_str = 'SF43882,SF43883,SF43885,SF43886,SF44945,SF44946,SF44070,SF44071,SF45383,SF45384,SF60689,SF60696'
        
        url +=  series_str+"/datos/%s?token=%s"%(date_range,token)

        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req).read()
        response = json.loads(response.decode('utf-8'))
        if response.get('bmx',False):
            series_dict = response.get('bmx',False)
            for data in series_dict.get('series',[]):
                self.create_update_product_rate('BONUS', series_fields_map,series_fields_type_map, data)   

    def get_PAGARE_product_rate(self,token,url,date_range):
        series_fields_map = {'SF331451':'rate_daily','SF43783':'rate_days_28','SF43878':'rate_days_91','SF111916':'rate_days_182'}
        series_fields_type_map = {'SF331451':'float','SF43783':'float','SF43878':'float','SF111916':'float'}
        series_str = 'SF331451,SF43783,SF43878,SF111916'
        
        url +=  series_str+"/datos/%s?token=%s"%(date_range,token)

        req = urllib.request.Request(url)
        response = urllib.request.urlopen(req).read()
        response = json.loads(response.decode('utf-8'))
        if response.get('bmx',False):
            series_dict = response.get('bmx',False)
            for data in series_dict.get('series',[]):
                self.create_update_product_rate('PAGARE', series_fields_map,series_fields_type_map, data)
                      
    def create_investment_period_rate(self):
        token = 'fccfd1e45c7e54ef7a6896f25f7dcf01d51cfa033424abd345707b6a8d2b59c3'
        url = 'https://www.banxico.org.mx/SieAPIRest/service/v1/series/'
        
        # url +=  series_str+"/datos/oportuno?token=%s"%token
        date_range = datetime.now()
        date_range = datetime.strftime(date_range,'%Y-%m-%d')
        final_date_range = datetime.now()+relativedelta(years=1)
        final_date_range = datetime.strftime(final_date_range,'%Y-%m-%d')
        
        date_range = date_range+"/"+final_date_range
        
        self.get_investment_product_rate(token,url,date_range)
        self.get_cetes_product_rate(token,url,date_range)
        self.get_UDIBONOS_product_rate(token,url,date_range)
        self.get_BONUS_product_rate(token,url,date_range)
        self.get_PAGARE_product_rate(token,url,date_range)
                