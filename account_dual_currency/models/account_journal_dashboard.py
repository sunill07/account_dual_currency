# -*- coding: utf-8 -*-

import ast
from babel.dates import format_datetime, format_date
from collections import defaultdict
from datetime import datetime, timedelta
import json
import random
from odoo import models, api, _, fields
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.release import version
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF, SQL
from odoo.tools.misc import formatLang, format_date as odoo_format_date, get_lang

def group_by_journal(vals_list):
    res = defaultdict(list)
    for vals in vals_list:
        res[vals['journal_id']].append(vals)
    return res

class account_journal(models.Model):
    _inherit = "account.journal"

    def _fill_sale_purchase_dashboard_data(self, dashboard_data):
        """Populate all sale and purchase journal's data dict with relevant information for the kanban card."""
        sale_purchase_journals = self.filtered(lambda journal: journal.type in ('sale', 'purchase'))
        purchase_journals = self.filtered(lambda journal: journal.type == 'purchase')
        sale_journals = self.filtered(lambda journal: journal.type == 'sale')
        if not sale_purchase_journals:
            return
        currency_id_dif = sale_purchase_journals[0].company_id.currency_id_dif
        bills_field_list = [
            "account_move.journal_id",
            "(CASE WHEN account_move.move_type IN ('out_refund', 'in_refund') THEN -1 ELSE 1 END) * account_move.amount_residual AS amount_total",
            "(CASE WHEN account_move.move_type IN ('in_invoice', 'in_refund', 'in_receipt') THEN -1 ELSE 1 END) * account_move.amount_total_usd AS amount_total_company",
            "account_move.currency_id AS currency",
            "account_move.move_type",
            "account_move.invoice_date",
            "account_move.company_id",
        ]
        # DRAFTS

        query, params = sale_purchase_journals._get_draft_sales_purchases_query().select(*bills_field_list)
        self.env.cr.execute(query, params)
        query_results_drafts = group_by_journal(self.env.cr.dictfetchall())

        # WAITING AND LATE BILLS AND PAYMENTS
        query_results_to_pay = {}
        late_query_results = {}
        for journal_type, journals in [('sale', sale_journals), ('purchase', purchase_journals)]:
            if not journals:
                continue

            query, selects = journals._get_open_sale_purchase_query(journal_type)
            sql = SQL("""%s
                    GROUP BY account_move.company_id, account_move.journal_id, account_move.currency_id, late, to_pay""",
                      query.select(*selects),
            )
            self.env.cr.execute(sql)
            query_result = group_by_journal(self.env.cr.dictfetchall())
            for journal in journals:
                query_results_to_pay[journal.id] = [r for r in query_result[journal.id] if r['to_pay']]
                late_query_results[journal.id] = [r for r in query_result[journal.id] if r['late']]

        to_check_vals = {
            journal.id: (amount_total_signed_sum, count)
            for journal, amount_total_signed_sum, count in self.env['account.move']._read_group(
                domain=[
                    *self.env['account.move']._check_company_domain(self.env.companies),
                    ('journal_id', 'in', sale_purchase_journals.ids),
                    ('checked', '=', False),
                    ('state', '=', 'posted'),
                ],
                groupby=['journal_id'],
                aggregates=['amount_total_signed:sum', '__count'],
            )
        }

        self.env.cr.execute(SQL("""
            SELECT id, moves_exists
            FROM account_journal journal
            LEFT JOIN LATERAL (
                SELECT EXISTS(SELECT 1
                              FROM account_move move
                              WHERE move.journal_id = journal.id
                              AND move.company_id = ANY (%(companies_ids)s) AND
                                  move.journal_id = ANY (%(journal_ids)s)) AS moves_exists
            ) moves ON TRUE
            WHERE journal.id = ANY (%(journal_ids)s);
        """,
            journal_ids=sale_purchase_journals.ids,
            companies_ids=self.env.companies.ids,
        ))
        is_sample_data_by_journal_id = {row[0]: not row[1] for row in self.env.cr.fetchall()}

        sale_purchase_journals._fill_dashboard_data_count(dashboard_data, 'account.move', 'entries_count', [])  
        for journal in sale_purchase_journals:
            # User may have read access on the journal but not on the company
            currency = journal.currency_id or self.env['res.currency'].browse(journal.company_id.sudo().currency_id.id)
            (number_waiting, sum_waiting) = self._count_results_and_sum_amounts(query_results_to_pay[journal.id], currency)
            (number_draft, sum_draft) = self._count_results_and_sum_amounts(query_results_drafts[journal.id], currency)
            (number_late, sum_late) = self._count_results_and_sum_amounts(late_query_results[journal.id], currency)
            amount_total_signed_sum, count = to_check_vals.get(journal.id, (0, 0))
            if journal.type == 'purchase':
                title_has_sequence_holes = _("Irregularities due to draft, cancelled or deleted bills with a sequence number since last lock date.")
                drag_drop_settings = {
                    'image': '/account/static/src/img/Bill.svg',
                    'text': _('Drop and let the AI process your bills automatically.'),
                }
            else:
                title_has_sequence_holes = _("Irregularities due to draft, cancelled or deleted invoices with a sequence number since last lock date.")
                drag_drop_settings = {
                    'image': '/web/static/img/quotation.svg',
                    'text': _('Drop to import your invoices.'),
                }

            dashboard_data[journal.id].update({
                'number_to_check': count,
                'to_check_balance': currency.format(amount_total_signed_sum),
                'title': _('Bills to pay') if journal.type == 'purchase' else _('Invoices owed to you'),
                'number_draft': number_draft,
                'number_waiting': number_waiting,
                'number_late': number_late,
                'sum_draft': currency.format(sum_draft),  # sign is already handled by the SQL query
                'sum_draft_usd': currency_id_dif.format(sum_draft * currency_id_dif.rate),
                'sum_waiting_usd': currency_id_dif.format(sum_waiting * currency_id_dif.rate * (1 if journal.type == 'sale' else -1)),
                'sum_waiting': currency.format(sum_waiting * (1 if journal.type == 'sale' else -1)),
                'sum_late': currency.format(sum_late * (1 if journal.type == 'sale' else -1)),
                'sum_late_usd': currency_id_dif.format(sum_late * currency_id_dif.rate * (1 if journal.type == 'sale' else -1)),
                'has_sequence_holes': journal.has_sequence_holes,
                'title_has_sequence_holes': title_has_sequence_holes,
                'has_unhashed_entries': journal.has_unhashed_entries,
                'is_sample_data': is_sample_data_by_journal_id[journal.id],
                'has_entries': not is_sample_data_by_journal_id[journal.id],
                'drag_drop_settings': drag_drop_settings,
            })
