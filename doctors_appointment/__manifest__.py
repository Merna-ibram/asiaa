{
    "name": "Doctor's Appointment",
    "author": 'Shins',
    'version': '0.1',
    'license': 'LGPL-3',
    "depends": ['base','hr','stock','report_xlsx', 'physiotherapy'],
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',

        "data/header.xml",

        'views/menu.xml',
        'views/patients_appoi.xml',

        'wizard/patient_wiz.xml',
        'wizard/appointment_report_wizard.xml',
        'wizard/doctor_invoices.xml',

        'report/doctor_appointment_report.xml',
        "report/patient_prescription_template.xml",
        "report/patient_prescription_view.xml",
        "report/doctor_invoices.xml",

    ]
}