#! -*- coding: utf8 -*-
from trytond.model import ModelView, ModelSQL, fields

__all__ = ['Partner']

class Partner(ModelSQL, ModelView):
    "cooperative_ar"
    __name__ = "cooperative.partner"
    _rec_name = 'party'

    file = fields.Integer('File')
    party = fields.Many2One('party.party', 'Party')
    company = fields.Many2One('company.company', 'Company')
    first_name = fields.Char('First Name')
    last_name = fields.Char('Last Name')
    dni = fields.Char('DNI')
    nationality = fields.Many2One('country.country', 'Nationality')
    marital_status = fields.Selection([('soltero/a', 'Soltero/a'), ('casado/a', 'Casado/a'), ('divorciado/a', 'Divorciado/a'), ('viudo/a', 'Viudo/a'), ('otra', 'Otra'), ], 'Marital Status')
    incorporation_date = fields.Date('Incorporation Date')
    payed_quotes = fields.Numeric('Payed Quotes')
    vacation_days = fields.Integer('Vacation Days')
    vacation = fields.One2Many('cooperative.partner.vacation', 'partner', 'Vacation')
    meeting = fields.Many2Many('cooperative.partner-meeting', 'partner', 'meeting', 'Meeting')

    def get_rec_name(self, name):
        """Return Record name"""
        return "%d - %s" % (self.file, self.party.rec_name)

