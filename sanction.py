#! -*- coding: utf8 -*-
# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields

__all__ = ['Sanction']


class Sanction(ModelSQL, ModelView):
    'Cooperative sanction'
    __name__ = 'cooperative.partner.sanction'

    date = fields.Date('Date')
    record = fields.Text('Record')
    response = fields.Text('Response')
    partner = fields.Many2One('cooperative.partner', 'Partner', required=True)
    type = fields.Selection([
        ('atencion', 'Llamada de Atención'),
        ('apercibimiento', 'Apercibimiento'),
        ('exclusion', 'Exclusión'),
        ], 'Tipo', required=True)
