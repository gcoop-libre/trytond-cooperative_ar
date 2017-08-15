#! -*- coding: utf8 -*-
# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields

__all__ = ['Vacation']


class Vacation(ModelSQL, ModelView):
    'Cooperative vacation'
    __name__ = 'cooperative.partner.vacation'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    days = fields.Integer('Days')
    year = fields.Char('Year')
    partner = fields.Many2One('cooperative.partner', 'Partner', required=True)
    type = fields.Selection([
        ('licencia_examen', u'Licencia Examen'),
        ('licencia_medica', u'Licencia Médica'),
        ('licencia_paternidad', u'Licencia Paternidad / Maternidad'),
        ('otras', u'Otras Licencias'),
        ('vacaciones', u'Vacaciones'),
        ], 'Tipo', required=True)
