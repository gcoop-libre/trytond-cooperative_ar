#! -*- coding: utf8 -*-
# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelSQL, fields

__all__ = ['PartnerMeeting']


class PartnerMeeting(ModelSQL):
    'Partner Meeting'
    __name__ = 'cooperative.partner-meeting'

    partner = fields.Many2One('cooperative.partner', 'Partner')
    meeting = fields.Many2One('cooperative.meeting', 'Meeting')
