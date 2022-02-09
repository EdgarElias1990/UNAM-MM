
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CustomPayrollProcessing(models.Model):
    _inherit = 'payment.batch.supplier'
    #Genera campo computado que despliga la quincena según la lógica de las líneas de protección de cheques
    fornight = fields.Selection([('01', '01'), ('02', '02'), ('03', '03'), ('04', '04'), ('05', '05'),
                                 ('06', '06'), ('07', '07'), ('08', '08'), ('09', '09'), ('10', '10'),
                                 ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'),
                                 ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20'),
                                 ('21', '21'), ('22', '22'), ('23', '23'), ('24', '24')],
                                string="Fornight", compute='_compute_fornight')


    def _compute_fornight(self):
        #print (self.type_of_batch)
        self.fornight = ''
        #Aplica lógica sólo a protección de cheques de tipo nómina
        if self.type_of_batch == 'nominal':
            nulos = 0
            counter = 0
            unico = []
            
            #instancia el conjunto de líneas de la protección concurrente
            lineas = self.env['check.payment.req'].search([('payment_batch_id', '=', self.id)])

            for pago in lineas:
                counter += 1
                if pago.payment_id.fornight:
                    quincena = pago.payment_id.fornight
                    #print(pago.payment_id.fornight)
                    #lista de las quincenas existentes en el conjunto de pagos
                    if quincena not in unico:
                        unico.append(quincena)
                else:
                    nulos += 1

            # print('id Protección: ' + str(self.id))
            # print('counter: ' + str(counter))
            # print('nulos: ' + str(nulos))
            # print('quincenas: ' + str(unico))
            # print('unico: ' + str(len(unico)))

            #si no hay nulos y todas las quincenas son igules
            if nulos == 0 and len(unico) == 1:
                self.fornight = quincena
