#! -*- coding: utf8 -*-
from decimal import Decimal
from trytond.model import ModelView, Workflow, ModelSQL, fields
from trytond.pyson import Eval, If
from trytond.transaction import Transaction
from trytond.pool import Pool

__all__ = ['Recibo']

_DEPENDS = ['state']

_STATES = {
    'readonly': Eval('state') != 'draft',
}

class Recibo(Workflow, ModelSQL, ModelView):
    "cooperative_ar"
    __name__ = "cooperative.partner.recibo"
    date = fields.Date('Date',
            states={
                'readonly': (Eval('state') != 'draft')
            }, required=True)
    amount = fields.Numeric('Amount',digits=(16,2),
            states={
                'readonly': (Eval('state') != 'draft')
            }, required=True)
    partner = fields.Many2One('cooperative.partner', 'Partner', required=True,
            states={
                'readonly': (Eval('state') != 'draft')
            })
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirm'),
        ('paid', 'Paid'),
        ('cancel', 'Canceled'),
        ], 'State', readonly=True)
    number = fields.Char('Number', size=None, readonly=True, select=True)

    description = fields.Char('Description', size=None, states=_STATES,
        depends=_DEPENDS)

    ## Integrando con asientos
    party = fields.Many2One('party.party', 'Party',
        required=True, states=_STATES, depends=_DEPENDS,
        on_change=['party','type', 'company'])
    company = fields.Many2One('company.company', 'Company', required=True,
        states=_STATES, select=True, domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ],
        depends=_DEPENDS)
    account = fields.Many2One('account.account', 'Account', required=True,
        states=_STATES, depends=_DEPENDS + ['type'],
        domain=[
            ('company', '=', Eval('context', {}).get('company', -1)),
            If(Eval('type').in_(['out_invoice', 'out_credit_note']),
                ('kind', '=', 'receivable'),
                ('kind', '=', 'payable')),
            ])
    accounting_date = fields.Date('Accounting Date', states=_STATES,
        depends=_DEPENDS)
    move = fields.Many2One('account.move', 'Move', readonly=True)
    cancel_move = fields.Many2One('account.move', 'Cancel Move', readonly=True,
        states={
            'invisible': Eval('type').in_(['out_invoice', 'out_credit_note']),
            })
    journal = fields.Many2One('account.journal', 'Journal', required=True,
        states=_STATES, depends=_DEPENDS)
    currency = fields.Many2One('currency.currency', 'Currency', required=True,
        states={
            'readonly': ((Eval('state') != 'draft')
                | (Eval('lines') & Eval('currency'))),
            }, depends=['state', 'lines'])
    currency_digits = fields.Function(fields.Integer('Currency Digits',
        on_change_with=['currency']), 'on_change_with_currency_digits')
    currency_date = fields.Function(fields.Date('Currency Date',
        on_change_with=['invoice_date']), 'on_change_with_currency_date',)

    @classmethod
    def __setup__(cls):
        super(Recibo, cls).__setup__()
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

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, recibos):
        Move = Pool().get('account.move')

        moves = []
        for recibo in recibos:
            if recibo.move:
                moves.append(recibo.move)
        if moves:
            with Transaction().set_user(0, set_context=True):
                Move.delete(moves)

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmed')
    def confirmed(cls, recibos):
        for recibo in recibos:
            recibo.set_number()
            recibo.create_move()

        cls.write(recibos, {
                'state': 'confirmed',
                })

    @classmethod
    @ModelView.button
    @Workflow.transition('paid')
    def paid(cls, recibos):
        cls.write(recibos, {
                'state': 'paid',
                })

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

    def set_number(self):
        '''
        Set number to the receipt
        '''
        if self.number:
            return

        vals = {'number': '001-0001'}
        self.write([self], vals)
        ### Original set_number. Ver como hacemos la sequence.
        #'''
        #Set number to the invoice
        #'''
        #pool = Pool()
        #Period = pool.get('account.period')
        #Sequence = pool.get('ir.sequence.strict')
        #Date = pool.get('ir.date')

        #if self.number:
        #    return

        #test_state = True
        #if self.type in ('in_invoice', 'in_credit_note'):
        #    test_state = False

        #accounting_date = self.accounting_date or self.invoice_date
        #period_id = Period.find(self.company.id,
        #    date=accounting_date, test_state=test_state)
        #period = Period(period_id)
        #sequence = period.get_invoice_sequence(self.type)
        #if not sequence:
        #    self.raise_user_error('no_invoice_sequence', {
        #            'invoice': self.rec_name,
        #            'period': period.rec_name,
        #            })
        #with Transaction().set_context(
        #        date=self.invoice_date or Date.today()):
        #    number = Sequence.get_id(sequence.id)
        #    vals = {'number': number}
        #    if (not self.invoice_date
        #            and self.type in ('out_invoice', 'out_credit_note')):
        #        vals['invoice_date'] = Transaction().context['date']
        #self.write([self], vals)

    def _get_move_line(self, date, amount):
        '''
        Return move line
        '''
        Currency = Pool().get('currency.currency')
        res = {}
        if self.currency.id != self.company.currency.id:
            with Transaction().set_context(date=self.currency_date):
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
        res['account'] = self.account.id
        res['maturity_date'] = date
        res['description'] = self.description
        res['party'] = self.party.id
        return res

    def create_move(self):
        '''
        Create account move for the invoice and return the created move
        '''
        pool = Pool()
        Move = pool.get('account.move')
        Period = pool.get('account.period')
        Date = pool.get('ir.date')

        if self.move:
            return self.move
        ##[{'party': 4, 'account': 93, 'description': u'Desarrollo de Software',
        # 'tax_lines': [('create', [{'amount': Decimal('1200.00'), 'code': 4, 'tax': 1}])],
        # 'credit': Decimal('1200.00'), 'debit': Decimal('0.0'), 'second_currency': None,
        # 'amount_second_currency': Decimal('0.0')}]
        # (Pdb) term_lines
        # [(datetime.date(2014, 2, 20), Decimal('-1452.00'))]
        # -> val = self._get_move_line(date, amount)
        # (Pdb) val
        # {'party': 4, 'account': 13, 'maturity_date': datetime.date(2014, 2, 20), 'description': u'', 'credit': Decimal('0.0'), 'debit': Decimal('1452.00'), 'second_currency': None, 'amount_second_currency': Decimal('0.0')}
        # (Pdb) move_lines
        # [
        #  {'party': 4, 'account': 93, 'description': u'Desarrollo de Software', 'tax_lines': [('create', [{'amount': Decimal('1200.00'), 'code': 4, 'tax': 1}])], 'credit': Decimal('1200.00'), 'debit': Decimal('0.0'), 'second_currency': None, 'amount_second_currency': Decimal('0.0')},
        #  {'party': 4, 'account': 62, 'description': u'IVA Asociado a ventas - 21%', 'credit': Decimal('252.00'), 'debit': Decimal('0.0'), 'second_currency': None, 'amount_second_currency': Decimal('0.0')},
        #  {'party': 4, 'account': 13, 'maturity_date': datetime.date(2014, 2, 20), 'description': u'', 'credit': Decimal('0.0'), 'debit': Decimal('1452.00'), 'second_currency': None, 'amount_second_currency': Decimal('0.0')}
        # ]
        # (Pdb) str(self)
        # 'account.invoice,21'


        move_lines = []
        val = self._get_move_line(Date.today(), self.amount)
        move_lines.append(val)

        accounting_date = self.accounting_date or self.date
        period_id = Period.find(self.company.id, date=accounting_date)
        #import pdb; pdb.set_trace()

        move, = Move.create([{
                    'journal': self.journal.id,
                    'period': period_id,
                    'date': self.date,
        #            'origin': str(self),
                    'lines': [('create', move_lines)],
                    }])
        self.write([self], {
                'move': move.id,
                })
        return move
