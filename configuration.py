# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, ModelSingleton, fields
from trytond.model import MultiValueMixin, ValueMixin
from trytond import backend
from trytond.tools.multivalue import migrate_property
from trytond.pool import Pool
from trytond.pyson import Eval, Id
from trytond.modules.company.model import (
    CompanyMultiValueMixin, CompanyValueMixin)


def default_func(field_name):
    @classmethod
    def default(cls, **pattern):
        return getattr(
            cls.multivalue_model(field_name),
            'default_%s' % field_name, lambda: None)()
    return default


class Configuration(
        ModelSingleton, ModelSQL, ModelView, CompanyMultiValueMixin):
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
    recibo_sequence = fields.MultiValue(fields.Many2One(
            'ir.sequence', "Recibo Sequence", required=True,
            domain=[
                ('sequence_type', '=',
                    Id('cooperative_ar', 'sequence_type_recibo')),
                ('company', 'in',
                    [Eval('context', {}).get('company', -1), None]),
                ]))
    recibo_lote_sequence = fields.MultiValue(fields.Many2One(
            'ir.sequence', "Recibo Lote Sequence", required=True,
            domain=[
                ('sequence_type', '=',
                    Id('cooperative_ar', 'sequence_type_recibo')),
                ('company', 'in',
                    [Eval('context', {}).get('company', -1), None]),
                ]))

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field in {'receipt_account_receivable', 'receipt_account_payable'}:
            return pool.get('cooperative_ar.configuration.receipt_account')
        if field in {'recibo_sequence', 'recibo_lote_sequence'}:
            return pool.get('cooperative_ar.configuration.sequence')
        return super().multivalue_model(field)

    default_recibo_sequence = default_func('recibo_sequence')
    default_recibo_lote_sequence = default_func('recibo_lote_sequence')


class _ConfigurationValue(ModelSQL):

    _configuration_value_field = None

    @classmethod
    def __register__(cls, module_name):
        TableHandler = backend.get('TableHandler')
        exist = TableHandler.table_exist(cls._table)

        super().__register__(module_name)

        if not exist:
            cls._migrate_property([], [], [])

    @classmethod
    def _migrate_property(cls, field_names, value_names, fields):
        field_names.append(cls._configuration_value_field)
        value_names.append(cls._configuration_value_field)
        migrate_property(
            'cooperative_ar.configuration', field_names, cls, value_names,
            fields=fields)


class ConfigurationSequence(_ConfigurationValue, ModelSQL, CompanyValueMixin):
    'Receipt Configuration Sequence'
    __name__ = 'cooperative_ar.configuration.sequence'
    recibo_sequence = fields.Many2One(
        'ir.sequence', "Recibo Sequence", required=True,
        domain=[
            ('sequence_type', '=',
                Id('cooperative_ar', 'sequence_type_recibo')),
            ('company', 'in', [Eval('company', -1), None]),
            ],
        depends=['company'])
    recibo_lote_sequence = fields.Many2One(
        'ir.sequence', "Recibo Lote Sequence", required=True,
        domain=[
            ('sequence_type', '=',
                Id('cooperative_ar', 'sequence_type_recibo')),
            ('company', 'in', [Eval('company', -1), None]),
            ],
        depends=['company'])
    _configuration_value_field = 'recibo_sequence'
    _configuration_value_field = 'recibo_lote_sequence'

    @classmethod
    def default_recibo_sequence(cls):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id('cooperative_ar', 'sequence_recibo')
        except KeyError:
            return None

    @classmethod
    def default_recibo_lote_sequence(cls):
        pool = Pool()
        ModelData = pool.get('ir.model.data')
        try:
            return ModelData.get_id('cooperative_ar', 'sequence_recibo_lote')
        except KeyError:
            return None


class ConfigurationReceiptAccount(ModelSQL, CompanyValueMixin):
    "Account Configuration Receipt Account"
    __name__ = 'cooperative_ar.configuration.receipt_account'
    receipt_account_receivable = fields.Many2One(
        'account.account', "Receipt Account Receivable",
        domain=[
            ('company', '=', Eval('context', {}).get('company', -1)),
            ],
        depends=['company'])
    receipt_account_payable = fields.Many2One(
        'account.account', "Receipt Account Payable",
        domain=[
            ('company', '=', Eval('context', {}).get('company', -1)),
            ],
        depends=['company'])
