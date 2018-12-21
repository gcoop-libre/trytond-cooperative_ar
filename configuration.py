# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
from trytond.pyson import Eval, Bool

__all__ = ['Configuration']


class Configuration(ModelSingleton, ModelSQL, ModelView):
    'Cooperative Configuration'
    __name__ = 'cooperative_ar.configuration'

    receipt_account_payable = fields.Property(fields.Many2One(
            'account.account', 'Account Payable', domain=[
                ('company', '=', Eval('context', {}).get('company', -1)),
                ],
            states={
                'required': Bool(Eval('context', {}).get('company')),
                'invisible': ~Eval('context', {}).get('company'),
                }))
    receipt_account_receivable = fields.Property(fields.Many2One(
            'account.account', 'Account Receivable', domain=[
                ('company', '=', Eval('context', {}).get('company', -1)),
                ],
            states={
                'required': Bool(Eval('context', {}).get('company')),
                'invisible': ~Eval('context', {}).get('company'),
                }))
    receipt_sequence = fields.Property(fields.Many2One('ir.sequence',
            'Receipt Sequence', domain=[
                ('code', '=', 'account.cooperative.receipt'),
                ]))
