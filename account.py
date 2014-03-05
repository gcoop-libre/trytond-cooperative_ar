#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval

__all__ = ['FiscalYear']

class FiscalYear(ModelSQL, ModelView):
    __name__ = 'account.fiscalyear'
    receipt_sequence = fields.Many2One('ir.sequence',
        'Receipt Sequence', required=True,
        domain=[
            ('code', '=', 'account.invoice'),
            ['OR',
                ('company', '=', Eval('company')),
                ('company', '=', None),
                ],
            ],
        context={
            'code': 'account.invoice',
            'company': Eval('company'),
            },
        depends=['company'])

    def get_sequence(self, field_name):
        sequence = getattr(self, field_name + '_sequence')
        if sequence:
            return sequence
        return getattr(self.fiscalyear, field_name + '_sequence')
