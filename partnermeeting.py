#! -*- coding: utf8 -*-
from trytond.model import ModelView, ModelSQL, fields

__all__ = ['PartnerMeeting']

class PartnerMeeting(ModelSQL):
    "cooperative_ar"
    __name__ = "cooperative.partner-meeting"
    partner = fields.Many2One('cooperative.partner', 'Partner')
    meeting = fields.Many2One('cooperative.meeting', 'Meeting')

