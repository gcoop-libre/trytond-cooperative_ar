====================
Cooperative Scenario
====================

Imports::

    >>> import datetime
    >>> from decimal import Decimal
    >>> from dateutil.relativedelta import relativedelta
    >>> from proteus import Model, Wizard, Report
    >>> from trytond.tests.tools import activate_modules, set_user
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> from trytond.modules.account.tests.tools import create_fiscalyear, \
    ...     create_chart, get_accounts
    >>> from trytond.modules.account_invoice.tests.tools import \
    ...     set_fiscalyear_invoice_sequences
    >>> today = datetime.date.today()

Install sale_subscription::

    >>> config = activate_modules('cooperative_ar')

Create company::

    >>> _ = create_company()
    >>> company = get_company()
    >>> tax_identifier = company.party.identifiers.new()
    >>> tax_identifier.type = 'ar_cuit'
    >>> tax_identifier.code = '30710158254' # gcoop CUIT
    >>> company.party.iva_condition = 'responsable_inscripto'
    >>> company.party.save()

Create coop user::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')

    >>> user = User()
    >>> user.name = 'coop'
    >>> user.login = 'coop'
    >>> user.main_company = company
    >>> group, = Group.find([('name', '=', 'Cooperatives')])
    >>> user.groups.append(group)
    >>> user.save()

Create fiscal year::

    >>> fiscalyear = set_fiscalyear_invoice_sequences(
    ...     create_fiscalyear(company))
    >>> fiscalyear.click('create_period')
    >>> period = fiscalyear.periods[0]
    >>> period_ids = [p.id for p in fiscalyear.periods]

Create chart of accounts::

    >>> _ = create_chart(company)
    >>> accounts = get_accounts(company)
    >>> payable = accounts['payable']
    >>> expense = accounts['expense']
    >>> account_cash = accounts['cash']

Create countries::

    >>> Country = Model.get('country.country')
    >>> Subdivision = Model.get('country.subdivision')
    >>> country_us = Country(
    ...     name="United States", code="US", code3="USA", code_numeric="840")
    >>> country_us.save()
    >>> california = Subdivision(
    ...     name="California", code="US-CA", type='state', country=country_us)
    >>> california.save()

Create payment method::

    >>> Journal = Model.get('account.journal')
    >>> PaymentMethod = Model.get('account.invoice.payment.method')
    >>> Sequence = Model.get('ir.sequence')
    >>> journal, = Journal.find([('type', '=', 'cash')])
    >>> payment_method = PaymentMethod()
    >>> payment_method.name = 'Cash'
    >>> payment_method.journal = journal
    >>> payment_method.credit_account = account_cash
    >>> payment_method.debit_account = account_cash
    >>> payment_method.save()

Create party::

    >>> Party = Model.get('party.party')
    >>> party = Party(name='Partner')
    >>> address, = party.addresses
    >>> address.country = country_us
    >>> address.subdivision = california
    >>> party.save()

Configure Cooperative::

    >>> CoopConfig = Model.get('cooperative_ar.configuration')

    >>> coop_config = CoopConfig(1)
    >>> coop_config.receipt_account_payable = payable
    >>> coop_config.receipt_account_receivable = expense
    >>> coop_config.save()

Set cooperative user::

    >>> set_user(user.id)

Create Partner::

    >>> Partner = Model.get('cooperative.partner')

    >>> partner = Partner()
    >>> partner.party = party
    >>> partner.file = 1
    >>> partner.company = company
    >>> partner.first_name = 'Lorem'
    >>> partner.last_name = 'Ipsum'
    >>> partner.gender = 'male'
    >>> partner.dni = '11111111'
    >>> partner.nationality = country_us
    >>> partner.marital_status = 'otra'
    >>> partner.incorporation_date = today
    >>> partner.meeting_date_of_incoroporation = today
    >>> partner.birthdate = today
    >>> partner.save()

Create Meeting::

    >>> Meeting = Model.get('cooperative.meeting')

    >>> meeting = Meeting()
    >>> meeting.type = 'ordinaria'
    >>> meeting.status = 'complete'
    >>> meeting.start_date = today
    >>> meeting.start_time = datetime.time(15, 0, 0)
    >>> meeting.end_time = datetime.time(16, 0, 0)
    >>> meeting.record = 'Lorem Ipsum'
    >>> meeting.partners.append(partner)
    >>> meeting.save()

Testing the report::

    >>> meeting_report = Report('cooperative.meeting')
    >>> ext, _, _, name = meeting_report.execute([meeting], {})
    >>> ext
    'odt'
    >>> name
    'Meeting'

Create Recibo::

    >>> Recibo = Model.get('cooperative.partner.recibo')

    >>> recibo = Recibo()
    >>> recibo.partner = partner
    >>> recibo.amount = Decimal('100')
    >>> recibo.payment_method = payment_method
    >>> recibo.journal = journal
    >>> recibo.save()
    >>> recibo.click('confirm')
    >>> recibo.state
    'confirmed'

Create new Recibo::

    >>> recibo, = recibo.duplicate()
    >>> recibo.state
    'draft'
    >>> recibo.number
    >>> recibo.amount = Decimal('100')
    >>> recibo.payment_method = payment_method
    >>> recibo.journal = journal
    >>> recibo.save()
    >>> recibo.click('confirm')
    >>> recibo.state
    'confirmed'

Create Lote::

    >>> Lote = Model.get('cooperative.partner.recibo.lote')

    >>> lote = Lote()
    >>> lote.state
    'draft'
    >>> lote.number
    >>> lote.payment_method = payment_method
    >>> lote.journal = journal
    >>> recibo, = lote.recibos
    >>> recibo.amount = Decimal('100')
    >>> lote.save()
    >>> lote.click('confirm')
    >>> lote.state
    'confirmed'

Create new Lote::

    >>> lote, = lote.duplicate()
    >>> lote.state
    'draft'
    >>> lote.number
    >>> lote.payment_method = payment_method
    >>> lote.journal = None
    >>> lote.journal = journal
    >>> recibo, = lote.recibos
    >>> recibo.amount = Decimal('100')
    >>> lote.save()
    >>> lote.click('confirm')
    >>> lote.state
    'confirmed'
