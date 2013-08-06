#! -*- coding: utf8 -*-
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, Equal

__all__ = ['Party']

class Party(ModelSQL, ModelView):
    """Pary module, extended for cooperative_ar"""

    __name__ = 'party.party'

    iva_condition = fields.Selection(
            [
                ('', ''),
                ('responsable_inscripto', 'Responsable Inscripto'),
                ('exento', 'Exento'),
                ('consumidor_final', 'Consumidor Final'),
            ],
            'Condicion ante el IVA',
            states={
                'readonly': ~Eval('active', True),
                'required': Equal(Eval('vat_country'), 'AR'),
                },

            )
