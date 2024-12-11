# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools.misc import get_lang
from odoo.tools import SQL



class CashFlowReportCustomHandler(models.AbstractModel):
    _inherit = 'account.cash.flow.report.handler'

    # Migration Note: Done
    def _compute_liquidity_balance(self, report, options, payment_account_ids, date_scope):
        ''' Compute the balance of all liquidity accounts to populate the following sections:
            'Cash and cash equivalents, beginning of period' and 'Cash and cash equivalents, closing balance'.

        :param options:                 The report options.
        :param payment_account_ids:     A tuple containing all account.account's ids being used in a liquidity journal.
        :return:                        A list of tuple (account_id, account_code, account_name, balance).
        '''
        queries = []
        currency_dif = options['currency_dif']

        for column_group_key, column_group_options in report._split_options_per_column_group(options).items():
            query = report._get_report_query(column_group_options, date_scope, domain=[('account_id', 'in', payment_account_ids)])
            account_alias = query.join(lhs_alias='account_move_line', lhs_column='account_id', rhs_table='account_account', rhs_column='id', link='account_id')
            account_name = self.env['account.account']._field_to_sql(account_alias, 'name')
            account_code = self.env['account.account']._field_to_sql(account_alias, 'code', query)
            if currency_dif == self.env.company.currency_id.symbol:
                queries.append(SQL(
                    '''
                    SELECT
                        %(column_group_key)s AS column_group_key,
                        account_move_line.account_id,
                        %(account_code)s AS account_code,
                        %(account_name)s AS account_name,
                        SUM(%(balance_select)s) AS balance
                    FROM %(table_references)s
                    %(currency_table_join)s
                    WHERE %(search_condition)s
                    GROUP BY account_move_line.account_id, account_code, account_name
                    ''',
                    column_group_key=column_group_key,
                    account_code=account_code,
                    account_name=account_name,
                    table_references=query.from_clause,
                    balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                    currency_table_join=report._currency_table_aml_join(column_group_options),
                    search_condition=query.where_clause,
                ))
            else:
                queries.append(SQL(
                    '''
                    SELECT
                        %(column_group_key)s AS column_group_key,
                        account_move_line.account_id,
                        %(account_code)s AS account_code,
                        %(account_name)s AS account_name,
                        SUM(%(balance_select)s) AS balance
                    FROM %(table_references)s
                    %(currency_table_join)s
                    WHERE %(search_condition)s
                    GROUP BY account_move_line.account_id, account_code, account_name
                    ''',
                    column_group_key=column_group_key,
                    account_code=account_code,
                    account_name=account_name,
                    table_references=query.from_clause,
                    balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance_usd")),
                    currency_table_join=report._currency_table_aml_join(column_group_options),
                    search_condition=query.where_clause,
                ))


        self._cr.execute(SQL(' UNION ALL ').join(queries))

        return self._cr.dictfetchall()

    # Migration Note: Done
    def _get_liquidity_moves(self, report, options, payment_account_ids, cash_flow_tag_ids):
        ''' Fetch all information needed to compute lines from liquidity moves.
        The difficulty is to represent only the not-reconciled part of balance.

        :param options:                 The report options.
        :param payment_account_ids:     A tuple containing all account.account's ids being used in a liquidity journal.
        :return:                        A list of tuple (account_id, account_code, account_name, account_type, amount).
        '''

        reconciled_aml_groupby_account = {}

        queries = []
        currency_dif = options['currency_dif']

        for column_group_key, column_group_options in report._split_options_per_column_group(options).items():
            move_ids_query = self._get_move_ids_query(report, payment_account_ids, column_group_options)
            query = Query(self.env, 'account_move_line')
            account_alias = query.join(lhs_alias='account_move_line', lhs_column='account_id', rhs_table='account_account', rhs_column='id', link='account_id')
            account_code = self.env['account.account']._field_to_sql(account_alias, 'code', query)
            account_name = self.env['account.account']._field_to_sql(account_alias, 'name')
            account_type = SQL.identifier(account_alias, 'account_type')
            if currency_dif == self.env.company.currency_id.symbol:
                queries.append(SQL(
                    '''
                    -- Credit amount of each account
                    SELECT
                        %(column_group_key)s AS column_group_key,
                        account_move_line.account_id,
                        %(account_code)s AS account_code,
                        %(account_name)s AS account_name,
                        %(account_type)s AS account_account_type,
                        account_account_account_tag.account_account_tag_id AS account_tag_id,
                        SUM(%(partial_amount_select)s) AS balance
                    FROM %(from_clause)s
                    %(currency_table_join)s
                    LEFT JOIN account_partial_reconcile
                        ON account_partial_reconcile.credit_move_id = account_move_line.id
                    LEFT JOIN account_account_account_tag
                        ON account_account_account_tag.account_account_id = account_move_line.account_id
                    WHERE account_move_line.move_id IN %(cash_flow_tag_ids)s
                        AND account_move_line.account_id NOT IN %(payment_account_ids)s
                        AND account_partial_reconcile.max_date BETWEEN %(date_from)s AND %(date_to)s
                    GROUP BY account_move_line.company_id, account_move_line.account_id, account_code, account_name, account_account_type, account_account_account_tag.account_account_tag_id

                    UNION ALL

                    -- Debit amount of each account
                    SELECT
                        %(column_group_key)s AS column_group_key,
                        account_move_line.account_id,
                        %(account_code)s AS account_code,
                        %(account_name)s AS account_name,
                        %(account_type)s AS account_account_type,
                        account_account_account_tag.account_account_tag_id AS account_tag_id,
                        -SUM(%(partial_amount_select)s) AS balance
                    FROM %(from_clause)s
                    %(currency_table_join)s
                    LEFT JOIN account_partial_reconcile
                        ON account_partial_reconcile.debit_move_id = account_move_line.id
                    LEFT JOIN account_account_account_tag
                        ON account_account_account_tag.account_account_id = account_move_line.account_id
                    WHERE account_move_line.move_id IN %(cash_flow_tag_ids)s
                        AND account_move_line.account_id NOT IN %(payment_account_ids)s
                        AND account_partial_reconcile.max_date BETWEEN %(date_from)s AND %(date_to)s
                    GROUP BY account_move_line.company_id, account_move_line.account_id, account_code, account_name, account_account_type, account_account_account_tag.account_account_tag_id

                    UNION ALL

                    -- Total amount of each account
                    SELECT
                        %(column_group_key)s AS column_group_key,
                        account_move_line.account_id AS account_id,
                        %(account_code)s AS account_code,
                        %(account_name)s AS account_name,
                        %(account_type)s AS account_account_type,
                        account_account_account_tag.account_account_tag_id AS account_tag_id,
                        SUM(%(aml_balance_select)s) AS balance
                    FROM %(from_clause)s
                    %(currency_table_join)s
                    LEFT JOIN account_account_account_tag
                        ON account_account_account_tag.account_account_id = account_move_line.account_id
                    WHERE account_move_line.move_id IN %(cash_flow_tag_ids)s
                        AND account_move_line.account_id NOT IN %(payment_account_ids)s
                    GROUP BY account_move_line.account_id, account_code, account_name, account_account_type, account_account_account_tag.account_account_tag_id)
                    ''',
                    column_group_key=column_group_key,
                    account_code=account_code,
                    account_name=account_name,
                    account_type=account_type,
                    from_clause=query.from_clause,
                    currency_table_join=report._currency_table_aml_join(column_group_options),
                    partial_amount_select=report._currency_table_apply_rate(SQL("account_partial_reconcile.amount_usd")),
                    aml_balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance_usd")),
                    cash_flow_tag_ids=tuple(payment_move_ids.get(column_group_key, [None])),

                    payment_account_ids=payment_account_ids,
                    date_from=column_group_options['date']['date_from'],
                    date_to=column_group_options['date']['date_to'],
                ))
            else:
                queries.append(SQL(
                    '''
                    -- Credit amount of each account
                    SELECT
                        %(column_group_key)s AS column_group_key,
                        account_move_line.account_id,
                        %(account_code)s AS account_code,
                        %(account_name)s AS account_name,
                        %(account_type)s AS account_account_type,
                        account_account_account_tag.account_account_tag_id AS account_tag_id,
                        SUM(%(partial_amount_select)s) AS balance
                    FROM %(from_clause)s
                    %(currency_table_join)s
                    LEFT JOIN account_partial_reconcile
                        ON account_partial_reconcile.credit_move_id = account_move_line.id
                    LEFT JOIN account_account_account_tag
                        ON account_account_account_tag.account_account_id = account_move_line.account_id
                    WHERE account_move_line.move_id IN %(cash_flow_tag_ids)s
                        AND account_move_line.account_id NOT IN %(payment_account_ids)s
                        AND account_partial_reconcile.max_date BETWEEN %(date_from)s AND %(date_to)s
                    GROUP BY account_move_line.company_id, account_move_line.account_id, account_code, account_name, account_account_type, account_account_account_tag.account_account_tag_id

                    UNION ALL

                    -- Debit amount of each account
                    SELECT
                        %(column_group_key)s AS column_group_key,
                        account_move_line.account_id,
                        %(account_code)s AS account_code,
                        %(account_name)s AS account_name,
                        %(account_type)s AS account_account_type,
                        account_account_account_tag.account_account_tag_id AS account_tag_id,
                        -SUM(%(partial_amount_select)s) AS balance
                    FROM %(from_clause)s
                    %(currency_table_join)s
                    LEFT JOIN account_partial_reconcile
                        ON account_partial_reconcile.debit_move_id = account_move_line.id
                    LEFT JOIN account_account_account_tag
                        ON account_account_account_tag.account_account_id = account_move_line.account_id
                    WHERE account_move_line.move_id IN %(cash_flow_tag_ids)s
                        AND account_move_line.account_id NOT IN %(payment_account_ids)s
                        AND account_partial_reconcile.max_date BETWEEN %(date_from)s AND %(date_to)s
                    GROUP BY account_move_line.company_id, account_move_line.account_id, account_code, account_name, account_account_type, account_account_account_tag.account_account_tag_id

                    UNION ALL

                    -- Total amount of each account
                    SELECT
                        %(column_group_key)s AS column_group_key,
                        account_move_line.account_id AS account_id,
                        %(account_code)s AS account_code,
                        %(account_name)s AS account_name,
                        %(account_type)s AS account_account_type,
                        account_account_account_tag.account_account_tag_id AS account_tag_id,
                        SUM(%(aml_balance_select)s) AS balance
                    FROM %(from_clause)s
                    %(currency_table_join)s
                    LEFT JOIN account_account_account_tag
                        ON account_account_account_tag.account_account_id = account_move_line.account_id
                    WHERE account_move_line.move_id IN %(cash_flow_tag_ids)s
                        AND account_move_line.account_id NOT IN %(payment_account_ids)s
                    GROUP BY account_move_line.account_id, account_code, account_name, account_account_type, account_account_account_tag.account_account_tag_id)
                    ''',
                    column_group_key=column_group_key,
                    account_code=account_code,
                    account_name=account_name,
                    account_type=account_type,
                    from_clause=query.from_clause,
                    currency_table_join=report._currency_table_aml_join(column_group_options),
                    partial_amount_select=report._currency_table_apply_rate(SQL("account_partial_reconcile.amount")),
                    aml_balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                    cash_flow_tag_ids=tuple(payment_move_ids.get(column_group_key, [None])),

                    payment_account_ids=payment_account_ids,
                    date_from=column_group_options['date']['date_from'],
                    date_to=column_group_options['date']['date_to'],
                ))


        self._cr.execute(SQL(' UNION ALL ').join(queries))

        for aml_data in self._cr.dictfetchall():
            reconciled_aml_groupby_account.setdefault(aml_data['account_id'], {})
            reconciled_aml_groupby_account[aml_data['account_id']].setdefault(aml_data['column_group_key'], {
                'column_group_key': aml_data['column_group_key'],
                'account_id': aml_data['account_id'],
                'account_code': aml_data['account_code'],
                'account_name': aml_data['account_name'],
                'account_account_type': aml_data['account_account_type'],
                'account_tag_id': aml_data['account_tag_id'],
                'balance': 0.0,
            })

            reconciled_aml_groupby_account[aml_data['account_id']][aml_data['column_group_key']]['balance'] -= aml_data['balance']

        return list(reconciled_aml_groupby_account.values())


    def _get_reconciled_moves(self, report, options, payment_account_ids, cash_flow_tag_ids):
        ''' Retrieve all moves being not a liquidity move to be shown in the cash flow statement.
        Each amount must be valued at the percentage of what is actually paid.
        E.g. An invoice of 1000 being paid at 50% must be valued at 500.

        :param options:                 The report options.
        :param payment_account_ids:     A tuple containing all account.account's ids being used in a liquidity journal.
        :return:                        A list of tuple (account_id, account_code, account_name, account_type, amount).
        '''

        reconciled_account_ids = {column_group_key: set() for column_group_key in options['column_groups']}
        reconciled_percentage_per_move = {column_group_key: {} for column_group_key in options['column_groups']}
        currency_table = report._get_currency_table(options)

        queries = []
        currency_dif = options['currency_dif']

        for column_group_key, column_group_options in report._split_options_per_column_group(options).items():
            move_ids_query = self._get_move_ids_query(report, payment_account_ids, column_group_options)
            if currency_dif == self.env.company.currency_id.symbol:

                queries.append(SQL(
                    '''
                    SELECT
                        %(column_group_key)s AS column_group_key,
                        debit_line.move_id,
                        debit_line.account_id,
                        SUM(%(partial_amount)s) AS balance
                    FROM account_move_line AS credit_line
                    LEFT JOIN account_partial_reconcile
                        ON account_partial_reconcile.credit_move_id = credit_line.id
                    JOIN %(currency_table)s
                        ON account_currency_table.company_id = account_partial_reconcile.company_id
                        AND account_currency_table.rate_type = 'current' -- For payable/receivable accounts it'll always be 'current' anyway
                    INNER JOIN account_move_line AS debit_line
                        ON debit_line.id = account_partial_reconcile.debit_move_id
                    WHERE credit_line.move_id IN %(column_group_payment_move_ids)s
                        AND credit_line.account_id NOT IN %(payment_account_ids)s
                        AND credit_line.credit > 0.0
                        AND debit_line.move_id NOT IN %(column_group_payment_move_ids)s
                        AND account_partial_reconcile.max_date BETWEEN %(date_from)s AND %(date_to)s
                    GROUP BY debit_line.move_id, debit_line.account_id

                    UNION ALL

                    SELECT
                        %(column_group_key)s AS column_group_key,
                        credit_line.move_id,
                        credit_line.account_id,
                        -SUM(%(partial_amount)s) AS balance
                    FROM account_move_line AS debit_line
                    LEFT JOIN account_partial_reconcile
                        ON account_partial_reconcile.debit_move_id = debit_line.id
                    JOIN %(currency_table)s
                        ON account_currency_table.company_id = account_partial_reconcile.company_id
                        AND account_currency_table.rate_type = 'current' -- For payable/receivable accounts it'll always be 'current' anyway
                    INNER JOIN account_move_line AS credit_line
                        ON credit_line.id = account_partial_reconcile.credit_move_id
                    WHERE debit_line.move_id IN  %(column_group_payment_move_ids)s
                        AND debit_line.account_id NOT IN %(payment_account_ids)s
                        AND debit_line.debit > 0.0
                        AND credit_line.move_id NOT IN %(column_group_payment_move_ids)s
                        AND account_partial_reconcile.max_date BETWEEN %(date_from)s AND %(date_to)s
                    GROUP BY credit_line.move_id, credit_line.account_id)
                    ''',
                    column_group_key=column_group_key,
                    column_group_payment_move_ids=column_group_payment_move_ids,
                    payment_account_ids=payment_account_ids,
                    date_from=column_group_options['date']['date_from'],
                    date_to=column_group_options['date']['date_to'],
                    currency_table=currency_table,
                    partial_amount=report._currency_table_apply_rate(SQL("account_partial_reconcile.amount")),
                ))
            else:
                queries.append(SQL(
                    '''
                    SELECT
                        %(column_group_key)s AS column_group_key,
                        debit_line.move_id,
                        debit_line.account_id,
                        SUM(%(partial_amount)s) AS balance
                    FROM account_move_line AS credit_line
                    LEFT JOIN account_partial_reconcile
                        ON account_partial_reconcile.credit_move_id = credit_line.id
                    JOIN %(currency_table)s
                        ON account_currency_table.company_id = account_partial_reconcile.company_id
                        AND account_currency_table.rate_type = 'current' -- For payable/receivable accounts it'll always be 'current' anyway
                    INNER JOIN account_move_line AS debit_line
                        ON debit_line.id = account_partial_reconcile.debit_move_id
                    WHERE credit_line.move_id IN %(column_group_payment_move_ids)s
                        AND credit_line.account_id NOT IN %(payment_account_ids)s
                        AND credit_line.credit_usd > 0.0
                        AND debit_line.move_id NOT IN %(column_group_payment_move_ids)s
                        AND account_partial_reconcile.max_date BETWEEN %(date_from)s AND %(date_to)s
                    GROUP BY debit_line.move_id, debit_line.account_id

                    UNION ALL

                    SELECT
                        %(column_group_key)s AS column_group_key,
                        credit_line.move_id,
                        credit_line.account_id,
                        -SUM(%(partial_amount)s) AS balance
                    FROM account_move_line AS debit_line
                    LEFT JOIN account_partial_reconcile
                        ON account_partial_reconcile.debit_move_id = debit_line.id
                    JOIN %(currency_table)s
                        ON account_currency_table.company_id = account_partial_reconcile.company_id
                        AND account_currency_table.rate_type = 'current' -- For payable/receivable accounts it'll always be 'current' anyway
                    INNER JOIN account_move_line AS credit_line
                        ON credit_line.id = account_partial_reconcile.credit_move_id
                    WHERE debit_line.move_id IN  %(column_group_payment_move_ids)s
                        AND debit_line.account_id NOT IN %(payment_account_ids)s
                        AND debit_line.debit_usd > 0.0
                        AND credit_line.move_id NOT IN %(column_group_payment_move_ids)s
                        AND account_partial_reconcile.max_date BETWEEN %(date_from)s AND %(date_to)s
                    GROUP BY credit_line.move_id, credit_line.account_id)
                    ''',
                    column_group_key=column_group_key,
                    column_group_payment_move_ids=column_group_payment_move_ids,
                    payment_account_ids=payment_account_ids,
                    date_from=column_group_options['date']['date_from'],
                    date_to=column_group_options['date']['date_to'],
                    currency_table=currency_table,
                    partial_amount=report._currency_table_apply_rate(SQL("account_partial_reconcile.amount_usd")),
                ))


        self._cr.execute(SQL(' UNION ALL ').join(queries))

        for aml_data in self._cr.dictfetchall():
            reconciled_percentage_per_move.setdefault(aml_data['column_group_key'], {})
            reconciled_percentage_per_move[aml_data['column_group_key']].setdefault(aml_data['move_id'], {})
            reconciled_percentage_per_move[aml_data['column_group_key']][aml_data['move_id']].setdefault(aml_data['account_id'], [0.0, 0.0])
            reconciled_percentage_per_move[aml_data['column_group_key']][aml_data['move_id']][aml_data['account_id']][0] += aml_data['balance']

            reconciled_account_ids.setdefault(aml_data['column_group_key'], set())
            reconciled_account_ids[aml_data['column_group_key']].add(aml_data['account_id'])

        if not reconciled_percentage_per_move:
            return []

        queries = []

        for column in options['columns']:
            if currency_dif == self.env.company.currency_id.symbol:
                queries.append(SQL(
                    '''
                    SELECT
                        %(column_group_key)s AS column_group_key,
                        account_move_line.move_id,
                        account_move_line.account_id,
                        SUM(%(balance_select)s) AS balance
                    FROM account_move_line
                    JOIN %(currency_table)s
                        ON account_currency_table.company_id = account_move_line.company_id
                        AND account_currency_table.rate_type = 'current' -- For payable/receivable accounts it'll always be 'current' anyway
                    WHERE account_move_line.move_id IN %(move_ids)s
                        AND account_move_line.account_id IN %(account_ids)s
                    GROUP BY account_move_line.move_id, account_move_line.account_id
                    ''',
                    column_group_key=column['column_group_key'],
                    currency_table=currency_table,
                    balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                    move_ids=tuple(reconciled_percentage_per_move[column['column_group_key']].keys()) or (None,),
                    account_ids=tuple(reconciled_account_ids[column['column_group_key']]) or (None,)
                ))
            else:
                queries.append(SQL(
                    '''
                    SELECT
                        %(column_group_key)s AS column_group_key,
                        account_move_line.move_id,
                        account_move_line.account_id,
                        SUM(%(balance_select)s) AS balance
                    FROM account_move_line
                    JOIN %(currency_table)s
                        ON account_currency_table.company_id = account_move_line.company_id
                        AND account_currency_table.rate_type = 'current' -- For payable/receivable accounts it'll always be 'current' anyway
                    WHERE account_move_line.move_id IN %(move_ids)s
                        AND account_move_line.account_id IN %(account_ids)s
                    GROUP BY account_move_line.move_id, account_move_line.account_id
                    ''',
                    column_group_key=column['column_group_key'],
                    currency_table=currency_table,
                    balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance_usd")),
                    move_ids=tuple(reconciled_percentage_per_move[column['column_group_key']].keys()) or (None,),
                    account_ids=tuple(reconciled_account_ids[column['column_group_key']]) or (None,)
                ))


        self._cr.execute(SQL(' UNION ALL ').join(queries))

        for aml_data in self._cr.dictfetchall():
            if aml_data['account_id'] in reconciled_percentage_per_move[aml_data['column_group_key']][aml_data['move_id']]:
                reconciled_percentage_per_move[aml_data['column_group_key']][aml_data['move_id']][aml_data['account_id']][1] += aml_data['balance']

        reconciled_aml_per_account = {}

        queries = []

        query = Query(self.env, 'account_move_line')
        account_alias = query.join(lhs_alias='account_move_line', lhs_column='account_id', rhs_table='account_account', rhs_column='id', link='account_id')
        account_code = self.env['account.account']._field_to_sql(account_alias, 'code', query)
        account_name = self.env['account.account']._field_to_sql(account_alias, 'name')
        account_type = SQL.identifier(account_alias, 'account_type')

        for column in options['columns']:
            if currency_dif == self.env.company.currency_id.symbol:
                queries.append(SQL(
                    '''
                    SELECT
                        %(column_group_key)s AS column_group_key,
                        account_move_line.move_id,
                        account_move_line.account_id,
                        %(account_code)s AS account_code,
                        %(account_name)s AS account_name,
                        %(account_type)s AS account_account_type,
                        account_account_account_tag.account_account_tag_id AS account_tag_id,
                        SUM(%(balance_select)s) AS balance
                    FROM %(from_clause)s
                    %(currency_table_join)s
                    LEFT JOIN account_account_account_tag
                        ON account_account_account_tag.account_account_id = account_move_line.account_id
                    WHERE account_move_line.move_id IN %(move_ids)s
                    GROUP BY account_move_line.move_id, account_move_line.account_id, account_code, account_name, account_account_type, account_account_account_tag.account_account_tag_id
                    ''',
                    column_group_key=column['column_group_key'],
                    account_code=account_code,
                    account_name=account_name,
                    account_type=account_type,
                    from_clause=query.from_clause,
                    currency_table_join=report._currency_table_aml_join(options),
                    balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance")),
                    move_ids=tuple(reconciled_percentage_per_move[column['column_group_key']].keys()) or (None,)
                ))
            else:
                queries.append(SQL(
                    '''
                    SELECT
                        %(column_group_key)s AS column_group_key,
                        account_move_line.move_id,
                        account_move_line.account_id,
                        %(account_code)s AS account_code,
                        %(account_name)s AS account_name,
                        %(account_type)s AS account_account_type,
                        account_account_account_tag.account_account_tag_id AS account_tag_id,
                        SUM(%(balance_select)s) AS balance
                    FROM %(from_clause)s
                    %(currency_table_join)s
                    LEFT JOIN account_account_account_tag
                        ON account_account_account_tag.account_account_id = account_move_line.account_id
                    WHERE account_move_line.move_id IN %(move_ids)s
                    GROUP BY account_move_line.move_id, account_move_line.account_id, account_code, account_name, account_account_type, account_account_account_tag.account_account_tag_id
                    ''',
                    column_group_key=column['column_group_key'],
                    account_code=account_code,
                    account_name=account_name,
                    account_type=account_type,
                    from_clause=query.from_clause,
                    currency_table_join=report._currency_table_aml_join(options),
                    balance_select=report._currency_table_apply_rate(SQL("account_move_line.balance_usd")),
                    move_ids=tuple(reconciled_percentage_per_move[column['column_group_key']].keys()) or (None,)
                ))

        self._cr.execute(SQL(' UNION ALL ').join(queries))

        for aml_data in self._cr.dictfetchall():
            aml_column_group_key = aml_data['column_group_key']
            aml_move_id = aml_data['move_id']
            aml_account_id = aml_data['account_id']
            aml_account_code = aml_data['account_code']
            aml_account_name = aml_data['account_name']
            aml_account_account_type = aml_data['account_account_type']
            aml_account_tag_id = aml_data['account_tag_id']
            aml_balance = aml_data['balance']

            # Compute the total reconciled for the whole move.
            total_reconciled_amount = 0.0
            total_amount = 0.0

            for reconciled_amount, amount in reconciled_percentage_per_move[aml_column_group_key][aml_move_id].values():
                total_reconciled_amount += reconciled_amount
                total_amount += amount

            # Compute matched percentage for each account.
            if total_amount and aml_account_id not in reconciled_percentage_per_move[aml_column_group_key][aml_move_id]:
                # Lines being on reconciled moves but not reconciled with any liquidity move must be valued at the
                # percentage of what is actually paid.
                reconciled_percentage = total_reconciled_amount / total_amount
                aml_balance *= reconciled_percentage
            elif not total_amount and aml_account_id in reconciled_percentage_per_move[aml_column_group_key][aml_move_id]:
                # The total amount to reconcile is 0. In that case, only add entries being on these accounts. Otherwise,
                # this special case will lead to an unexplained difference equivalent to the reconciled amount on this
                # account.
                # E.g:
                #
                # Liquidity move:
                # Account         | Debit     | Credit
                # --------------------------------------
                # Bank            |           | 100
                # Receivable      | 100       |
                #
                # Reconciled move:                          <- reconciled_amount=100, total_amount=0.0
                # Account         | Debit     | Credit
                # --------------------------------------
                # Receivable      |           | 200
                # Receivable      | 200       |             <- Only the reconciled part of this entry must be added.
                aml_balance = -reconciled_percentage_per_move[aml_column_group_key][aml_move_id][aml_account_id][0]
            else:
                # Others lines are not considered.
                continue

            reconciled_aml_per_account.setdefault(aml_account_id, {})
            reconciled_aml_per_account[aml_account_id].setdefault(aml_column_group_key, {
                'column_group_key': aml_column_group_key,
                'account_id': aml_account_id,
                'account_code': aml_account_code,
                'account_name': aml_account_name,
                'account_account_type': aml_account_account_type,
                'account_tag_id': aml_account_tag_id,
                'balance': 0.0,
            })

            reconciled_aml_per_account[aml_account_id][aml_column_group_key]['balance'] -= aml_balance

        return list(reconciled_aml_per_account.values())