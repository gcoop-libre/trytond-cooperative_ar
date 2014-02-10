#! -*- coding: utf8 -*-
#from decimal import Decimal
from trytond.model import ModelView, ModelSQL, fields

__all__ = ['Recibo']

class Recibo(ModelSQL, ModelView):
    "cooperative_ar"
    __name__ = "cooperative.partner.recibo"
    date = fields.Date('Fecha')
    monto = fields.Numeric('Monto',digits=(16,2))
    partner = fields.Many2One('cooperative.partner', 'Partner', required=True)
