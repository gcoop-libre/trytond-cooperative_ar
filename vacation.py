#! -*- coding: utf8 -*-
from trytond.model import ModelView, ModelSQL, fields

__all__ = ['Vacation']

class Vacation(ModelSQL, ModelView):
    "cooperative_ar"
    __name__ = "cooperative.partner.vacation"
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    days = fields.Integer('Days')
    partner = fields.Many2One('cooperative.partner', 'Partner', required=True)
    type = fields.Selection([('licencia_examen', u'Licencia Examen'),
                             ('licencia_medica', u'Licencia Médica'),
                             ('licencia_paternidad', u'Licencia Paternidad / Maternidad'),
                             ('otras', u'Otras Licencias'),
                             ('vacaciones', u'Vacaciones'),
                            ], u'Tipo',
                             required=True)

