{
    'name'          : "Custom APP Clinic",
    'version'       : "1.0",
    'author'        : "Kevin",
    'website'       : "website",
    'category'      : 'Uncategorized',
    'summary'       : "not hospital, just clinic",
    'description'   : """
        for you that just feel fever, cough, or just need MC
    """,
    'depends'       : [
        'product',
        # 'account',
    ],
    'data'          : [
        "views/menu.xml",
        "views/res_partner.xml",
        "views/poly.xml",
        "views/register.xml",
        "views/checkup.xml",
        "views/clinic_css.xml",
        # "views/cancelled.xml",
        "views/product_template.xml",
        "wizard/reason_cancel_wizard.xml",
        "wizard/create_patient.xml",
        "report/report_prescription.xml",
        "report/clinic_invoice_report.xml",
        "report/invoice_card.xml",
        "security/ir.model.access.csv",
        "data/sequence.xml",
        "views/invoice.xml"
    ],
    'application'   : True,
    'installable'   : True,
    'auto_install'  : False,
}