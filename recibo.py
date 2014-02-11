#! -*- coding: utf8 -*-
from trytond.model import ModelView, Workflow, ModelSQL, fields
from trytond.pyson import Eval

__all__ = ['Recibo']

class Recibo(Workflow, ModelSQL, ModelView):
    "cooperative_ar"
    __name__ = "cooperative.partner.recibo"
    date = fields.Date('Fecha',
            states={
                'readonly': (Eval('state') != 'draft')
            })
    monto = fields.Numeric('Monto',digits=(16,2),
            states={
                'readonly': (Eval('state') != 'draft')
            })
    partner = fields.Many2One('cooperative.partner', 'Partner', required=True,
            states={
                'readonly': (Eval('state') != 'draft')
            })
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirm'),
        ('paid', 'Paid'),
        ('cancel', 'Canceled'),
        ], 'State', readonly=True)

    @classmethod
    def __setup__(cls):
        super(Recibo, cls).__setup__()
        cls._transitions |= set((
                ('draft', 'confirmed'),
                ('draft', 'cancel'),
                ('confirmed', 'draft'),
                ('confirmed', 'paid'),
                ('confirmed', 'cancel'),
                ('cancel', 'draft'),
                ))

        cls._buttons.update({
                'cancel': {
                    'invisible': ~Eval('state').in_(['draft', 'confirmed']),
                    },
                'draft': {
                    'invisible': ~Eval('state').in_(['cancel','confirmed']),
                    },
                'paid': {
                    'invisible': ~Eval('state').in_(['confirmed']),
                    },
                'confirmed': {
                    'invisible': Eval('state').in_(['cancel', 'paid']),
                    },
                })

    @classmethod
    @ModelView.button
    @Workflow.transition('draft')
    def draft(cls, recibos):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('cancel')
    def cancel(cls, recibos):
        cls.write(recibos, {
                'state': 'cancel',
                })

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmed')
    def confirm(cls, recibos):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('paid')
    def paid(cls, recibos):
        pass

    @staticmethod
    def default_state():
        return 'draft'
