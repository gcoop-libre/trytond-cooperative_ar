from trytond.pool import Pool
from .partner import *
from .meeting import *
from .vacation import *
from .partnermeeting import *


def register():
    Pool.register(Partner, Meeting, Vacation, PartnerMeeting, module='cooperative_ar', type_='model')
