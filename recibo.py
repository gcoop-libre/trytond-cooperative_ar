#! -*- coding: utf8 -*-
# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from singing_girl import Singer
from decimal import Decimal
import stdnum.ar.cbu as cbu

from trytond.model import ModelView, Workflow, ModelSQL, fields
from trytond.pyson import Eval, If
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta
from trytond.wizard import Wizard, StateView, StateReport, Button
from trytond.report import Report

__all__ = ['Move', 'Recibo', 'ReciboReport', 'ReciboTransactionsStart',
    'ReciboTransactions', 'ReciboTransactionsReport', 'ReciboLote']

_DEPENDS = ['state']

_STATES = {
    'readonly': Eval('state') != 'draft',
}


class Move(metaclass=PoolMeta):
    __name__ = 'account.move'

    @classmethod
    def _get_origin(cls):
        return super(Move, cls)._get_origin() + ['cooperative.partner.recibo']


class Recibo(Workflow, ModelSQL, ModelView):
    'Cooperative receipt'
    __name__ = 'cooperative.partner.recibo'
    date = fields.Date('Date', states=_STATES, depends=_DEPENDS, required=True)
    amount = fields.Numeric('Amount', digits=(16, Eval('currency_digits', 2)),
            states=_STATES, required=True,
            depends=_DEPENDS + ['currency_digits'])
    partner = fields.Many2One('cooperative.partner', 'Partner', states=_STATES,
        depends=_DEPENDS, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ], 'State', readonly=True)
    number = fields.Char('Number', size=None, readonly=True, select=True)
    description = fields.Char('Description', size=None, states=_STATES,
        depends=_DEPENDS)
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
            'invisible': Eval('state').in_(['draft']),
            }, readonly=True)
    journal = fields.Many2One('account.journal', "Journal", required=True,
        domain=[('type', '=', 'cash')], states=_STATES, depends=_DEPENDS)
    payment_method = fields.Many2One(
        'account.invoice.payment.method', "Payment Method",  required=True,
        domain=[
            ('company', '=', Eval('company')),
            ],
        states=_STATES,
        depends=_DEPENDS + ['company'])
    currency = fields.Many2One('currency.currency', 'Currency', states={
            'readonly': Eval('state') != 'draft',
            }, depends=['state'], required=True)
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    currency_date = fields.Function(fields.Date('Currency Date'),
        'on_change_with_currency_date')
    account = fields.Many2One('account.account', 'Account', required=True,
        states=_STATES, depends=_DEPENDS + [
            'company', 'accounting_date', 'date'],
        domain=[
            ('company', '=', Eval('company', -1)),
            ('kind', '=', 'payable'),
            ],
        context={
            'date': If(Eval('accounting_date'),
                Eval('accounting_date'),
                Eval('date')),
            })
    account_expense = fields.Many2One('account.account', 'Account',
        required=True, states=_STATES, depends=_DEPENDS + [
            'company', 'accounting_date', 'date'],
        domain=[
            ('company', '=', Eval('company', -1)),
            ('kind', '=', 'expense'),
            ],
        context={
            'date': If(Eval('accounting_date'),
                Eval('accounting_date'),
                Eval('date')),
            })
    bank_account = fields.Many2One('bank.account', 'Bank account',
        states=_STATES,
        domain=[
            ('owners', '=', Eval('party')),
            ('numbers.type', '=', 'cbu'),
            ],
        context={
            'owners': Eval('party'),
            'numbers.type': 'cbu',
            },
        depends=_DEPENDS + ['party'])
    lote = fields.Many2One('cooperative.partner.recibo.lote', 'Lote')

    @classmethod
    def __setup__(cls):
        super(Recibo, cls).__setup__()
        cls._error_messages.update({
                'missing_config_accounts': ('You must set debit/credit '
                    'accounts at the configuration module.'),
                'delete_numbered': ('The numbered receipt "%s" can not be '
                    'deleted.'),
                'no_cooperative_sequence': ('You must set a receipt sequence '
                    'at the configuration module.'),
                })
        cls._transitions |= set((
                ('draft', 'confirmed'),
                ('draft', 'cancelled'),
                ('confirmed', 'draft'),
                ('confirmed', 'cancelled'),
                ('cancel', 'draft'),
                ))
        cls._buttons.update({
                'cancel': {
                    'invisible': ~Eval('state').in_(['draft']),
                    },
                'draft': {
                    'invisible': ~Eval('state').in_(['cancelled']),
                    },
                'confirm': {
                    'invisible': ~Eval('state').in_(['draft']),
                    },
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
    def default_date():
        return Pool().get('ir.date').today()

    @staticmethod
    def default_amount():
        return Decimal('0')

    @staticmethod
    def default_currency():
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.currency.id

    @staticmethod
    def default_currency_digits():
        Company = Pool().get('company.company')
        if Transaction().context.get('company'):
            company = Company(Transaction().context['company'])
            return company.currency.digits
        return 2

    @staticmethod
    def default_account_expense():
        pool = Pool()
        Config = Pool().get('cooperative_ar.configuration')
        config = Config(1)
        return config.receipt_account_receivable.id

    @staticmethod
    def default_account():
        pool = Pool()
        Config = Pool().get('cooperative_ar.configuration')
        config = Config(1)
        return config.receipt_account_payable.id

    @fields.depends('partner')
    def on_change_with_party(self, name=None):
        if self.partner:
            return self.partner.party.id

    @fields.depends('currency')
    def on_change_with_currency_digits(self, name=None):
        if self.currency:
            return self.currency.digits
        return 2

    @fields.depends('date')
    def on_change_with_currency_date(self, name=None):
        Date = Pool().get('ir.date')
        return self.date or Date.today()

    @fields.depends('partner', 'party')
    def on_change_with_bank_account(self, name=None):
        if self.party:
            return self.get_bank_account()

    def get_bank_account(self):
        "Return the bank_account to transfer"
        for bank_account in self.party.bank_accounts:
            for bank_account_number in bank_account.numbers:
                if bank_account_number.type == 'cbu':
                    return bank_account.id

    @classmethod
    def copy(cls, receipts, default=None):
        if default is None:
            default = {}
        default = default.copy()
        default['number'] = None
        default['state'] = 'draft'
        default['accounting_date'] = None
        default['confirmed_move'] = None
        default['paid_move'] = None
        default['amount'] = Decimal('0')
        default['lote'] = None
        return super(Recibo, cls).copy(receipts, default=default)

    @classmethod
    def delete(cls, receipts):
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
    def confirm(cls, recibos):
        Move = Pool().get('account.move')

        moves = []
        for recibo in recibos:
            recibo.set_number()
            recibo.create_move()

        cls.write(recibos, {
                'state': 'confirmed',
                })

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelled')
    def cancel(cls, recibos):
        pass

    def set_number(self):
        '''
        Set number to the receipt
        '''
        pool = Pool()
        Date = pool.get('ir.date')
        Sequence = pool.get('ir.sequence')
        Configuration = pool.get('cooperative_ar.configuration')

        if self.number:
            return

        config = Configuration(1)
        sequence = config.receipt_sequence
        if not sequence:
            self.raise_user_error('no_cooperative_sequence')

        with Transaction().set_context(
                date=self.date or Date.today()):
            number = Sequence.get_id(sequence.id)
            vals = {'number': number}

        self.write([self], vals)

    def _get_move_line(self, date, amount, account):
        '''
        Return move line
        '''
        pool = Pool()
        Currency = pool.get('currency.currency')
        MoveLine = pool.get('account.move.line')
        line = MoveLine()
        if self.currency != self.company.currency:
            with Transaction().set_context(date=self.date):
                line.amount_second_currency = Currency.compute(
                    self.company.currency, amount, self.currency)
            line.second_currency = self.currency
        else:
            line.amount_second_currency = None
            line.second_currency = None
        if amount <= 0:
            line.debit, line.credit = -amount, 0
        else:
            line.debit, line.credit = 0, amount
        if line.amount_second_currency:
            line.amount_second_currency = (
                line.amount_second_currency.copy_sign(
                    line.debit - line.credit))
        line.account = account
        if account.party_required:
            line.party = self.party
        line.maturity_date = date
        line.description = '%s %s' % (self.description, self.party.name)
        line.origin = self
        return line

    def get_move(self, move_lines, journal):

        pool = Pool()
        Move = pool.get('account.move')
        Period = pool.get('account.period')

        accounting_date = self.accounting_date or self.date
        period_id = Period.find(self.company.id, date=accounting_date)

        move = Move()
        move.journal = journal
        move.period = period_id
        move.date = accounting_date
        move.origin = self
        move.company = self.company
        move.description = '%s %s' % (self.description, self.number)
        move.lines = move_lines
        return move

    def create_move(self):
        '''
        Create account move for the receipt and return the created move
        '''
        pool = Pool()
        Move = pool.get('account.move')
        MoveLine = pool.get('account.move.line')
        move_lines = []
        accounting_date = self.accounting_date or self.date

        val = self._get_move_line(accounting_date, self.amount, self.account)
        move_lines.append(val)
        val = self._get_move_line(accounting_date, -self.amount,
            self.account_expense)
        move_lines.append(val)

        move = self.get_move(move_lines, self.journal)
        Move.save([move])
        Move.post([move])

        reconcile_lines = [l for l in move.lines if l.party_required]

        self.write([self], {
                'confirmed_move': move.id,
                })

        move_lines = []
        val = self._get_move_line(accounting_date, self.amount,
            self.payment_method.credit_account)
        move_lines.append(val)
        val = self._get_move_line(accounting_date, -self.amount, self.account)
        move_lines.append(val)

        move = self.get_move(move_lines, self.payment_method.journal)
        Move.save([move])
        Move.post([move])

        reconcile_lines += [l for l in move.lines if l.party_required]

        self.write([self], {
                'paid_move': move.id,
                })

        MoveLine.reconcile(reconcile_lines)


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


class ReciboTransactionsStart(ModelView):
    'Recibo Transactions Start'
    __name__ = 'cooperative.partner.recibo.transactions.start'


class ReciboTransactions(Wizard):
    'Recibo Transactions'
    __name__ = 'cooperative.partner.recibo.transactions'
    start = StateView('cooperative.partner.recibo.transactions.start',
        'cooperative_ar.recibo_transactions_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Process', 'transactions', 'tryton-ok', default=True),
        ])
    transactions = StateReport('cooperative.partner.recibo.transactions_report')

    def do_transactions(self, action):
        pool = Pool()
        Recibo = pool.get('cooperative.partner.recibo')
        recibos = Recibo.browse(Transaction().context['active_ids'])
        ids = [r.id for r in recibos
            if r.state == 'confirmed'
            and r.party
            and r.paid_move]
        if ids:
            return action, {
                'id': ids[0],
                'ids': ids,
                }


