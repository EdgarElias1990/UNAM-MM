from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import re   # libreria para realizar comparaciones de strings

class OperationType(models.Model):
    _inherit = 'operation.type'

    def unlink(self):   #Creación de función para eliminar campos

        for ac in self:
            # Busqueda de elementos coincidentes con el domino dado
            a = self.env["account.move"].search([('upa_key','=',ac.upa_catalog_policy_id.id),
                                                 ('document_type','=',ac.currency_type)])
            for i in range(len(a)):

                lista = re.findall(ac.name, a[i].operation_type_id.name)    #Validacion de coincidencias entre las cadenas

                if lista:
                    raise UserError(_("Operacion de Solicitud en Uso"))     #mensaje de error si la lista no se encuentra vacia
                    break

        return super(OperationType, self).unlink()