# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval
from trytond.report import Report

__all__ = ['Meeting', 'MeetingReport']

STATES = {'required': Eval('status') == 'complete'}


class Meeting(ModelSQL, ModelView):
    'Meeting'
    __name__ = 'cooperative.meeting'

    _states = {'required': Eval('status') == 'complete'}

    type = fields.Selection([
        ('ordinaria', 'Ordinaria'),
        ('extraordinaria', 'Extraordinaria'),
        ('reunion', 'Reunion de Consejo'),
        ], 'Type', required=True)
    status = fields.Selection([
        ('planned', 'Planned'),
        ('complete', 'Complete'),
        ], 'Status', required=True)
    start_date = fields.Date('Start Date', states=_states)
    start_time = fields.Time('Start Time', states=_states)
    end_time = fields.Time('End Time', states=_states)
    record = fields.Text('Record', states=_states)
    partners = fields.Many2Many('cooperative.partner-meeting',
        'meeting', 'partner', 'Partner',
        domain=[
            ('status', '=', 'active'),
            ])

    del _states

    @staticmethod
    def default_type():
        return 'reunion'

    @staticmethod
    def default_status():
        return 'planned'


class MeetingReport(Report):
    __name__ = 'cooperative.meeting'

    @classmethod
    def get_context(cls, records, data):
        report_context = super(MeetingReport, cls).get_context(records,
            data)
        report_context['company'] = report_context['user'].company
        report_context['format_vat_number'] = cls.format_vat_number
        return report_context

    @classmethod
    def format_vat_number(cls, vat_number=''):
        return '%s-%s-%s' % (vat_number[:2], vat_number[2:-1], vat_number[-1])
