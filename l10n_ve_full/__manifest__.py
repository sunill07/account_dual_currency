# -*- coding: utf-8 -*-
{
    'name': "Venezuela: Localización Completa",

    'summary': """
        Localización Venezolana""",
    'description': """
        Localización completa para Venezuela

    """,

    "version": "18.0.0.0",
    'author': 'José Luis Vizcaya López',
    'company': 'José Luis Vizcaya López',
    'maintainer': 'José Luis Vizcaya López',
    'website': 'https://vizcaya.mi-erp.app',
    'category': 'Localization',
    'depends': ['base', 'base_vat', 'base_address_extended', 'l10n_ve', 'contacts', 'account','account_accountant', "accountant",'account_debit_note', 'sale_management', 'purchase','stock', 'product'],
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/res.country.state.xml',
        'data/res.country.state.municipality.xml',
        'data/res.country.state.municipality.parish.xml',
        'views/res_partner.xml',
        #'views/res_company.xml',
        'views/sale_order.xml',
        'views/purchase_order.xml',
        'views/account_ut.xml',
        'views/account_tax.xml',
        'views/account_journal.xml',
        'wizard/search_info_partner_seniat.xml',
        'wizard/wizard_nro_ctrl_view.xml',
        'views/account_move.xml',
        'views/account_move_reversal.xml',
        'views/account_wh_iva.xml',
        'views/account_wh_iva_txt.xml',
        'report/account_wh_iva_report_comprobante.xml',
        'data/account_wh_iva_sequence.xml',
        'wizard/account_wh_iva_list.xml',
        'report/account_wh_iva_list.xml',
        'views/account_wh_islr_concept.xml',
        'data/account_wh_islr_concept_data.xml',
        'views/account_wh_islr_rates.xml',
        'data/account_wh_islr_rates_data.xml',
        'views/account_wh_islr_xml.xml',
        'views/account_wh_islr_doc.xml',
        'wizard/account_wh_islr_list.xml',
        'report/account_wh_islr_list.xml',
        'views/product_product.xml',
        'data/decimal_precision.xml',
        'data/account_wh_islr_doc_sequence.xml',
        #'data/account_wh_islr_doc_sequence_refund.xml',
        'report/account_wh_islr_report_comprobante.xml',
        'wizard/change_invoice_sin_cred_view.xml',
        'wizard/account_fiscal_book_wizard_view.xml',
        'views/account_fiscal_book.xml',
        'report/account_fiscal_book_report.xml',
        'report/account_fiscal_purchase_book_report.xml',
        'wizard/account_wizard_libro_resumen.xml',
        'views/account_payment.xml',
        'wizard/employee_income_wh_islr.xml',
        'wizard/account_inventory_book.xml',
        'report/account_inventary_book_report.xml',
        'views/res_config_settings.xml',
        'views/template_mail.xml',
        'views/account_wh_municipal_rates.xml',
    ],
    "license": "GPL-2",
    "price": 3500,
    "currency": "USD",
}