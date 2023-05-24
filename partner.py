# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool
from trytond.pyson import Equal, Eval
from trytond.transaction import Transaction
from trytond.exceptions import UserError
from trytond.i18n import gettext


class Partner(ModelSQL, ModelView):
    'Partner'
    __name__ = 'cooperative.partner'

    status = fields.Selection([
        ('active', 'Active'),
        ('give_up', 'Give Up'),
        ], 'Status', required=True)
    file = fields.Integer('File', required=True)
    party = fields.Many2One('party.party', 'Party', required=True,
        states={'readonly': Eval('status') == 'active'},
        depends=['status'])
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
    leaving_date = fields.Date('Leaving Date',
        states={
            'readonly': ~Equal(Eval('status'), 'give_up'),
            'required': Equal(Eval('status'), 'give_up'),
            },
        depends=['status'])
    payed_quotes = fields.Numeric('Payed Quotes')
    vacation_days = fields.Integer('Vacation Days')
    vacation = fields.One2Many('cooperative.partner.vacation', 'partner',
        'Vacation')
    meeting = fields.Many2Many('cooperative.partner-meeting', 'partner',
        'meeting', 'Meeting')
    sanction = fields.One2Many('cooperative.partner.sanction', 'partner',
        'Sanctions')
    recibos = fields.One2Many('cooperative.partner.recibo', 'partner',
        'Recibos')
    proposal_letter = fields.Binary('Proposal Letter')
    proof_tax = fields.Binary('Proof of tax registation')
    meeting_date_of_incoroporation = fields.Date(
        'Meeting date of incorporation', required=True)
    birthdate = fields.Date('Birthdate', required=True)
    # Skills
    recibo_base = fields.Numeric('Base Amount', digits=(16, 2))
    skill_01 = fields.Boolean('Skill 1')
    skill_02 = fields.Boolean('Skill 2')
    skill_03 = fields.Boolean('Skill 3')
    skill_04 = fields.Boolean('Skill 4')
    skill_05 = fields.Boolean('Skill 5')
    skill_06 = fields.Boolean('Skill 6')
    skill_07 = fields.Boolean('Skill 7')
    skill_08 = fields.Boolean('Skill 8')
    skill_09 = fields.Boolean('Skill 9')
    skill_10 = fields.Boolean('Skill 10')
    recibo_total = fields.Function(fields.Numeric(
        'Total Amount', digits=(16, 2)), 'on_change_with_recibo_total')

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

    @staticmethod
    def default_recibo_base():
        return Decimal(0)

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

    @classmethod
    def copy(cls, partners, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['file'] = 9999
        # default['party'] = None
        default['recibos'] = None
        default['sanction'] = None
        default['meeting'] = None
        default['vacation'] = None
        default['vacation_days'] = 0
        return super().copy(partners, default=default)

    @classmethod
    def write(cls, partners, vals):
        if 'file' in vals:
            data = cls.search([('file', '=', vals['file'])])
            if data and data != partners:
                raise UserError(gettext('cooperative_ar.msg_unique_file'))
        return super().write(partners, vals)

    @classmethod
    def create(cls, vlist):
        for vals in vlist:
            if 'file' in vals:
                data = cls.search([('file', '=', vals['file'])])
                if data:
                    raise UserError(gettext('cooperative_ar.msg_unique_file'))
        return super().create(vlist)

    @fields.depends('recibo_base', 'skill_01', 'skill_02', 'skill_03',
        'skill_04', 'skill_05', 'skill_06', 'skill_07', 'skill_08',
        'skill_09', 'skill_10')
    def on_change_with_recibo_total(self, name=None):
        pool = Pool()
        ConfigurationSkill = pool.get('cooperative_ar.configuration.skill')

        recibo_base = self.recibo_base
        if not recibo_base:
            return Decimal(0)

        configuration = ConfigurationSkill(1)
        amount = recibo_base
        quantize = Decimal(10) ** -Decimal(2)

        if self.skill_01 and configuration.skill_01:
            amount += (recibo_base * configuration.skill_01 /
                Decimal(100)).quantize(quantize)
        if self.skill_02 and configuration.skill_02:
            amount += (recibo_base * configuration.skill_02 /
                Decimal(100)).quantize(quantize)
        if self.skill_03 and configuration.skill_03:
            amount += (recibo_base * configuration.skill_03 /
                Decimal(100)).quantize(quantize)
        if self.skill_04 and configuration.skill_04:
            amount += (recibo_base * configuration.skill_04 /
                Decimal(100)).quantize(quantize)
        if self.skill_05 and configuration.skill_05:
            amount += (recibo_base * configuration.skill_05 /
                Decimal(100)).quantize(quantize)
        if self.skill_06 and configuration.skill_06:
            amount += (recibo_base * configuration.skill_06 /
                Decimal(100)).quantize(quantize)
        if self.skill_07 and configuration.skill_07:
            amount += (recibo_base * configuration.skill_07 /
                Decimal(100)).quantize(quantize)
        if self.skill_08 and configuration.skill_08:
            amount += (recibo_base * configuration.skill_08 /
                Decimal(100)).quantize(quantize)
        if self.skill_09 and configuration.skill_09:
            amount += (recibo_base * configuration.skill_09 /
                Decimal(100)).quantize(quantize)
        if self.skill_10 and configuration.skill_10:
            amount += (recibo_base * configuration.skill_10 /
                Decimal(100)).quantize(quantize)

        return amount
