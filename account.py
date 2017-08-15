# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pyson import Eval
from trytond.pool import Pool, PoolMeta

__all__ = ['FiscalYear']


class FiscalYear:
    __metaclass__ = PoolMeta
    __name__ = 'account.fiscalyear'
    cooperative_receipt_sequence = fields.Many2One('ir.sequence',
        'Cooperative Receipt Sequence', required=True,  domain=[
            ('code', '=', 'account.cooperative.receipt'),
            [
                'OR',
                ('company', '=', Eval('company')),
                ('company', '=', None),
            ],
        ],
        context={
            'code': 'account.cooperative.receipt',
            'company': Eval('company'),
            },
        depends=['company'])

    @classmethod
    def __setup__(cls):
        super(FiscalYear, cls).__setup__()
        cls._error_messages.update({
                'change_cooperative_sequence': ('You can not change '
                    'cooperative sequence in fiscal year "%s" because there '
                    'are already posted receipts in this fiscal year.'),
                'different_cooperative_sequence': ('Fiscal year "%(first)s" '
                    'and "%(second)s" have the same cooperative receipt '
                    'sequence.'),
                })

    @classmethod
    def validate(cls, years):
        super(FiscalYear, cls).validate(years)
        for year in years:
            year.check_cooperative_sequences()

    def check_cooperative_sequences(self):
        for sequence in ['cooperative_receipt_sequence']:
            fiscalyears = self.search([
                    (sequence, '=', getattr(self, sequence).id),
                    ('id', '!=', self.id),
                    ])
            if fiscalyears:
                self.raise_user_error('different_cooperative_sequence', {
                        'first': self.rec_name,
                        'second': fiscalyears[0].rec_name,
                        })

    @classmethod
    def write(cls, *args):
        Receipt = Pool().get('cooperative.partner.recibo')

        actions = iter(args)
        for fiscalyears, values in zip(actions, actions):
            sequence = 'cooperative_receipt_sequence'
            if not values.get(sequence):
                continue
            for fiscalyear in fiscalyears:
                if (getattr(fiscalyear, sequence) and
                        (getattr(fiscalyear, sequence).id !=
                            values[sequence])):
                    if Receipt.search([
                                ('date', '>=', fiscalyear.start_date),
                                ('date', '<=', fiscalyear.end_date),
                                ('number', '!=', None),
                                ]):
                        cls.raise_user_error(
                            'change_cooperative_sequence',
                            (fiscalyear.rec_name))
        super(FiscalYear, cls).write(*args)

    def get_sequence(self, field_name):
        return getattr(self, field_name + '_sequence')
