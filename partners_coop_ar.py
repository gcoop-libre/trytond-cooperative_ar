# Imports, for base primitives
from tryton_builder import Module, Model, Field, Relation


# ---------- Partner -------------- #
socio = Model('Partner', 'cooperative.partner')
socio.add_field(Field('Integer', 'File')) #Legajo
socio.add_field(Relation('Many2One', 'Party', 'party.party'))
socio.add_field(Relation('Many2One', 'Company', 'company.company'))
socio.add_field(Field('Char', 'First Name'))
socio.add_field(Field('Char', 'Last Name'))
socio.add_field(Field('Char', 'DNI'))
socio.add_field(Relation('Many2One', 'Nationality', 'country.country'))
socio.add_field(Field('Selection', 'Marital Status', options=[
    'Soltero/a', 'Casado/a', 'Divorciado/a', 'Viudo/a', 'Otra'
    ]))
socio.add_field(Field('Date', 'Incorporation Date'))
socio.add_field(Field('Numeric', 'Payed Quotes'))
socio.add_field(Field('Integer', 'Vacation Days'))
socio.add_field(Relation('One2Many', 'Vacation', 'cooperative.partner.vacation', field='partner'))
#Relacion con vacaciones

# ---------- Vacations ------------- #
#Relacion con Socios
vacations = Model('Vacation', 'cooperative.partner.vacation')
vacations.add_field(Field('Date', 'Start Date'))
vacations.add_field(Field('Date', 'End Date'))
vacations.add_field(Field('Integer', 'Days'))
vacations.add_field(Relation('Many2One', 'Partner', 'cooperative.partner'))
#relacion many to many con Meetings

# --------- Meetings --------------- #

reunion = Model('Meeting', 'cooperative.meeting')
reunion.add_field(Field('Selection', 'Type', options=[
    'Ordinaria', 'Extraordinaria', 'Reunion'
    ]))
reunion.add_field(Field('Selection', 'Status', options=[
    'Planned', 'Complete',
    ]))
reunion.add_field(Field('Date', 'Start Date'))
reunion.add_field(Field('Time', 'Start Time'))
reunion.add_field(Field('Time', 'End Time'))
# Campo para subir archivos
# Relacion con socios para los asistentes


# --------- Assignments ------------ #

module = Module('cooperative_ar')
module.add_dependence('company')
module.add_dependence('country')
module.add_dependence('party')

module.add_model(socio)
module.add_model(reunion)
module.add_model(vacations)

module.many2many(socio, reunion)
# Build!!
module.build()
# Our module is placed on HelloWorld dir
