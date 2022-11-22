from trytond.pool import Pool
from .partner import *
from .meeting import *
from .vacation import *
from .partnermeeting import *
from .sanction import *
from . import recibo
from .analytic_account import *
from . import inaes
from . import configuration


def register():
    Pool.register(
        configuration.Configuration,
        configuration.ConfigurationSequence,
        configuration.ConfigurationReceiptAccount,
        Partner,
        Meeting,
        Vacation,
        PartnerMeeting,
        Sanction,
        recibo.Recibo,
        AnalyticAccountNota,
        PrintBalanceSocialStart,
        recibo.Move,
        recibo.ReciboTransactionsStart,
        recibo.ReciboLote,
        inaes.ReciboInaesStart,
        module='cooperative_ar', type_='model')
    Pool.register(
        PrintBalanceSocial,
        recibo.ReciboTransactions,
        inaes.ReciboInaes,
        module='cooperative_ar', type_='wizard')
    Pool.register(
        recibo.ReciboReport,
        recibo.ReciboTransactionsReport,
        BalanceSocial,
        inaes.ReciboInaesReport,
        MeetingReport,
        module='cooperative_ar', type_='report')
