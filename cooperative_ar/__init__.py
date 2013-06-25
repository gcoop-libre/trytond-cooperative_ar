from trytond.pool import Pool
from .partner import *
from .meeting import *
from .vacation import *
from .partnermeeting import *
from .party import *


def register():
    Pool.register(Partner, Meeting, Vacation, PartnerMeeting, Party, module='cooperative_ar', type_='model')
