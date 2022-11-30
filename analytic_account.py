# This file is part of the cooperative_ar module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import datetime
from trytond.model import ModelView, ModelSQL, fields
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.wizard import Wizard, StateView, StateAction, Button
from trytond.report import Report

__all__ = ['AnalyticAccountNota', 'PrintBalanceSocialStart',
    'PrintBalanceSocial', 'BalanceSocial']


class AnalyticAccountNota(ModelSQL, ModelView):
    'Notes Analytic Account'
    __name__ = 'analytic_account.account.nota'

    name = fields.Char('Name')
    date = fields.Date('Date')
    note = fields.Text('Note')
    account = fields.Many2One('analytic_account.account', 'Account',
        domain=[
            ('root.name', '=', 'Balance Social Cooperativo'),
            ('type', '=', 'normal'),
        ], required=True, select=True)

    type = fields.Selection([
        ('line', 'Line'),
        ('subtotal', 'Subtotal'),
        ('title', 'Title'),
        ('comment', 'Comment'),
        ], 'Type', select=True, required=True)

    @staticmethod
    def default_type():
        return 'line'


class PrintBalanceSocialStart(ModelView):
    'Print Balance Social'
    __name__ = 'analytic_account.print_balance_social.start'

    from_date = fields.Date('From Date', required=True)
    to_date = fields.Date('To Date', required=True)
    company = fields.Many2One('company.company', 'Company', required=True)

    @staticmethod
    def default_from_date():
        Date = Pool().get('ir.date')
        return datetime.date(Date.today().year, 1, 1)

    @staticmethod
    def default_to_date():
        Date = Pool().get('ir.date')
        return Date.today()

    @staticmethod
    def default_company():
        return Transaction().context.get('company')


class PrintBalanceSocial(Wizard):
    'Print Balance Social'
    __name__ = 'analytic_account.print_balance_social'
    start = StateView('analytic_account.print_balance_social.start',
        'cooperative_ar.print_balance_social_start_view_form', [
            Button('Cancel', 'end', 'tryton-cancel'),
            Button('Print', 'print_', 'tryton-print', default=True),
            ])
    print_ = StateAction('cooperative_ar.report_balance_social')

    def do_print_(self, action):
        data = {
            'company': self.start.company.id,
            'from_date': self.start.from_date,
            'to_date': self.start.to_date,
            }
        return action, data

    def transition_print_(self):
        return 'end'


