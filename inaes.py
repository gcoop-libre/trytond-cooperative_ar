# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
import stdnum.ar.cuit as cuit
import stdnum.ar.cbu as cbu

from trytond.model import ModelView, fields
from trytond.wizard import Wizard, StateView, StateReport, Button
from trytond.report import Report
from trytond.pool import Pool
from trytond.transaction import Transaction


class ReciboInaesStart(ModelView):
    'Recibo Inaes Start'
    __name__ = 'cooperative.partner.recibo.inaes.start'


class ReciboInaes(Wizard):
    'Recibo INAES'
    __name__ = 'cooperative.partner.recibo.inaes'

    start = StateView('cooperative.partner.recibo.inaes.start',
        'cooperative_ar.recibo_inaes_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Process', 'recibos_inaes', 'tryton-ok', default=True),
        ])
    recibos_inaes = StateReport(
        'cooperative.partner.recibo.inaes_report')

    def do_recibos_inaes(self, action):
        pool = Pool()
        Recibo = pool.get('cooperative.partner.recibo')
        recibos = Recibo.browse(Transaction().context['active_ids'])
        ids = [r.id for r in recibos
            if r.state == 'confirmed'
            and r.party
            and r.bank_account
            and r.paid_move]
        if ids:
            return action, {
                'id': ids[0],
                'ids': ids,
                }


class ReciboInaesReport(Report):
    'Recibo Inaes Report'
    __name__ = 'cooperative.partner.recibo.inaes_report'

    @classmethod
    def get_context(cls, records, data):

        def format_decimal(n):
            if not isinstance(n, Decimal):
                n = Decimal(n)
            return ('{0:.2f}'.format(abs(n))).replace('.', ',')

        def strip_accents(s):
            from unicodedata import normalize, category
            return ''.join(c for c in normalize('NFD', s)
                if category(c) != 'Mn')

        context = super().get_context(records, data)
        pool = Pool()
        Recibo = pool.get('cooperative.partner.recibo')
        recibos = Recibo.browse(data['ids'])
        context['records'] = recibos
        context['format_decimal'] = format_decimal
        context['get_company_cuit'] = cls._get_company_cuit
        context['get_partner_cuit'] = cls._get_partner_cuit
        context['get_partner_cbu'] = cls._get_partner_cbu
        return context

    @classmethod
    def _get_company_cuit(cls, record):
        return cuit.compact(record.company.party.tax_identifier.code)

    @classmethod
    def _get_partner_cuit(cls, record):
        return cuit.compact(record.party.tax_identifier.code)

    @classmethod
    def _get_partner_cbu(cls, record):
        return cbu.compact(record.bank_account.rec_name)
