from trytond.pool import Pool
from .partner import *
from .meeting import *
from .vacation import *
from .partnermeeting import *
from .sanction import *
from .recibo import *
from .analytic_account import *
from . import configuration


def register():
    Pool.register(
        configuration.Configuration,
        Partner,
        Meeting,
        Vacation,
        PartnerMeeting,
        Sanction,
        Recibo,
        AnalyticAccountNota,
        PrintBalanceSocialStart,
        module='cooperative_ar', type_='model')
    Pool.register(
        PrintBalanceSocial,
        module='cooperative_ar', type_='wizard')
    Pool.register(
        ReciboReport,
        BalanceSocial,
        module='cooperative_ar', type_='report')
