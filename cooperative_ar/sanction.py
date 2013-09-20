#! -*- coding: utf8 -*-
from trytond.model import ModelView, ModelSQL, fields

__all__ = ['Sanction']

class Sanction(ModelSQL, ModelView):
    "cooperative_ar"
    __name__ = "cooperative.partner.sanction"
    date = fields.Date('Date')
    record = fields.Text('Record')
    response = fields.Text('Response')
    partner = fields.Many2One('cooperative.partner', 'Partner', required=True)
    type = fields.Selection([('atencion', u'Llamada de Atención'),
                             ('apercibimiento', u'Apercibimiento'),
                             ('exclusion', u'Exclusión'),
                            ], 'Tipo',
                             required=True)
