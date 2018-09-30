#! -*- coding: utf8 -*-
# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from decimal import Decimal
from trytond.model import ModelView, Workflow, ModelSQL, fields
from trytond.pyson import Eval, If
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.report import Report

__all__ = ['Recibo', 'ReciboReport']

_DEPENDS = ['state']

_STATES = {
    'readonly': Eval('state') != 'draft',
}


class Recibo(Workflow, ModelSQL, ModelView):
    'Cooperative receipt'
    __name__ = 'cooperative.partner.recibo'
    date = fields.Date('Date', states={
                'readonly': (Eval('state') != 'draft')
            }, required=True)
    amount = fields.Numeric('Amount', digits=(16, 2), states={
                'readonly': (Eval('state') != 'draft')
            }, required=True)
    partner = fields.Many2One('cooperative.partner', 'Partner', states={
                'readonly': (Eval('state') != 'draft')
            }, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirm'),
        ('paid', 'Paid'),
        ('cancel', 'Canceled'),
        ], 'State', readonly=True)
    number = fields.Char('Number', size=None, readonly=True, select=True)

    description = fields.Char('Description', size=None, states=_STATES,
        depends=_DEPENDS)

    # Integrando con asientos
    party = fields.Function(fields.Many2One(
            'party.party', 'Party', required=True, states=_STATES,
            depends=_DEPENDS), 'on_change_with_party')
    company = fields.Many2One('company.company', 'Company', states=_STATES,
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ],
        depends=_DEPENDS, required=True, select=True)
    accounting_date = fields.Date('Accounting Date', states=_STATES,
        depends=_DEPENDS)
    confirmed_move = fields.Many2One('account.move', 'Confirmed Move',
        readonly=True)
    paid_move = fields.Many2One('account.move', 'Paid Move', states={
            'invisible': Eval('state').in_(['draft', 'confirmed']),
            }, readonly=True)
    journal = fields.Many2One('account.journal', 'Journal', states=_STATES,
        depends=_DEPENDS, required=True)
    currency = fields.Many2One('currency.currency', 'Currency', states={
            'readonly': ((Eval('state') != 'draft') | (Eval('lines') &
                    Eval('currency'))),
            }, depends=['state', 'lines'], required=True)

    @classmethod
    def __setup__(cls):
        super(Recibo, cls).__setup__()
        cls._error_messages.update({
                'missing_journal_accounts': ('You must set debit/credit '
                    'account at the journal "%(journal)s".'),
                'missing_config_accounts': ('You must set debit/credit '
                    'accounts at the configuration module.'),
                })
        cls._transitions |= set((
                ('draft', 'confirmed'),
                ('draft', 'cancel'),
                ('confirmed', 'draft'),
                ('confirmed', 'paid'),
                ('confirmed', 'cancel'),
                ('cancel', 'draft'),
                ))
        cls._buttons.update({
                'cancel': {
                    'invisible': ~Eval('state').in_(['draft']),
                    },
                'draft': {
                    'invisible': ~Eval('state').in_(['cancel']),
                    },
                'paid': {
                    'invisible': ~Eval('state').in_(['confirmed']),
                    },
                'confirmed': {
                    'invisible': ~Eval('state').in_(['draft']),
                    },
                })
        cls._error_messages.update({
                'delete_numbered': ('The numbered receipt "%s" can not be '
                    'deleted.'),
                })

    @classmethod
    def delete(cls, receipts):
        #cls.check_modify(invoices)
        # Cancel before delete
        #cls.cancel(invoices)
        for receipt in receipts:
            if receipt.number:
                cls.raise_user_error('delete_numbered', (receipt.rec_name,))
        super(Recibo, cls).delete(receipts)

    @classmethod
    def get_sing_number(self, recibo_amount):
        '''
        Convert numbers in its equivalent string text
        representation in spanish
        '''
        from singing_girl import Singer
        singer = Singer()
        return singer.sing(recibo_amount)

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, recibos):
        Move = Pool().get('account.move')

        moves = []
        for recibo in recibos:
            if recibo.confirmed_move:
                moves.append(recibo.confirmed_move)
        if moves:
            with Transaction().set_user(0, set_context=True):
                Move.delete(moves)

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmed')
    def confirmed(cls, recibos):
        Move = Pool().get('account.move')

        moves = []
        for recibo in recibos:
            recibo.set_number()
            moves.append(recibo.create_confirmed_move())

        cls.write(recibos, {
                'state': 'confirmed',
                })
        Move.post(moves)

    @classmethod
    @ModelView.button
    @Workflow.transition('paid')
    def paid(cls, recibos):
        Move = Pool().get('account.move')

        moves = []
        for recibo in recibos:
            moves.append(recibo.create_paid_move())

        cls.write(recibos, {
                'state': 'paid',
                })
        Move.post(moves)

    @classmethod
    @ModelView.button
    @Workflow.transition('cancel')
    def cancel(cls, recibos):
        cls.write(recibos, {
                'state': 'cancel',
                })

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_description():
        return 'Retornos a cuenta de excedentes'

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_currency():
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.currency.id

    @fields.depends('partner')
    def on_change_with_party(self, name=None):
        if self.partner:
            return self.partner.party.id

    def set_number(self):
        '''
        Set number to the receipt
        '''
        pool = Pool()
        FiscalYear = pool.get('account.fiscalyear')
        Date = pool.get('ir.date')
        Sequence = pool.get('ir.sequence')

        if self.number:
            return

        accounting_date = self.accounting_date or self.date
        fiscalyear_id = FiscalYear.find(self.company.id,
            date=accounting_date)
        fiscalyear = FiscalYear(fiscalyear_id)
        sequence = fiscalyear.get_sequence('cooperative_receipt')
        if not sequence:
            self.raise_user_error('no_cooperative_sequence', {
                    'receipt': self.rec_name,
                    'fiscalyear': fiscalyear.rec_name,
                    })

        with Transaction().set_context(
                date=self.date or Date.today()):
            number = Sequence.get_id(sequence.id)
            vals = {'number': number}

        self.write([self], vals)

    def _get_move_line(self, date, amount, account_id, party_required=False):
        '''
        Return move line
        '''
        Currency = Pool().get('currency.currency')
        res = {}
        if self.currency.id != self.company.currency.id:
            with Transaction().set_context(date=self.date):
                res['amount_second_currency'] = Currency.compute(
                    self.company.currency, amount, self.currency)
            res['amount_second_currency'] = abs(res['amount_second_currency'])
            res['second_currency'] = self.currency.id
        else:
            res['amount_second_currency'] = Decimal('0.0')
            res['second_currency'] = None
        if amount >= Decimal('0.0'):
            res['debit'] = Decimal('0.0')
            res['credit'] = amount
        else:
            res['debit'] = - amount
            res['credit'] = Decimal('0.0')
        res['account'] = account_id
        res['maturity_date'] = date
        res['description'] = self.description
        if party_required:
            res['party'] = self.party.id
        return res

    def create_move(self, move_lines):

        pool = Pool()
        Move = pool.get('account.move')
        Period = pool.get('account.period')

        accounting_date = self.accounting_date or self.date
        period_id = Period.find(self.company.id, date=accounting_date)

        move, = Move.create([{
                    'journal': self.journal.id,
                    'period': period_id,
                    'date': self.date,
        #            'origin': str(self),
                    'lines': [('create', move_lines)],
                    }])
        return move

    def create_confirmed_move(self):
        '''
        Create account move for the receipt and return the created move
        '''
        pool = Pool()
        Date = pool.get('ir.date')
        Config = Pool().get('cooperative_ar.configuration')
        config = Config(1)
        if (not config.receipt_account_receivable and not
                config.receipt_account_payable):
            self.raise_user_error('missing_config_accounts')

        account_receivable = config.receipt_account_receivable
        account_payable = config.receipt_account_payable

        move_lines = []

        val = self._get_move_line(Date.today(), self.amount,
            account_payable.id, party_required=True)
        move_lines.append(val)
        # issue #4461
        # En vez de usar la cuenta "a cobrar" del party, deberia ser la
        # cuenta Retornos Asociados (5242) siempre fija, que esta seteada como
        # Expense (Gasto).
        val = self._get_move_line(Date.today(), -self.amount,
            account_receivable.id, party_required=False)
        move_lines.append(val)

        move = self.create_move(move_lines)

        self.write([self], {
                'confirmed_move': move.id,
                })
        return move

    def create_paid_move(self):
        '''
        Create account move for the receipt and return the created move
        '''
        pool = Pool()
        Date = pool.get('ir.date')
        Config = Pool().get('cooperative_ar.configuration')
        config = Config(1)
        if not self.journal.credit_account:
            self.raise_user_error('missing_journal_accounts', {
                    'journal': self.journal.name,
                    })

        account_payable = config.receipt_account_payable

        move_lines = []

        val = self._get_move_line(Date.today(), self.amount,
            self.journal.credit_account.id, party_required=False)
        move_lines.append(val)
        val = self._get_move_line(Date.today(), -self.amount,
            account_payable.id, party_required=True)
        move_lines.append(val)

        move = self.create_move(move_lines)

        self.write([self], {
                'paid_move': move.id,
                })
        return move


class ReciboReport(Report):
    'Report Receipt'
    __name__ = 'cooperative.partner.recibo'

    @classmethod
    def get_context(cls, records, data):
        report_context = super(ReciboReport, cls).get_context(records, data)
        report_context['company'] = report_context['user'].company
        report_context['vat_number'] = \
            cls._get_vat_number(report_context['user'].company)
        report_context['get_place'] = cls.get_place
        return report_context

    @classmethod
    def _get_vat_number(cls, company):
        value = company.party.vat_number
        return '%s-%s-%s' % (value[:2], value[2:-1], value[-1])

    @classmethod
    def get_place(cls, party):
        place = ''
        invoice_address = party.address_get(type='invoice')
        if invoice_address.city:
            place = invoice_address.city
        elif invoice_address.subdivision:
            place = invoice_address.subdivision.name
        return place
