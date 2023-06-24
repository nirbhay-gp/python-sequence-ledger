from decimals.dynamodb import db
from decimals.crypto import crypto
from clojure.data.json import json
from clojure.spec.alpha import s
from java.time import t

def ctx_to_id(context, party=None):
    if party is None:
        party = 'from'
    return {
        'public_key': context['customer']['public_key'],
        'currency': context['tx']['currency'],
        'account': context['request']['query_params']['account'],
    }

def id_to_pk(id):
    return str(id['public_key']) + '#' + str(id['account'])

def list_balances(query):
    balances = db.list_balances(query)
    return balances

def balance(query):
    pk = id_to_pk(query)
    return db.query_balance(pk, query['currency'])

def account_to_genesis(account, party):
    acc_id = account[party]
    currency = account['currency']
    return {
        'id': str(acc_id) + '#' + currency,
        'public_key': account['public_key'],
        'party': party,
        'from': acc_id,
        'to': acc_id,
        'amount': 0,
        'currency': currency,
        'date': str(t.instant()),
        'timestamp': str(t.to_millis_from_epoch(t.instant()) - 1),
        'type': 'genesis',
        'balance': 0,
    }

def context_to_account(context, party):
    tx = context['tx']
    cust = context['customer']
    party = {party: tx[party]}
    currency = tx['currency']
    pub_key = cust['public_key']
    return {**party, **pub_key, **currency}

def is_genesis(account):
    return account['public_key'] == account['from']

def genesis(context):
    tx = context['tx']
    account = context_to_account(context, 'from')
    if is_genesis(account):
        if 'from' in context and 'balance' in context['from']:
            genesis_balance = context['from']['balance']
            genesis_funds = {
                'balance': genesis_balance + 2 * tx['amount'],
            }
            return genesis_funds
        else:
            genesis_tx = account_to_genesis(account, 'from')
            genesis_funds = {
                'balance': 2 * tx['amount'],
            }
            return genesis_funds
    else:
        return None