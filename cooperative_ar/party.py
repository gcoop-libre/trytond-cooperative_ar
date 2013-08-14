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

    @staticmethod
    def default_vat_country():
        return 'AR'

    @classmethod
    def __setup__(cls):
        super(Party, cls).__setup__()
        cls._error_messages.update({
            'unique_vat_number': 'The VAT number must be unique in each country.',
            })

    @classmethod
    def create(cls, vlist):
        for vals in vlist:
            if 'vat_number' in vals and 'vat_country' in vals:
                data = cls.search([('vat_number','=', vals['vat_number']),
                                   ('vat_country','=', vals['vat_country']),
                                  ])
                if data:
                    cls.raise_user_error('unique_vat_number')

        return super(Party, cls).create(vlist)

    @classmethod
    def write(cls, parties, vals):
        if 'vat_number' in vals and 'vat_country' in vals:
            data = cls.search([('vat_number','=', vals['vat_number']),
                               ('vat_country','=', vals['vat_country']),
                              ])
            if data and data != parties:
                cls.raise_user_error('unique_vat_number')

        return super(Party, cls).write(parties, vals)
        pass
