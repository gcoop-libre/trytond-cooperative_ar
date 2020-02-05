#! -*- coding: utf8 -*-
# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Equal, Eval
from trytond.transaction import Transaction

__all__ = ['Partner']


class Partner(ModelSQL, ModelView):
    'Partner'
    __name__ = 'cooperative.partner'
    status = fields.Selection([
        ('active', 'Active'),
        ('give_up', 'Give Up'),
        ], 'Status', required=True)
    file = fields.Integer('File', required=True)
    party = fields.Many2One('party.party', 'Party', required=True)
    company = fields.Many2One('company.company', 'Company', required=True)
    first_name = fields.Char('First Name', required=True)
    last_name = fields.Char('Last Name', required=True)
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'other'),
        ], 'Gender', required=True)
    dni = fields.Char('DNI', required=True)
    nationality = fields.Many2One('country.country', 'Nationality',
        required=True)
    marital_status = fields.Selection([
        ('soltero/a', 'Soltero/a'),
        ('casado/a', 'Casado/a'),
        ('divorciado/a', 'Divorciado/a'),
        ('viudo/a', 'Viudo/a'),
        ('otra', 'Otra'),
        ], 'Marital Status', required=True)
    incorporation_date = fields.Date('Incorporation Date', required=True)
    leaving_date = fields.Date('Leaving Date', states={
                'readonly': ~Equal(Eval('status'), 'give_up'),
                'required': Equal(Eval('status'), 'give_up'),
                })
    payed_quotes = fields.Numeric('Payed Quotes')
    vacation_days = fields.Integer('Vacation Days')
    vacation = fields.One2Many('cooperative.partner.vacation', 'partner',
        'Vacation')
    meeting = fields.Many2Many('cooperative.partner-meeting', 'partner',
        'meeting', 'Meeting')
    sanction = fields.One2Many('cooperative.partner.sanction', 'partner',
        'Sanction')
    recibo = fields.One2Many('cooperative.partner.recibo', 'partner', 'Recibo')
    proposal_letter = fields.Binary('Proposal Letter')
    proof_tax = fields.Binary('Proof of tax registation')
    meeting_date_of_incoroporation = fields.Date(
        'Meeting date of incorporation', required=True)
    birthdate = fields.Date('Birthdate', required=True)

    @classmethod
    def copy(cls, partners, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['file'] = 9999
        # default['party'] = None
        default['recibo'] = None
        default['sanction'] = None
        default['meeting'] = None
        default['vacation'] = None
        default['vacation_days'] = 0
        return super(Partner, cls).copy(partners, default=default)

    def get_rec_name(self, name):
        if self.file:
            prefix = '[%s]' % self.id
        if self.party:
            return '%s %s' % (prefix, self.party.name)
        else:
            return prefix

    @classmethod
    def search_rec_name(cls, name, clause):
        if clause[1].startswith('!') or clause[1].startswith('not '):
            bool_op = 'AND'
        else:
            bool_op = 'OR'

        return [bool_op,
            ('party.name',) + tuple(clause[1:]),
            ('dni',) + tuple(clause[1:]),
            ]

    @staticmethod
    def default_status():
        return 'active'

    @staticmethod
    def default_nationality():
        Country = Pool().get('country.country')
        countries = Country.search([('code', '=', 'AR')])
        if countries:
            return countries[0].id
        return None

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @classmethod
    def __setup__(cls):
        super(Partner, cls).__setup__()
        cls._error_messages.update({
            'unique_file': 'The file must be unique.',
            })

    @classmethod
    def write(cls, partners, vals):
        if 'file' in vals:
            data = cls.search([('file', '=', vals['file'])])
            if data and data != partners:
                cls.raise_user_error('unique_file')

        return super(Partner, cls).write(partners, vals)

    @classmethod
    def create(cls, vlist):
        for vals in vlist:
            if 'file' in vals:
                data = cls.search([('file', '=', vals['file'])])
                if data:
                    cls.raise_user_error('unique_file')

        return super(Partner, cls).create(vlist)
