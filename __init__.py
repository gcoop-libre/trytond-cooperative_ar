from trytond.pool import Pool
from .partner import *
from .meeting import *
from .vacation import *
from .partnermeeting import *
from .sanction import *
from .recibo import *
from .account import *
from .analytic_account import *


def register():
    Pool.register(Partner,
                  Meeting,
                  Vacation,
                  PartnerMeeting,
                  Sanction,
                  Recibo,
                  FiscalYear,
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
