# -*- coding: utf-8 -*-
# vencida por cobrar y pagar
from odoo import models, fields

from dateutil.relativedelta import relativedelta
from itertools import chain
from odoo.tools import SQL


class AgedPartnerBalanceCustomHandler(models.AbstractModel):
    _inherit = 'account.aged.partner.balance.report.handler'

    # def _aged_partner_report_custom_engine_common(self, options, internal_type, current_groupby, next_groupby, offset=0, limit=None):
    #     report = self.env['account.report'].browse(options['report_id'])
    #     report._check_groupby_fields((next_groupby.split(',') if next_groupby else []) + ([current_groupby] if current_groupby else []))
    #     currency_dif = options['currency_dif']
    #     def minus_days(date_obj, days):
    #         return fields.Date.to_string(date_obj - relativedelta(days=days))

    #     date_to = fields.Date.from_string(options['date']['date_to'])
    #     periods = [
    #         (False, fields.Date.to_string(date_to)),
    #         (minus_days(date_to, 1), minus_days(date_to, 30)),
    #         (minus_days(date_to, 31), minus_days(date_to, 60)),
    #         (minus_days(date_to, 61), minus_days(date_to, 90)),
    #         (minus_days(date_to, 91), minus_days(date_to, 120)),
    #         (minus_days(date_to, 121), False),
    #     ]

    #     def build_result_dict(report, query_res_lines):
    #         rslt = {f'period{i}': 0 for i in range(len(periods))}

    #         for query_res in query_res_lines:
    #             for i in range(len(periods)):
    #                 period_key = f'period{i}'
    #                 rslt[period_key] += query_res[period_key]

    #         if current_groupby == 'id':
    #             query_res = query_res_lines[0] # We're grouping by id, so there is only 1 element in query_res_lines anyway
    #             currency = self.env['res.currency'].browse(query_res['currency_id'][0]) if len(query_res['currency_id']) == 1 else None
    #             expected_date = len(query_res['expected_date']) == 1 and query_res['expected_date'][0] or len(query_res['due_date']) == 1 and query_res['due_date'][0]
    #             rslt.update({
    #                 'invoice_date': query_res['invoice_date'][0] if len(query_res['invoice_date']) == 1 else None,
    #                 'due_date': query_res['due_date'][0] if len(query_res['due_date']) == 1 else None,
    #                 'amount_currency': None,
    #                 'currency_id': query_res['currency_id'][0] if len(query_res['currency_id']) == 1 else None,
    #                 'currency': None,
    #                 'account_name': query_res['account_name'][0] if len(query_res['account_name']) == 1 else None,
    #                 'expected_date': expected_date or None,
    #                 'total': None,
    #                 'has_sublines': query_res['aml_count'] > 0,

    #                 # Needed by the custom_unfold_all_batch_data_generator, to speed-up unfold_all
    #                 'partner_id': query_res['partner_id'][0] if query_res['partner_id'] else None,
    #             })
    #         else:
    #             rslt.update({
    #                 'invoice_date': None,
    #                 'due_date': None,
    #                 'amount_currency': None,
    #                 'currency_id': None,
    #                 'currency': None,
    #                 'account_name': None,
    #                 'expected_date': None,
    #                 'total': sum(rslt[f'period{i}'] for i in range(len(periods))),
    #                 'has_sublines': False,
    #             })

    #         return rslt

    #     # Build period table
    #     period_table_format = ('(VALUES %s)' % ','.join("(%s, %s, %s)" for period in periods))
    #     params = list(chain.from_iterable(
    #         (period[0] or None, period[1] or None, i)
    #         for i, period in enumerate(periods)
    #     ))
    #     period_table = self.env.cr.mogrify(period_table_format, params).decode(self.env.cr.connection.encoding)

    #     # Build query
    #     tables, where_clause, where_params = report._query_get(options, 'strict_range', domain=[('account_id.account_type', '=', internal_type)])

    #     currency_table = report._get_query_currency_table(options)
    #     always_present_groupby = "period_table.period_index, currency_table.rate, currency_table.precision"
    #     if current_groupby:
    #         select_from_groupby = f"account_move_line.{current_groupby} AS grouping_key,"
    #         groupby_clause = f"account_move_line.{current_groupby}, {always_present_groupby}"
    #     else:
    #         select_from_groupby = ''
    #         groupby_clause = always_present_groupby
    #     if currency_dif == self.env.company.currency_id.symbol:
    #         select_period_query = ','.join(
    #             f"""
    #                 CASE WHEN period_table.period_index = {i}
    #                 THEN %s * (
    #                     SUM(ROUND(account_move_line.balance * currency_table.rate, currency_table.precision))
    #                     - COALESCE(SUM(ROUND(part_debit.amount * currency_table.rate, currency_table.precision)), 0)
    #                     + COALESCE(SUM(ROUND(part_credit.amount * currency_table.rate, currency_table.precision)), 0)
    #                 )
    #                 ELSE 0 END AS period{i}
    #             """
    #             for i in range(len(periods))
    #         )
    #     else:
    #         select_period_query = ','.join(
    #             f"""
    #                             CASE WHEN period_table.period_index = {i}
    #                             THEN %s * (
    #                                 SUM(ROUND(account_move_line.balance_usd, currency_table.precision))
    #                                 - COALESCE(SUM(ROUND(part_debit.amount, currency_table.precision)), 0)
    #                                 + COALESCE(SUM(ROUND(part_credit.amount, currency_table.precision)), 0)
    #                             )
    #                             ELSE 0 END AS period{i}
    #                         """
    #             for i in range(len(periods))
    #         )

    #     tail_query, tail_params = report._get_engine_query_tail(offset, limit)
    #     if currency_dif == self.env.company.currency_id.symbol:
    #         query = f"""
    #                     WITH period_table(date_start, date_stop, period_index) AS ({period_table})

    #                     SELECT
    #                         {select_from_groupby}
    #                         %s * (
    #                             SUM(account_move_line.amount_currency)
    #                             - COALESCE(SUM(part_debit.debit_amount_currency), 0)
    #                             + COALESCE(SUM(part_credit.credit_amount_currency), 0)
    #                         ) AS amount_currency,
    #                         ARRAY_AGG(DISTINCT account_move_line.partner_id) AS partner_id,
    #                         ARRAY_AGG(account_move_line.payment_id) AS payment_id,
    #                         ARRAY_AGG(DISTINCT move.invoice_date) AS invoice_date,
    #                         ARRAY_AGG(DISTINCT COALESCE(account_move_line.date_maturity, account_move_line.date)) AS report_date,
    #                         ARRAY_AGG(DISTINCT account_move_line.expected_pay_date) AS expected_date,
    #                         ARRAY_AGG(DISTINCT account.code) AS account_name,
    #                         ARRAY_AGG(DISTINCT COALESCE(account_move_line.date_maturity, account_move_line.date)) AS due_date,
    #                         ARRAY_AGG(DISTINCT account_move_line.currency_id) AS currency_id,
    #                         COUNT(account_move_line.id) AS aml_count,
    #                         ARRAY_AGG(account.code) AS account_code,
    #                         {select_period_query}

    #                     FROM {tables}

    #                     JOIN account_journal journal ON journal.id = account_move_line.journal_id
    #                     JOIN account_account account ON account.id = account_move_line.account_id
    #                     JOIN account_move move ON move.id = account_move_line.move_id
    #                     JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id

    #                     LEFT JOIN LATERAL (
    #                         SELECT
    #                             SUM(part.amount) AS amount,
    #                             SUM(part.debit_amount_currency) AS debit_amount_currency,
    #                             part.debit_move_id
    #                         FROM account_partial_reconcile part
    #                         WHERE part.max_date <= %s
    #                         GROUP BY part.debit_move_id
    #                     ) part_debit ON part_debit.debit_move_id = account_move_line.id

    #                     LEFT JOIN LATERAL (
    #                         SELECT
    #                             SUM(part.amount) AS amount,
    #                             SUM(part.credit_amount_currency) AS credit_amount_currency,
    #                             part.credit_move_id
    #                         FROM account_partial_reconcile part
    #                         WHERE part.max_date <= %s
    #                         GROUP BY part.credit_move_id
    #                     ) part_credit ON part_credit.credit_move_id = account_move_line.id

    #                     JOIN period_table ON
    #                         (
    #                             period_table.date_start IS NULL
    #                             OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
    #                         )
    #                         AND
    #                         (
    #                             period_table.date_stop IS NULL
    #                             OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
    #                         )

    #                     WHERE {where_clause}

    #                     GROUP BY {groupby_clause}

    #                     HAVING
    #                         (
    #                             SUM(ROUND(account_move_line.debit * currency_table.rate, currency_table.precision))
    #                             - COALESCE(SUM(ROUND(part_debit.amount * currency_table.rate, currency_table.precision)), 0)
    #                         ) != 0
    #                         OR
    #                         (
    #                             SUM(ROUND(account_move_line.credit * currency_table.rate, currency_table.precision))
    #                             - COALESCE(SUM(ROUND(part_credit.amount * currency_table.rate, currency_table.precision)), 0)
    #                         ) != 0
    #                     {tail_query}
    #                 """
    #     else:
    #         query = f"""
    #                         WITH period_table(date_start, date_stop, period_index) AS ({period_table})

    #                         SELECT
    #                             {select_from_groupby}
    #                             %s * SUM(account_move_line.amount_currency) AS amount_currency,
    #                             ARRAY_AGG(DISTINCT account_move_line.partner_id) AS partner_id,
    #                             ARRAY_AGG(account_move_line.payment_id) AS payment_id,
    #                             ARRAY_AGG(DISTINCT move.invoice_date) AS invoice_date,
    #                             ARRAY_AGG(DISTINCT account_move_line.expected_pay_date) AS expected_date,
    #                             ARRAY_AGG(DISTINCT account.code) AS account_name,
    #                             ARRAY_AGG(DISTINCT COALESCE(account_move_line.date_maturity, account_move_line.date)) AS due_date,
    #                             ARRAY_AGG(DISTINCT account_move_line.currency_id) AS currency_id,
    #                             COUNT(account_move_line.id) AS aml_count,
    #                             ARRAY_AGG(account.code) AS account_code,
    #                             {select_period_query}

    #                         FROM {tables}

    #                         JOIN account_journal journal ON journal.id = account_move_line.journal_id
    #                         JOIN account_account account ON account.id = account_move_line.account_id
    #                         JOIN account_move move ON move.id = account_move_line.move_id
    #                         JOIN {currency_table} ON currency_table.company_id = account_move_line.company_id

    #                         # changes here
    #                         LEFT JOIN LATERAL (
    #                             SELECT SUM(part.amount_usd) AS amount, part.debit_move_id
    #                             FROM account_partial_reconcile part
    #                             WHERE part.max_date <= %s
    #                             GROUP BY part.debit_move_id
    #                         ) part_debit ON part_debit.debit_move_id = account_move_line.id

    #                         LEFT JOIN LATERAL (
    #                             SELECT SUM(part.amount_usd) AS amount, part.credit_move_id
    #                             FROM account_partial_reconcile part
    #                             WHERE part.max_date <= %s
    #                             GROUP BY part.credit_move_id
    #                         ) part_credit ON part_credit.credit_move_id = account_move_line.id

    #                         JOIN period_table ON
    #                             (
    #                                 period_table.date_start IS NULL
    #                                 OR COALESCE(account_move_line.date_maturity, account_move_line.date) <= DATE(period_table.date_start)
    #                             )
    #                             AND
    #                             (
    #                                 period_table.date_stop IS NULL
    #                                 OR COALESCE(account_move_line.date_maturity, account_move_line.date) >= DATE(period_table.date_stop)
    #                             )

    #                         WHERE {where_clause}

    #                         GROUP BY {groupby_clause}

    #                         HAVING (
    #                             SUM(ROUND(account_move_line.balance_usd, currency_table.precision))
    #                             - COALESCE(SUM(ROUND(part_debit.amount, currency_table.precision)), 0)
    #                             + COALESCE(SUM(ROUND(part_credit.amount, currency_table.precision)), 0)
    #                         ) != 0
    #                         {tail_query}
    #                     """

    #     multiplicator = -1 if internal_type == 'liability_payable' else 1
    #     params = [
    #         multiplicator,
    #         *([multiplicator] * len(periods)),
    #         date_to,
    #         date_to,
    #         *where_params,
    #         *tail_params,
    #     ]
    #     self._cr.execute(query, params)
    #     query_res_lines = self._cr.dictfetchall()

    #     if not current_groupby:
    #         return build_result_dict(report, query_res_lines)
    #     else:
    #         rslt = []

    #         all_res_per_grouping_key = {}
    #         for query_res in query_res_lines:
    #             grouping_key = query_res['grouping_key']
    #             all_res_per_grouping_key.setdefault(grouping_key, []).append(query_res)

    #         for grouping_key, query_res_lines in all_res_per_grouping_key.items():
    #             rslt.append((grouping_key, build_result_dict(report, query_res_lines)))

    #         return rslt

    def _aged_partner_report_custom_engine_common(self, options, internal_type, current_groupby, next_groupby, offset=0, limit=None):
        report = self.env['account.report'].browse(options['report_id'])
        report._check_groupby_fields((next_groupby.split(',') if next_groupby else []) + ([current_groupby] if current_groupby else []))
        currency_dif = options['currency_dif']


        def minus_days(date_obj, days):
            return fields.Date.to_string(date_obj - relativedelta(days=days))

        aging_date_field = SQL.identifier('invoice_date') if options['aging_based_on'] == 'base_on_invoice_date' else SQL.identifier('date_maturity')
        date_to = fields.Date.from_string(options['date']['date_to'])
        interval = options['aging_interval']
        periods = [(False, fields.Date.to_string(date_to))]
        # Since we added the first period in the list we have to do one less iteration
        nb_periods = len([column for column in options['columns'] if column['expression_label'].startswith('period')]) - 1
        for i in range(nb_periods):
            start_date = minus_days(date_to, (interval * i) + 1)
            # The last element of the list will have False for the end date
            end_date = minus_days(date_to, interval * (i + 1)) if i < nb_periods - 1 else False
            periods.append((start_date, end_date))

        def build_result_dict(report, query_res_lines):
            rslt = {f'period{i}': 0 for i in range(len(periods))}

            for query_res in query_res_lines:
                for i in range(len(periods)):
                    period_key = f'period{i}'
                    rslt[period_key] += query_res[period_key]

            if current_groupby == 'id':
                query_res = query_res_lines[0] # We're grouping by id, so there is only 1 element in query_res_lines anyway
                currency = self.env['res.currency'].browse(query_res['currency_id'][0]) if len(query_res['currency_id']) == 1 else None
                rslt.update({
                    'invoice_date': query_res['invoice_date'][0] if len(query_res['invoice_date']) == 1 else None,
                    'due_date': query_res['due_date'][0] if len(query_res['due_date']) == 1 else None,
                    'amount_currency': query_res['amount_currency'],
                    'currency_id': query_res['currency_id'][0] if len(query_res['currency_id']) == 1 else None,
                    'currency': currency.display_name if currency else None,
                    'account_name': query_res['account_name'][0] if len(query_res['account_name']) == 1 else None,
                    'total': None,
                    'has_sublines': query_res['aml_count'] > 0,

                    # Needed by the custom_unfold_all_batch_data_generator, to speed-up unfold_all
                    'partner_id': query_res['partner_id'][0] if query_res['partner_id'] else None,
                })
            else:
                rslt.update({
                    'invoice_date': None,
                    'due_date': None,
                    'amount_currency': None,
                    'currency_id': None,
                    'currency': None,
                    'account_name': None,
                    'total': sum(rslt[f'period{i}'] for i in range(len(periods))),
                    'has_sublines': False,
                })

            return rslt

        # Build period table
        period_table_format = ('(VALUES %s)' % ','.join("(%s, %s, %s)" for period in periods))
        params = list(chain.from_iterable(
            (period[0] or None, period[1] or None, i)
            for i, period in enumerate(periods)
        ))
        period_table = SQL(period_table_format, *params)

        # Build query
        query = report._get_report_query(options, 'strict_range', domain=[('account_id.account_type', '=', internal_type)])
        account_alias = query.left_join(lhs_alias='account_move_line', lhs_column='account_id', rhs_table='account_account', rhs_column='id', link='account_id')
        account_code = self.env['account.account']._field_to_sql(account_alias, 'code', query)

        always_present_groupby = SQL("period_table.period_index")
        if current_groupby:
            select_from_groupby = SQL("%s AS grouping_key,", SQL.identifier("account_move_line", current_groupby))
            groupby_clause = SQL("%s, %s", SQL.identifier("account_move_line", current_groupby), always_present_groupby)
        else:
            select_from_groupby = SQL()
            groupby_clause = always_present_groupby
        multiplicator = -1 if internal_type == 'liability_payable' else 1
        if currency_dif == self.env.company.currency_id.symbol: 
            select_period_query = SQL(',').join(
                SQL("""
                    CASE WHEN period_table.period_index = %(period_index)s
                    THEN %(multiplicator)s * SUM(%(balance_select)s)
                    ELSE 0 END AS %(column_name)s
                    """,
                    period_index=i,
                    multiplicator=multiplicator,
                    column_name=SQL.identifier(f"period{i}"),
                    balance_select=report._currency_table_apply_rate(SQL(
                        "account_move_line.balance - COALESCE(part_debit.amount, 0) + COALESCE(part_credit.amount, 0)"
                    )),
                )
                for i in range(len(periods))
            )
        else:
            select_period_query = SQL(',').join(
                SQL("""
                    CASE WHEN period_table.period_index = %(period_index)s
                    THEN %(multiplicator)s * SUM(%(balance_select)s)
                    ELSE 0 END AS %(column_name)s
                    """,
                    period_index=i,
                    multiplicator=multiplicator,
                    column_name=SQL.identifier(f"period{i}"),
                    balance_select=report._currency_table_apply_rate(SQL(
                        "account_move_line.balance_usd - COALESCE(part_debit.amount_usd, 0) + COALESCE(part_credit.amount_usd, 0)"
                    )),
                )
                for i in range(len(periods))
            )


        tail_query = report._get_engine_query_tail(offset, limit)
        if currency_dif == self.env.company.currency_id.symbol:

            query = SQL(
                """
                WITH period_table(date_start, date_stop, period_index) AS (%(period_table)s)

                SELECT
                    %(select_from_groupby)s
                    %(multiplicator)s * (
                        SUM(account_move_line.amount_currency)
                        - COALESCE(SUM(part_debit.debit_amount_currency), 0)
                        + COALESCE(SUM(part_credit.credit_amount_currency), 0)
                    ) AS amount_currency,
                    ARRAY_AGG(DISTINCT account_move_line.partner_id) AS partner_id,
                    ARRAY_AGG(account_move_line.payment_id) AS payment_id,
                    ARRAY_AGG(DISTINCT move.invoice_date) AS invoice_date,
                    ARRAY_AGG(DISTINCT COALESCE(account_move_line.%(aging_date_field)s, account_move_line.date)) AS report_date,
                    ARRAY_AGG(DISTINCT %(account_code)s) AS account_name,
                    ARRAY_AGG(DISTINCT COALESCE(account_move_line.%(aging_date_field)s, account_move_line.date)) AS due_date,
                    ARRAY_AGG(DISTINCT account_move_line.currency_id) AS currency_id,
                    COUNT(account_move_line.id) AS aml_count,
                    ARRAY_AGG(%(account_code)s) AS account_code,
                    %(select_period_query)s

                FROM %(table_references)s

                JOIN account_journal journal ON journal.id = account_move_line.journal_id
                JOIN account_move move ON move.id = account_move_line.move_id
                %(currency_table_join)s

                LEFT JOIN LATERAL (
                    SELECT
                        SUM(part.amount) AS amount,
                        SUM(part.debit_amount_currency) AS debit_amount_currency,
                        part.debit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <= %(date_to)s AND part.debit_move_id = account_move_line.id
                    GROUP BY part.debit_move_id
                ) part_debit ON TRUE

                LEFT JOIN LATERAL (
                    SELECT
                        SUM(part.amount) AS amount,
                        SUM(part.credit_amount_currency) AS credit_amount_currency,
                        part.credit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <= %(date_to)s AND part.credit_move_id = account_move_line.id
                    GROUP BY part.credit_move_id
                ) part_credit ON TRUE

                JOIN period_table ON
                    (
                        period_table.date_start IS NULL
                        OR COALESCE(account_move_line.%(aging_date_field)s, account_move_line.date) <= DATE(period_table.date_start)
                    )
                    AND
                    (
                        period_table.date_stop IS NULL
                        OR COALESCE(account_move_line.%(aging_date_field)s, account_move_line.date) >= DATE(period_table.date_stop)
                    )

                WHERE %(search_condition)s

                GROUP BY %(groupby_clause)s

                HAVING
                    ROUND(SUM(%(having_debit)s), %(currency_precision)s) != 0
                    OR ROUND(SUM(%(having_credit)s), %(currency_precision)s) != 0
                %(tail_query)s
                """,
                account_code=account_code,
                period_table=period_table,
                select_from_groupby=select_from_groupby,
                select_period_query=select_period_query,
                multiplicator=multiplicator,
                aging_date_field=aging_date_field,
                table_references=query.from_clause,
                currency_table_join=report._currency_table_aml_join(options),
                date_to=date_to,
                search_condition=query.where_clause,
                groupby_clause=groupby_clause,
                having_debit=report._currency_table_apply_rate(SQL("CASE WHEN account_move_line.balance > 0  THEN account_move_line.balance else 0 END - COALESCE(part_debit.amount, 0)")),
                having_credit=report._currency_table_apply_rate(SQL("CASE WHEN account_move_line.balance < 0  THEN -account_move_line.balance else 0 END - COALESCE(part_credit.amount, 0)")),
                currency_precision=self.env.company.currency_id.decimal_places,
                tail_query=tail_query,
            )
        else:
            query = SQL(
                """
                WITH period_table(date_start, date_stop, period_index) AS (%(period_table)s)

                SELECT
                    %(select_from_groupby)s
                    %(multiplicator)s * SUM(account_move_line.amount_currency) AS amount_currency,
                    ARRAY_AGG(DISTINCT account_move_line.partner_id) AS partner_id,
                    ARRAY_AGG(account_move_line.payment_id) AS payment_id,
                    ARRAY_AGG(DISTINCT move.invoice_date) AS invoice_date,
                    ARRAY_AGG(DISTINCT COALESCE(account_move_line.%(aging_date_field)s, account_move_line.date)) AS report_date,
                    ARRAY_AGG(DISTINCT %(account_code)s) AS account_name,
                    ARRAY_AGG(DISTINCT COALESCE(account_move_line.%(aging_date_field)s, account_move_line.date)) AS due_date,
                    ARRAY_AGG(DISTINCT account_move_line.currency_id) AS currency_id,
                    COUNT(account_move_line.id) AS aml_count,
                    ARRAY_AGG(%(account_code)s) AS account_code,
                    %(select_period_query)s

                FROM %(table_references)s

                JOIN account_journal journal ON journal.id = account_move_line.journal_id
                JOIN account_move move ON move.id = account_move_line.move_id
                %(currency_table_join)s

                LEFT JOIN LATERAL (
                    SELECT
                        SUM(part.amount_usd) AS amount,
                        part.debit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <= %(date_to)s AND part.debit_move_id = account_move_line.id
                    GROUP BY part.debit_move_id
                ) part_debit ON TRUE

                LEFT JOIN LATERAL (
                    SELECT
                        SUM(part.amount_usd) AS amount,
                        part.credit_move_id
                    FROM account_partial_reconcile part
                    WHERE part.max_date <= %(date_to)s AND part.credit_move_id = account_move_line.id
                    GROUP BY part.credit_move_id
                ) part_credit ON TRUE

                JOIN period_table ON
                    (
                        period_table.date_start IS NULL
                        OR COALESCE(account_move_line.%(aging_date_field)s, account_move_line.date) <= DATE(period_table.date_start)
                    )
                    AND
                    (
                        period_table.date_stop IS NULL
                        OR COALESCE(account_move_line.%(aging_date_field)s, account_move_line.date) >= DATE(period_table.date_stop)
                    )

                WHERE %(search_condition)s

                GROUP BY %(groupby_clause)s

                HAVING (
                    SUM(ROUND(account_move_line.balance_usd, %(currency_precision)s))
                    - COALESCE(SUM(ROUND(part_debit.amount, %(currency_precision)s)), 0)
                    + COALESCE(SUM(ROUND(part_credit.amount, %(currency_precision)s)), 0)
                    ) != 0



                %(tail_query)s
                """,
                account_code=account_code,
                period_table=period_table,
                select_from_groupby=select_from_groupby,
                select_period_query=select_period_query,
                multiplicator=multiplicator,
                aging_date_field=aging_date_field,
                table_references=query.from_clause,
                currency_table_join=report._currency_table_aml_join(options),
                date_to=date_to,
                search_condition=query.where_clause,
                groupby_clause=groupby_clause,
                currency_precision=self.env.company.currency_id.decimal_places,
                tail_query=tail_query,
            )


        self._cr.execute(query)
        query_res_lines = self._cr.dictfetchall()

        if not current_groupby:
            return build_result_dict(report, query_res_lines)
        else:
            rslt = []

            all_res_per_grouping_key = {}
            for query_res in query_res_lines:
                grouping_key = query_res['grouping_key']
                all_res_per_grouping_key.setdefault(grouping_key, []).append(query_res)

            for grouping_key, query_res_lines in all_res_per_grouping_key.items():
                rslt.append((grouping_key, build_result_dict(report, query_res_lines)))

            return rslt