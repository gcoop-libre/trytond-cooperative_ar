#! -*- coding: utf8 -*-
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Equal, Eval, Id
from trytond.transaction import Transaction

__all__ = ['Partner']

class Partner(ModelSQL, ModelView):
    "cooperative_ar"
    __name__ = "cooperative.partner"
    _rec_name = 'party'
    status = fields.Selection([('active', 'Active'),
                               ('give_up', 'Give Up'),
                               ],'Status', required=True)
    file = fields.Integer('File', required=True)
    party = fields.Many2One('party.party', 'Party', required=True)
    company = fields.Many2One('company.company', 'Company', required=True)
    first_name = fields.Char('First Name', required=True)
    last_name = fields.Char('Last Name', required=True)
    gender = fields.Selection([('male', 'Male'),
                               ('female', 'Female'),
                               ('other', 'other'),
                               ], 'Gender', required=True)
    dni = fields.Char('DNI', required=True)
    nationality = fields.Many2One('country.country', 'Nationality', required=True)
    marital_status = fields.Selection([('soltero/a', 'Soltero/a'),
                                       ('casado/a', 'Casado/a'),
                                       ('divorciado/a', 'Divorciado/a'),
                                       ('viudo/a', 'Viudo/a'),
                                       ('otra', 'Otra'),
                                       ], 'Marital Status', required=True)
    incorporation_date = fields.Date('Incorporation Date', required=True)
    leaving_date = fields.Date('Leaving Date',
            states={
                'readonly': ~Equal(Eval('status'), 'give_up'),
                'required': Equal(Eval('status'), 'give_up'),
                },
            )

    payed_quotes = fields.Numeric('Payed Quotes')
    vacation_days = fields.Integer('Vacation Days')
    vacation = fields.One2Many('cooperative.partner.vacation', 'partner', 'Vacation')
    meeting = fields.Many2Many('cooperative.partner-meeting', 'partner', 'meeting', 'Meeting')
    sanction = fields.One2Many('cooperative.partner.sanction', 'partner', 'Sanction')
    recibo = fields.One2Many('cooperative.partner.recibo', 'partner', 'Recibo')

    marital_status = fields.Selection([('',''), ('soltero/a', 'Soltero/a'), ('casado/a', 'Casado/a'), ('divorciado/a', 'Divorciado/a'), ('viudo/a', 'Viudo/a'), ('otra', 'Otra'), ], 'Marital Status')

    proposal_letter = fields.Binary('Proposal Letter')
    proof_tax = fields.Binary('Proof of tax registation')

    meeting_date_of_incoroporation = fields.Date('Meeting date of incorporation', required=True)

    def get_rec_name(self, name):
        """Return Record name"""
        return "%d - %s" % (self.file, self.party.rec_name)

    @classmethod
    def search_rec_name(cls, name, clause):
        if cls.search([('dni',) + tuple(clause[1:])], limit=1):
            return [('dni',) + tuple(clause[1:])]
        return [(cls._rec_name,) + tuple(clause[1:])]

    @staticmethod
    def default_status():
        return 'active'

    @staticmethod
    def default_nationality():
        return Id('country', 'ar').pyson()

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @classmethod
    def write(cls, partners, vals):
        if 'file' in vals:
            data = cls.search([('file','=', vals['file'])])
            if data and data != partners:
                cls.raise_user_error('unique_file')

        return super(Partner, cls).write(partners, vals)

    @classmethod
    def create(cls, vlist):
        for vals in vlist:
            if 'file' in vals:
                data = cls.search([('file','=', vals['file'])])
                if data:
                    cls.raise_user_error('unique_file')

        return super(Partner, cls).create(vlist)

    @classmethod
    def __setup__(cls):
        super(Partner, cls).__setup__()
        cls._error_messages.update({
            'unique_file': 'The file must be unique.',
            })
