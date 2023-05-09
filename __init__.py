# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.

from trytond.pool import Pool
from . import partner
from . import meeting
from . import vacation
from . import sanction
from . import recibo
from . import analytic_account
from . import inaes
from . import configuration


def register():
    Pool.register(
        configuration.Configuration,
        configuration.ConfigurationSequence,
        configuration.ConfigurationReceiptAccount,
        configuration.ConfigurationSkill,
        partner.Partner,
        meeting.Meeting,
        meeting.PartnerMeeting,
        vacation.Vacation,
        sanction.Sanction,
        recibo.Recibo,
        analytic_account.AnalyticAccountNota,
        analytic_account.PrintBalanceSocialStart,
        recibo.Move,
        recibo.MoveLine,
        recibo.ReciboTransactionsStart,
        recibo.ReciboLote,
        inaes.ReciboInaesStart,
        module='cooperative_ar', type_='model')
    Pool.register(
        analytic_account.PrintBalanceSocial,
        recibo.ReciboTransactions,
        inaes.ReciboInaes,
        module='cooperative_ar', type_='wizard')
    Pool.register(
        recibo.ReciboReport,
        recibo.ReciboTransactionsReport,
        analytic_account.BalanceSocial,
        meeting.MeetingReport,
        inaes.ReciboInaesReport,
        module='cooperative_ar', type_='report')
