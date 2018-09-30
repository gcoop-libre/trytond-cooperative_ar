#! -*- coding: utf8 -*-
# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval

__all__ = ['Meeting']

STATES = {'required': Eval('status') == 'complete'}


class Meeting(ModelSQL, ModelView):
    'Meeting'
    __name__ = 'cooperative.meeting'

    type = fields.Selection([
        ('ordinaria', 'Ordinaria'),
        ('extraordinaria', 'Extraordinaria'),
        ('reunion', 'Reunion de Consejo'),
        ], 'Type', required=True)
    status = fields.Selection([
        ('planned', 'Planned'),
        ('complete', 'Complete'),
        ], 'Status', required=True)
    start_date = fields.Date('Start Date', states=STATES)
    start_time = fields.Time('Start Time', states=STATES)
    end_time = fields.Time('End Time', states=STATES)
    partners = fields.Many2Many('cooperative.partner-meeting',
                                'meeting', 'partner',
                                'Partner', domain=[
                                ('status', '=', 'active'),
                                ])

    record = fields.Text('Record',
                         states=STATES,
                        )
