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

