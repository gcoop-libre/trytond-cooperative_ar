# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from singing_girl import Singer
from decimal import Decimal
import stdnum.ar.cbu as cbu
import stdnum.ar.cuit as cuit

from trytond.model import ModelView, Workflow, ModelSQL, fields
from trytond.wizard import Wizard, StateView, StateReport, Button
from trytond.report import Report
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval, If
from trytond.transaction import Transaction
from trytond.exceptions import UserError
from trytond.i18n import gettext


class Move(metaclass=PoolMeta):
    __name__ = 'account.move'

    @classmethod
    def _get_origin(cls):
        return super()._get_origin() + [
            'cooperative.partner.recibo']


class MoveLine(metaclass=PoolMeta):
    __name__ = 'account.move.line'

    @classmethod
    def _get_origin(cls):
        return super()._get_origin() + [
            'cooperative.partner.recibo']


class Recibo(Workflow, ModelSQL, ModelView):
    'Cooperative receipt'
    __name__ = 'cooperative.partner.recibo'

    _states = {'readonly': Eval('state') != 'draft'}
    _depends = ['state']

    date = fields.Date('Date', states=_states, depends=_depends, required=True)
    amount = fields.Numeric('Amount', digits=(16, Eval('currency_digits', 2)),
        states=_states, required=True,
        depends=_depends + ['currency_digits'])
    partner = fields.Many2One('cooperative.partner', 'Partner', states=_states,
        depends=_depends, required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ], 'State', readonly=True)
    number = fields.Char('Number', size=None, readonly=True, select=True)
    description = fields.Char('Description', size=None, states=_states,
        depends=_depends)
    party = fields.Function(fields.Many2One(
        'party.party', 'Party', required=True, states=_states,
        depends=_depends), 'on_change_with_party')
    company = fields.Many2One('company.company', 'Company', states=_states,
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ],
        depends=_depends, required=True, select=True)
    accounting_date = fields.Date('Accounting Date', states=_states,
        depends=_depends)
    paid_cancel_move = fields.Many2One('account.move', 'Paid Cancel Move',
        readonly=True, domain=[('company', '=', Eval('company', -1))],
        states={'invisible': ~Eval('paid_cancel_move')},
        depends=['company'])
    confirmed_cancel_move = fields.Many2One('account.move',
        'Confirmed Cancel Move', readonly=True,
        domain=[('company', '=', Eval('company', -1))],
        states={'invisible': ~Eval('confirmed_cancel_move')},
        depends=['company'])
    confirmed_move = fields.Many2One('account.move', 'Confirmed Move',
        readonly=True, domain=[('company', '=', Eval('company', -1))],
        depends=['company'])
    paid_move = fields.Many2One('account.move', 'Paid Move', readonly=True,
        domain=[('company', '=', Eval('company', -1))],
        depends=['company'])
    journal = fields.Many2One('account.journal', "Journal", required=True,
        domain=[('type', '=', 'cash')], states=_states, depends=_depends)
    payment_method = fields.Many2One(
        'account.invoice.payment.method', "Payment Method", required=True,
        domain=[('company', '=', Eval('company'))],
        states=_states, depends=_depends + ['company'])
    currency = fields.Many2One('currency.currency', 'Currency', required=True,
        states={'readonly': Eval('state') != 'draft'}, depends=['state'])
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    currency_date = fields.Function(fields.Date('Currency Date'),
        'on_change_with_currency_date')
    account = fields.Many2One('account.account', 'Account', required=True,
        states=_states, depends=_depends + [
            'company', 'accounting_date', 'date'],
        domain=[
            ('closed', '!=', True),
            ('type.payable', '=', True),
            ('company', '=', Eval('company', -1)),
            ],
        context={
            'date': If(Eval('accounting_date'),
                Eval('accounting_date'),
                Eval('date')),
            })
    account_expense = fields.Many2One('account.account', 'Account',
        required=True, states=_states, depends=_depends + [
            'company', 'accounting_date', 'date'],
        domain=[
            ('closed', '!=', True),
            ('type.expense', '=', True),
            ('company', '=', Eval('company', -1)),
            ],
        context={
            'date': If(Eval('accounting_date'),
                Eval('accounting_date'),
                Eval('date')),
            })
    bank_account = fields.Many2One('bank.account', 'Bank account',
        states=_states,
        domain=[
            ('owners', '=', Eval('party')),
            ('numbers.type', '=', 'cbu'),
            ],
        context={
            'owners': Eval('party'),
            'numbers.type': 'cbu',
            },
        depends=_depends + ['party'])
    lote = fields.Many2One('cooperative.partner.recibo.lote', 'Lote',
        ondelete='CASCADE')

    del _states, _depends

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._transitions |= set((
                ('draft', 'confirmed'),
                ('confirmed', 'draft'),
                ('confirmed', 'cancelled'),
                ))
        cls._buttons.update({
                'cancel': {
                    'invisible': ~Eval('state').in_(['confirmed']),
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
        return 'retornos a cuenta de excedentes'

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
        Config = pool.get('cooperative_ar.configuration')
        config = Config(1)
        if config.receipt_account_receivable:
            return config.receipt_account_receivable.id
        return None

    @staticmethod
    def default_account():
        pool = Pool()
        Config = pool.get('cooperative_ar.configuration')
        config = Config(1)
        if config.receipt_account_payable:
            return config.receipt_account_payable.id
        return None

    @fields.depends('partner', '_parent_partner.party')
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

    @fields.depends('party', '_parent_party.bank_accounts')
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
        else:
            default = default.copy()
        lote = Transaction().context.get('lote', False)

        default.setdefault('number', None)
        default.setdefault('state', 'draft')
        default.setdefault('accounting_date', None)
        default.setdefault('confirmed_move', None)
        default.setdefault('paid_move', None)
        default.setdefault('confirmed_cancel_move', None)
        default.setdefault('paid_cancel_move', None)
        default.setdefault('amount', Decimal('0'))
        if not lote:
            default.setdefault('lote', None)
        return super().copy(receipts, default=default)

    @classmethod
    def delete(cls, receipts):
        for receipt in receipts:
            if receipt.number:
                raise UserError(gettext(
                    'cooperative_ar.msg_receipt_delete_numbered',
                    receipt=receipt.rec_name))
        super().delete(receipts)

    @classmethod
    def get_sing_number(self, recibo_amount):
        '''
        Convert numbers in its equivalent string text
        representation in spanish
        '''
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
        for recibo in recibos:
            recibo.set_number()
            recibo.create_move()
        cls.write(recibos, {'state': 'confirmed'})

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelled')
    def cancel(cls, recibos):
        pool = Pool()
        Move = pool.get('account.move')
        Line = pool.get('account.move.line')
        Reconciliation = pool.get('account.move.reconciliation')

        cancel_moves = []
        delete_moves = []

        for recibo in recibos:
            reconciliations_c = [x.reconciliation
                for x in recibo.confirmed_move.lines
                if x.reconciliation]
            reconciliations_p = [x.reconciliation
                for x in recibo.paid_move.lines
                if x.reconciliation]
            with Transaction().set_user(0, set_context=True):
                if reconciliations_c:
                    Reconciliation.delete(reconciliations_c)
                if reconciliations_p:
                    Reconciliation.delete(reconciliations_p)

            if recibo.confirmed_move:
                recibo.confirmed_cancel_move = recibo.confirmed_move.cancel()
                recibo.save()
                cancel_moves.append(recibo.confirmed_cancel_move)
            if recibo.paid_move:
                recibo.paid_cancel_move = recibo.paid_move.cancel()
                recibo.save()
                cancel_moves.append(recibo.paid_cancel_move)

        if cancel_moves:
            Move.save(cancel_moves)
        if delete_moves:
            Move.delete(delete_moves)
        if cancel_moves:
            Move.post(cancel_moves)
        cls.write(recibos, {'state': 'cancelled'})

        for recibo in recibos:
            if not recibo.confirmed_move or not recibo.confirmed_cancel_move:
                continue
            to_reconcile = []
            for line in (recibo.confirmed_move.lines +
                    recibo.confirmed_cancel_move.lines):
                if line.account == recibo.account:
                    to_reconcile.append(line)
            Line.reconcile(to_reconcile)

            to_reconcile = []
            for line in recibo.paid_move.lines + recibo.paid_cancel_move.lines:
                if line.account == recibo.account:
                    to_reconcile.append(line)
            Line.reconcile(to_reconcile)

    def set_number(self):
        '''
        Set number to the receipt
        '''
        pool = Pool()
        Date = pool.get('ir.date')
        Configuration = pool.get('cooperative_ar.configuration')

        if self.number:
            return

        config = Configuration(1)
        sequence = config.recibo_sequence
        if not sequence:
            raise UserError(gettext(
                'cooperative_ar.msg_no_cooperative_sequence'))

        with Transaction().set_context(
                date=self.date or Date.today()):
            vals = {'number': sequence.get()}

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
    def get_context(cls, records, header, data):
        context = super().get_context(records, header, data)
        context['vat_number'] = cls.get_vat_number
        context['get_place'] = cls.get_place
        return context

    @classmethod
    def get_vat_number(cls, company):
        value = company.party.vat_number
        return cuit.format(value)

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
    'Recibo Transactions'
    __name__ = 'cooperative.partner.recibo.transactions.start'


class ReciboTransactions(Wizard):
    'Recibo Transactions'
    __name__ = 'cooperative.partner.recibo.transactions'

    start = StateView('cooperative.partner.recibo.transactions.start',
        'cooperative_ar.recibo_transactions_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Process', 'transactions', 'tryton-ok', default=True),
        ])
    transactions = StateReport(
        'cooperative.partner.recibo.transactions_report')

    def do_transactions(self, action):
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


class ReciboTransactionsReport(Report):
    'Recibo Transactions Report'
    __name__ = 'cooperative.partner.recibo.transactions_report'

    @classmethod
    def get_context(cls, records, header, data):

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

        context = super().get_context(records, header, data)
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
        return context

    @classmethod
    def _get_account_type(cls, record):
        '''
        Informacion del CBU
        CBU: '0': 'CC $' y '1': 'CA $'
        Importador transferencias BCCL: '1': 'CC $' y '2': 'CA $'
        '''
        cbu_number = cbu.compact(record.bank_account.rec_name.split("@")[0])
        return str(int(cbu_number[10]) + 1)

    @classmethod
    def _get_bank_code(cls, record):
        cbu_number = cbu.compact(record.bank_account.rec_name.split("@")[0])
        return cbu_number[0:3]

    @classmethod
    def _get_filial(cls, record):
        cbu_number = cbu.compact(record.bank_account.rec_name.split("@")[0])
        return cbu_number[4:7]

    @classmethod
    def _get_num_cuenta_mas_digito(cls, record):
        cbu_number = cbu.compact(record.bank_account.rec_name.split("@")[0])
        return cbu_number[14:-1]

    @classmethod
    def _get_digito_verificador(cls, record):
        cbu_number = cbu.compact(record.bank_account.rec_name.split("@")[0])
        return cbu_number[-2]

    @classmethod
    def _get_address(cls, record):
        pool = Pool()
        Party = pool.get('party.party')
        if Party and isinstance(record.party, Party):
            contact = record.party.contact_mechanism_get(
                'email', usage='invoice')
            if contact and contact.email:
                return contact.email
        return ''


class ReciboLote(Workflow, ModelSQL, ModelView):
    'Recibo Lote'
    __name__ = 'cooperative.partner.recibo.lote'

    _states = {'readonly': Eval('state') != 'draft'}
    _depends = ['state']

    number = fields.Char('Number', readonly=True, select=True)
    date = fields.Date('Date', states=_states, depends=_depends, required=True)
    description = fields.Char('Description', states=_states, depends=_depends)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ], 'State', readonly=True)
    journal = fields.Many2One('account.journal', "Journal", required=True,
        domain=[('type', '=', 'cash')], states=_states, depends=_depends)
    payment_method = fields.Many2One(
        'account.invoice.payment.method', "Payment Method", required=True,
        domain=[('company', '=', Eval('company'))],
        states=_states, depends=_depends + ['company'])
    company = fields.Many2One('company.company', 'Company', states=_states,
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ],
        depends=_depends, required=True, select=True)
    amount_recibos = fields.Function(fields.Numeric('Total Recibos',
        digits=(16, 2)), 'on_change_with_amount_recibos')
    recibos = fields.One2Many('cooperative.partner.recibo', 'lote',
        'Recibos', states=_states, depends=_depends)

    del _states, _depends

    @classmethod
    def __setup__(cls):
        super().__setup__()
        cls._transitions |= set((
                ('draft', 'confirmed'),
                ('confirmed', 'draft'),
                ('confirmed', 'cancelled'),
                ))
        cls._buttons.update({
                'cancel': {
                    'invisible': ~Eval('state').in_(['confirmed']),
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
        return 'retornos a cuenta de excedentes'

    @staticmethod
    def default_date():
        return Pool().get('ir.date').today()

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_amount_recibos():
        return Decimal('0')

    @fields.depends('recibos')
    def on_change_with_amount_recibos(self, name=None):
        total = Decimal('0')
        if self.recibos:
            for recibo in self.recibos:
                total += recibo.amount
        return total

    @fields.depends('recibos', 'company', 'journal', 'payment_method',
        'date', 'description')
    def on_change_description(self):
        self.add_recibos()

    @fields.depends('recibos', 'company', 'journal', 'payment_method',
        'date', 'description')
    def on_change_payment_method(self):
        self.add_recibos()

    @fields.depends('recibos', 'company', 'journal', 'payment_method',
        'date', 'description')
    def on_change_journal(self):
        self.add_recibos()

    @fields.depends('recibos', 'company', 'journal', 'payment_method',
        'date', 'description')
    def on_change_company(self):
        self.add_recibos()

    def add_recibos(self):
        pool = Pool()
        Recibo = pool.get('cooperative.partner.recibo')
        Partner = pool.get('cooperative.partner')
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
            recibo.description = self.description
            recibo.journal = self.journal
            recibo.payment_method = self.payment_method
            recibo.amount = partner.recibo_total or Decimal(0)
            recibo.state = recibo.default_state()
            lines.append(recibo)

        self.recibos = lines

    @classmethod
    def set_number(cls, lotes):
        '''
        Fill the number field with the lote sequence
        '''
        pool = Pool()
        Config = pool.get('cooperative_ar.configuration')

        config = Config(1)
        for lote in lotes:
            if lote.number:
                continue
            lote.number = config.recibo_lote_sequence.get()
        cls.save(lotes)

    @classmethod
    def copy(cls, lotes, default=None):
        if default is None:
            default = {}
        else:
            default = default.copy()
        default.setdefault('number', None)
        with Transaction().set_context(lote=True):
            return super().copy(lotes, default=default)

    @classmethod
    def delete(cls, lotes):
        for lote in lotes:
            if lote.number:
                raise UserError(gettext(
                    'cooperative_ar.msg_lot_delete_numbered',
                    lot=lote.rec_name))
        super().delete(lotes)

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, lotes):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelled')
    def cancel(cls, lotes):
        pool = Pool()
        Recibo = pool.get('cooperative.partner.recibo')

        for lote in lotes:
            Recibo.cancel(lote.recibos)

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmed')
    def confirm(cls, lotes):
        pool = Pool()
        Recibo = pool.get('cooperative.partner.recibo')

        cls.set_number(lotes)
        for lote in lotes:
            Recibo.confirm(lote.recibos)