class ReciboTransactionsReport(Report):
    'Recibo Transactions Report'
    __name__ = 'cooperative.partner.recibo.transactions_report'

    @classmethod
    def get_context(cls, records, data):

        def get_eol():
            return '\r\n'

        def justify(string, size):
            return string[:size].ljust(size)

        def format_decimal(n):
            if not isinstance(n, Decimal):
                n = Decimal(n)
            return ('{0:.2f}'.format(abs(n))).replace('.', '').rjust(15, '0')

        def strip_accents(s):
            from unicodedata import normalize, category
            return ''.join(c for c in normalize('NFD', s)
                if category(c) != 'Mn')

        context = super(ReciboTransactionsReport, cls).get_context(records, data)
        pool = Pool()
        Recibo = pool.get('cooperative.partner.recibo')
        recibos = Recibo.browse(data['ids'])
        context['records'] = recibos
        context['strip_accents'] = strip_accents
        context['get_account_type'] = cls._get_account_type
        context['get_bank_code'] = cls._get_bank_code
        context['get_filial'] = cls._get_filial
        context['get_num_cuenta_mas_digito'] = cls._get_num_cuenta_mas_digito
        context['get_digito_verificador'] = cls._get_digito_verificador
        context['format_decimal'] = format_decimal
        context['justify'] = justify
        context['get_address'] = cls._get_address
        context['get_eol'] = get_eol
        return context

    @classmethod
    def _get_account_type(cls, record):
        return cbu.compact(record.bank_account.rec_name)[10]

    @classmethod
    def _get_bank_code(cls, record):
        return record.bank_account.bank.bcra_code

    @classmethod
    def _get_filial(cls, record):
        return cbu.compact(record.bank_account.rec_name)[3:7]

    @classmethod
    def _get_num_cuenta_mas_digito(cls, record):
        return cbu.compact(record.bank_account.rec_name)[14:]

    @classmethod
    def _get_digito_verificador(cls, record):
        return cbu.compact(record.bank_account.rec_name)[-1]

    @classmethod
    def _get_address(cls, record):
        pool = Pool()
        Party = pool.get('party.party')
        if Party and isinstance(record.party, Party):
            contact = record.party.contact_mechanism_get(
                'email', usage='invoice')
            if contact and contact.email:
                return contact.email


