# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
from trytond.model import MultiValueMixin, ValueMixin
from trytond import backend
from trytond.tools.multivalue import migrate_property
from trytond.pyson import Eval
from trytond.pool import Pool
from trytond.modules.company.model import (
    CompanyMultiValueMixin, CompanyValueMixin)

__all__ = ['Configuration', 'ConfigurationSequence',
    'ConfigurationReceiptAccount']

receipt_sequence = fields.Many2One('ir.sequence', 'Receipt Sequence',
    domain=[
        ('code', '=', 'cooperative.receipt'),
        ],
    help="Used to generate the receipt number.")


class Configuration(ModelSingleton, ModelSQL, ModelView, MultiValueMixin):
    'Cooperative Configuration'
    __name__ = 'cooperative_ar.configuration'

    receipt_account_receivable = fields.MultiValue(fields.Many2One(
            'account.account', "Default Account Receivable",
            domain=[
                ('company', '=', Eval('context', {}).get('company', -1)),
                ]))
    receipt_account_payable = fields.MultiValue(fields.Many2One(
            'account.account', "Default Account Payable",
            domain=[
                ('company', '=', Eval('context', {}).get('company', -1)),
                ]))
    receipt_sequence = fields.MultiValue(receipt_sequence)

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field in {'receipt_account_receivable', 'receipt_account_payable'}:
            return pool.get('cooperative_ar.configuration.receipt_account')
        return super(Configuration, cls).multivalue_model(field)

class _ConfigurationValue(ModelSQL):

    _configuration_value_field = None

    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')
        exist = TableHandler.table_exist(cls._table)

        super(_ConfigurationValue, cls).__register__(module_name)

        if not exist:
            cls._migrate_property([], [], [])

    @classmethod
    def _migrate_property(cls, field_names, value_names, fields):
        field_names.append(cls._configuration_value_field)
        value_names.append(cls._configuration_value_field)
        migrate_property(
            'cooperative_ar.configuration', field_names, cls, value_names,
            fields=fields)


class ConfigurationSequence(_ConfigurationValue, ModelSQL, ValueMixin):
    'Receipt Configuration Sequence'
    __name__ = 'cooperative_ar.configuration.receipt_sequence'
    receipt_sequence = receipt_sequence
    _configuration_value_field = 'receipt_sequence'

    @classmethod
    def check_xml_record(cls, records, values):
        return True


class ConfigurationReceiptAccount(ModelSQL, CompanyValueMixin):
    "Account Configuration Receipt Account"
    __name__ = 'account.configuration.receipt_account'
    receipt_account_receivable = fields.Many2One(
        'account.account', "Receipt Account Receivable",
        domain=[
            ('company', '=', Eval('company', -1)),
            ],
        depends=['company'])
    receipt_account_payable = fields.Many2One(
        'account.account', "Receipt Account Payable",
        domain=[
            ('company', '=', Eval('company', -1)),
            ],
        depends=['company'])
