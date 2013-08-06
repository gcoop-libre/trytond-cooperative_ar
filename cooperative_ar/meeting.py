#! -*- coding: utf8 -*-
from trytond.model import ModelView, ModelSQL, fields

__all__ = ['Meeting']

class Meeting(ModelSQL, ModelView):
    "cooperative_ar"
    __name__ = "cooperative.meeting"
    type = fields.Selection([('', ''), ('ordinaria', 'Ordinaria'), ('extraordinaria', 'Extraordinaria'), ('reunion', 'Reunion'), ], 'Type')
    status = fields.Selection([('', ''), ('planned', 'Planned'), ('complete', 'Complete'), ], 'Status')
    start_date = fields.Date('Start Date')
    start_time = fields.Time('Start Time')
    end_time = fields.Time('End Time')
    partner = fields.Many2Many('cooperative.partner-meeting', 'meeting', 'partner', 'Partner')