class ReciboLote(Workflow, ModelSQL, ModelView):
    'Recibo Lote'
    __name__ = 'cooperative.partner.recibo.lote'

    number = fields.Char('Number', readonly=True, select=True)
    date = fields.Date('Date', states=_STATES, depends=_DEPENDS, required=True)
    description = fields.Char('Description', states=_STATES, depends=_DEPENDS)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Canceled'),
        ], 'State', readonly=True)
    journal = fields.Many2One('account.journal', "Journal", required=True,
        domain=[('type', '=', 'cash')], states=_STATES, depends=_DEPENDS)
    payment_method = fields.Many2One(
        'account.invoice.payment.method', "Payment Method",  required=True,
        domain=[
            ('company', '=', Eval('company')),
            ],
        states=_STATES,
        depends=_DEPENDS + ['company'])
    company = fields.Many2One('company.company', 'Company', states=_STATES,
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ],
        depends=_DEPENDS, required=True, select=True)
    recibos = fields.One2Many('cooperative.partner.recibo', 'lote',
        'Recibos', states=_STATES, depends=_DEPENDS)

    @classmethod
    def __setup__(cls):
        super(ReciboLote, cls).__setup__()
        cls._transitions |= set((
                ('draft', 'confirmed'),
                ('draft', 'cancelled'),
                ('confirmed', 'draft'),
                ('confirmed', 'cancelled'),
                ('cancelled', 'draft'),
                ))
        cls._buttons.update({
                'cancel': {
                    'invisible': ~Eval('state').in_(['draft']),
                    },
                'draft': {
                    'invisible': ~Eval('state').in_(['cancelled']),
                    },
                'confirm': {
                    'invisible': ~Eval('state').in_(['draft']),
                    },
                })

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_date():
        return Pool().get('ir.date').today()

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @fields.depends('recibos', 'company', 'journal', 'payment_method', 'date')
    def on_change_payment_method(self):
        self.add_recibos()

    @fields.depends('recibos', 'company', 'journal', 'payment_method', 'date')
    def on_change_journal(self):
        self.add_recibos()

    @fields.depends('recibos', 'company', 'journal', 'payment_method', 'date')
    def on_change_company(self):
        self.add_recibos()

    def add_recibos(self):
        pool = Pool()
        Recibo = pool.get('cooperative.partner.recibo')
        Partner = pool.get('cooperative.partner')
        Currency = pool.get('currency.currency')
        lines = []

        if not self.journal or not self.payment_method or not self.date:
            self.recibos = lines
            return

        if self.recibos:
            return

        partners = Partner.search([('status', '=', 'active')],
            order=[('file', 'ASC')])

        for partner in partners:
            recibo = Recibo()
            recibo.partner = partner
            recibo.party = recibo.on_change_with_party()
            recibo.bank_account = recibo.on_change_with_bank_account()
            recibo.account = recibo.default_account()
            recibo.account_expense = recibo.default_account_expense()
            recibo.date = self.date
            recibo.company = self.company
            recibo.currency = recibo.default_currency()
            recibo.currency_digits = recibo.on_change_with_currency_digits()
            recibo.currency_date = recibo.on_change_with_currency_date()
            recibo.description = recibo.default_description()
            recibo.journal = self.journal
            recibo.payment_method = self.payment_method
            recibo.amount = Decimal('0')
            recibo.state = recibo.default_state()
            lines.append(recibo)

        self.recibos = lines

    @classmethod
    def set_number(cls, lotes):
        '''
        Fill the number field with the lote sequence
        '''
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = Pool().get('cooperative_ar.configuration')

        config = Config(1)
        for lote in lotes:
            if lote.number:
                continue
            lote.number = Sequence.get_id(config.receipt_lote_sequence.id)
        cls.save(lotes)


    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, lotes):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('cancel')
    def cancel(cls, lotes):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmed')
    def confirm(cls, lotes):
        pool = Pool()
        Recibo = pool.get('cooperative.partner.recibo')

        cls.set_number(lotes)
        for lote in lotes:
            Recibo.confirm(lote.recibos)