class BalanceSocial(Report):
    __name__ = 'cooperative_ar.report_balance_social'

    @classmethod
    def _get_records(cls, ids, model, data):
        AnalyticAccount = Pool().get('analytic_account.account')

        accounts = AnalyticAccount.search([
                ('type', '=', 'normal'),
                ('root.name', '=', 'Balance Social Cooperativo'),
                ])
        return accounts

    @classmethod
    def get_context(cls, records, data):
        report_context = super(BalanceSocial, cls).get_context(records, data)
        company = report_context['user'].company
        report_context['company'] = company
        report_context['digits'] = company.currency.digits
        report_context['from_date'] = data['from_date']
        report_context['to_date'] = data['to_date']
        report_context['get_analytic_lines'] = cls.get_analytic_lines
        report_context['has_analytic_lines'] = cls.has_analytic_lines
        report_context['get_partners'] = cls.get_partners
        report_context['get_partners_nuevos'] = cls.get_partners_nuevos
        report_context['get_partners_leave'] = cls.get_partners_leave
        report_context['get_partners_gender'] = cls.get_partners_gender
        report_context['get_meetings'] = cls.get_meetings
        report_context['get_notas'] = cls.get_notas
        report_context['has_notas'] = cls.has_notas
        report_context['get_analytic_accounts'] = cls.get_analytic_accounts
        report_context['get_analytic_subaccounts'] = \
            cls.get_analytic_subaccounts
        report_context['get_partners_birthdate'] = cls.get_partners_birthdate
        report_context['get_birthdate'] = cls.get_birthdate
        report_context['get_meeting_type'] = cls.get_meeting_type
        report_context['get_summary_meeting'] = cls.get_summary_meeting
        return report_context

    @classmethod
    def get_analytic_accounts(self, company):
        AnalyticAccount = Pool().get('analytic_account.account')

        accounts = AnalyticAccount.search([
                ('root.name', '=', 'Balance Social Cooperativo'),
                ('type', '=', 'view'),
                ])
        return accounts

    @classmethod
    def get_analytic_subaccounts(self, account_id):
        AnalyticAccount = Pool().get('analytic_account.account')

        accounts = AnalyticAccount.search([
                ('root.name', '=', 'Balance Social Cooperativo'),
                ('type', '=', 'normal'),
                ('parent', '=', account_id),
                ])
        return accounts

    @classmethod
    def get_notas(self, analytic_account_id, from_date, to_date):
        AnalyticAccountNota = Pool().get('analytic_account.account.nota')
        clause = [
            ('date', '>=', from_date),
            ('date', '<=', to_date),
            ('account', '=', analytic_account_id),
        ]
        notas = AnalyticAccountNota.search(clause, order=[
                ('date', 'ASC'), ('id', 'ASC')])

        return notas

    @classmethod
    def has_notas(self, analytic_account_id, from_date, to_date):
        AnalyticAccountNota = Pool().get('analytic_account.account.nota')
        clause = [
            ('date', '>=', from_date),
            ('date', '<=', to_date),
            ('account', '=', analytic_account_id),
        ]
        notas = AnalyticAccountNota.search(clause, order=[
                ('date', 'ASC'), ('id', 'ASC')])

        if notas == []:
            return False
        else:
            return True

    @classmethod
    def get_summary_meeting(self, from_date, to_date, type):
        Meeting = Pool().get('cooperative.meeting')
        clause = [
            ('start_date', '>=', from_date),
            ('start_date', '<=', to_date),
            ('status', '=', 'complete'),
            ('type', '=', type),
        ]

        return len(Meeting.search(clause))

    @classmethod
    def get_meetings(self, from_date, to_date):
        Meeting = Pool().get('cooperative.meeting')
        clause = [
            ('start_date', '>=', from_date),
            ('start_date', '<=', to_date),
            ('status', '=', 'complete'),
        ]

        meetings = Meeting.search(clause, order=[
                ('start_date', 'ASC'), ('type', 'ASC'), ('id', 'ASC')])

        return meetings

    @classmethod
    def get_meeting_type(self, type):
        Meeting = Pool().get('cooperative.meeting')
        return dict(Meeting._fields['type'].selection)[type]

    @classmethod
    def get_birthdate(self, partner):
        from dateutil.relativedelta import relativedelta
        from datetime import datetime

        today = datetime.now()
        age = relativedelta(today, partner.birthdate)  # calculate age

        return age.years

    @classmethod
    def get_partners_birthdate(self):
        CooperativePartner = Pool().get('cooperative.partner')
        clause = [
            ('status', '=', 'active'),
        ]

        partners = CooperativePartner.search(clause, order=[
                ('last_name', 'ASC'), ('id', 'ASC')])

        return partners

    @classmethod
    def get_partners(self):
        CooperativePartner = Pool().get('cooperative.partner')
        clause = [
            ('status', '=', 'active'),
        ]

        partners = CooperativePartner.search(clause, order=[
                ('last_name', 'ASC'), ('id', 'ASC')])

        return partners

    @classmethod
    def get_partners_leave(self, from_date, to_date):
        CooperativePartner = Pool().get('cooperative.partner')
        clause = [
            ('leaving_date', '>=', from_date),
            ('leaving_date', '<=', to_date),
            ('status', '=', 'give_up'),
        ]

        partners = CooperativePartner.search(clause, order=[
                ('last_name', 'ASC'), ('id', 'ASC')])

        return partners

    @classmethod
    def get_partners_nuevos(self, from_date, to_date):
        CooperativePartner = Pool().get('cooperative.partner')
        clause = [
            ('incorporation_date', '>=', from_date),
            ('incorporation_date', '<=', to_date),
            ('status', '=', 'active'),
        ]

        partners = CooperativePartner.search(clause, order=[
                ('last_name', 'ASC'), ('id', 'ASC')])

        return partners

    @classmethod
    def get_partners_gender(self, from_date, to_date, gender):
        CooperativePartner = Pool().get('cooperative.partner')
        clause = [
            ('status', '=', 'active'),
            ('gender', '=', gender),
        ]

        return len(CooperativePartner.search(clause))

    @classmethod
    def get_analytic_lines(self, analytic_account_id, from_date, to_date):
        AnalyticAccountLine = Pool().get('analytic_account.line')
        clause = [
            ('date', '>=', from_date),
            ('date', '<=', to_date),
            ('account', '=', analytic_account_id),
        ]

        lines = AnalyticAccountLine.search(clause, order=[
                ('date', 'ASC'), ('id', 'ASC')])

        return lines

    @classmethod
    def has_analytic_lines(self, analytic_account_id, from_date, to_date):
        AnalyticAccountLine = Pool().get('analytic_account.line')
        clause = [
            ('date', '>=', from_date),
            ('date', '<=', to_date),
            ('account', '=', analytic_account_id),
        ]

        lines = AnalyticAccountLine.search(clause, order=[
                ('date', 'ASC'), ('id', 'ASC')])

        if lines == []:
            return False
        else:
            return True
