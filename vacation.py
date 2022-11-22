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
        ('licencia_examen', 'Licencia Examen'),
        ('licencia_medica', 'Licencia Médica'),
        ('licencia_paternidad', 'Licencia Paternidad / Maternidad'),
        ('otras', 'Otras Licencias'),
        ('vacaciones', 'Vacaciones'),
        ('licencia_rp', 'Licencia RP'),
        ], 'Tipo', required=True)

    @classmethod
    def __setup__(cls):
        super(Vacation, cls).__setup__()
        cls._order.insert(0, ('year', 'ASC'))
