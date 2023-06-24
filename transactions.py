import logging
from datetime import datetime

from java_time import Instant, ZoneOffset

from .dynamodb import query, transact_put, list_transactions
from .crypto import map_to_md5
from .balances import ctx_to_id, balance, account_to_genesis
from .specs import select_spec_pub_transaction, select_spec_balance_tx

logging.basicConfig(level=logging.DEBUG)


def account_to_id(account, party):
    return f"{account['public-key']}#{account[party]}"


def tx_get(id):
    return query(id)


def item_to_tuple(item):
    logging.debug(f"putting {item}")
    return ("put", item)


def doc_to_put(doc):
    return {
        "table-name": "decimals",
        "item": doc,
        "cond-expr": "attribute_not_exists(#SK)",
        "expr-attr-names": {"#SK": doc["id"]}
    }


def tx_to_doc(tx):
    doc = tx.copy()
    doc["PK"] = account_to_id(tx, tx["party"])
    doc["SK"] = tx["id"]
    doc["GSI1_PK"] = tx["public-key"]
    doc["GSI1_SK"] = account_to_id(tx, tx["party"])
    doc["LSI1_SK"] = tx["timestamp"]
    return doc


def chain(context):
    from_balance = context["from"]["balance"]
    from_tx = context["from"]["tx"]
    to_balance = context["to"]["balance"]
    to_tx = context["to"]["tx"]
    txs = [from_balance, from_tx, to_balance, to_tx]

    items = [
        item_to_tuple(doc_to_put(tx_to_doc(tx)))
        for tx in txs
    ]

    if created := transact_put(items):
        return {
            **context,
            "success": [from_tx, to_tx]
        }
    else:
        return {
            **context,
            "error": "internal"
        }


def context_to_account(context, party):
    tx = context["tx"]
    cust = context["customer"]
    party = {party: tx[party]}
    pub_key = {"public-key": cust["public-key"]}
    currency = {"currency": tx["currency"]}
    account = {**party, **pub_key, **currency}
    if s.valid?(:account, account):
        return account
    else:
        logging.warn(s.explain_data(:account, account))


def party_funds(context, party):
    if query := ctx_to_id(context, party):
        if balance := balance(query):
            if s.valid?(:balance_tx, balance):
                logging.debug(f"got balance: {balance}")
                return balance
            else:
                logging.warn(f"invalid balance in database: {balance} {s.explain_data(:balance_tx, balance)}")


def hash_txs(context):
    to_account = context_to_account(context, "to")
    from_account = context_to_account(context, "from")
    if to := (
            party_funds(context, "to")
            or account_to_genesis(to_account, "to")
    ):
        tx = context["tx"]
        from_balance = context["from"]["balance"]
        from_tx = {
            "id": map_to_md5(select_spec_pub_transaction(from_balance)),
            "public-key": from_account["public-key"],
            "party": "from",
            "account": context["from"]["account"],
            "balance": from_balance["balance"] - tx["amount"],
            "date": str(Instant.now()),
            "timestamp": str(Instant.now().toEpochMilli()),
            "type": "debit"
        }
        to_tx = {
            "id": map_to_md5(select_spec_pub_transaction(to)),
            "public-key": to_account["public-key"],
            "party": "to",
            "account": to_account["to"],
            "balance": to["balance"] + tx["amount"],
            "date": str(Instant.now()),
            "timestamp": str(Instant.now().toEpochMilli()),
            "type": "credit"
        }
        context["to"]["balance"] = to
        context["to"]["tx"] = to_tx
        context["from"]["tx"] = from_tx
    return context


def list_transactions(query):
    if transactions := list_transactions(query):
        logging.debug(transactions)
        return transactions