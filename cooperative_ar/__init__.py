from trytond.pool import Pool
from .partner import *
from .meeting import *
from .vacation import *
from .partnermeeting import *
from .party import *
from .address import *
from .sanction import *


def register():
    Pool.register(Partner,
                  Meeting,
                  Vacation,
                  PartnerMeeting,
                  Party,
                  Address,
                  Sanction,
                  module='cooperative_ar', type_='model'
                  )
