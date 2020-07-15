# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.pool import Pool
from . import partner
from . import meeting
from . import vacation
from . import sanction
from . import recibo
from . import analytic_account
from . import configuration

__all__ = ['register']


def register():
    Pool.register(
        configuration.Configuration,
        configuration.ConfigurationSequence,
        configuration.ConfigurationReceiptAccount,
        partner.Partner,
        meeting.Meeting,
        meeting.PartnerMeeting,
        vacation.Vacation,
        sanction.Sanction,
        recibo.Recibo,
        analytic_account.AnalyticAccountNota,
        analytic_account.PrintBalanceSocialStart,
        recibo.Move,
        recibo.ReciboTransactionsStart,
        recibo.ReciboLote,
        module='cooperative_ar', type_='model')
    Pool.register(
        analytic_account.PrintBalanceSocial,
        recibo.ReciboTransactions,
        module='cooperative_ar', type_='wizard')
    Pool.register(
        recibo.ReciboReport,
        recibo.ReciboTransactionsReport,
        analytic_account.BalanceSocial,
        meeting.MeetingReport,
        module='cooperative_ar', type_='report')
