import io.pedestal.http as http
import io.pedestal.http.route as route
import io.pedestal.interceptor.chain as chain
import clojure.data.json as json
import clojure.tools.logging as log
import clojure.walk as walk
import spec_tools.core as st
import clojure.spec.alpha as s
import decimals.security as sec
import decimals.crypto as crypto
import decimals.transactions as tx
import decimals.analytics as analytics
import decimals.balances as b

msg = {
    'generic': {'message': 'Sorry, we had a problem. Please, try again or reach out.'},
    'funds': {'message': 'Insufficient funds, check origin account balance.'},
    'creds': {'message': 'Invalid credentials.'}
}

def response(status, body, **headers):
    return {'status': status, 'body': body, 'headers': headers}

ok = lambda body, **headers: response(200, body, **headers)
created = lambda body, **headers: response(201, body, **headers)
accepted = lambda body, **headers: response(202, body, **headers)
badrequest = lambda body, **headers: response(400, body, **headers)
forbidden = lambda body, **headers: response(401, body, **headers)
not_found = lambda body, **headers: response(404, body, **headers)
server_error = lambda body, **headers: response(500, body, **headers)

def req_meta(context):
    return {k: context['request'][k] for k in ['path-info', 'remote-addr', 'request-method', 'server-name', 'transit-params', 'uri']}

def respond(context, response):
    m = req_meta(context)
    status = response['status']
    if status == 200:
        analytics.track(context, "Success", m)
    elif status == 201:
        analytics.track(context, "Created", m)
    elif status == 400:
        analytics.track(context, "Bad request", m)
    elif status == 401:
        analytics.track(context, "Unauthorized", m)
    elif status == 500:
        analytics.track(context, "Server Error", m)
    return chain.terminate(context.copy().update({'response': response}))

genesis_balance = {
    'name': 'genesis-balance',
    'enter': lambda context: context.update({'from': {'balance': b.genesis(context)}}) if b.genesis(context) else context
}

check_balance = {
    'name': 'check-balance',
    'enter': lambda context: (
        log.debug("checking origin funds %s %s", context['from']['balance']['balance'], context['tx']['amount']),
        (badrequest(msg['funds']) if (context['from']['balance']['balance'] < context['tx']['amount']) else context)
    )
}

hash_txs = {
    'name': 'hash-txs',
    'enter': lambda context: context.update(tx.hash_txs(context)) if tx.hash_txs(context) else (server_error({'message': msg['generic']}))
}

chain_txs = {
    'name': 'chain-tx',
    'enter': lambda context: (
        response := tx.chain(context),
        respond(context, created(map(lambda x: st.select_spec(::tx/pub-transaction, x), response['success']))) if 'success' in response else respond(context, server_error({'message': msg['generic']}))
    )
}

spec_tx = {
    'name': 'spec-tx',
    'enter': lambda context: context if s.valid?(::tx/transaction, context['tx']) else respond(context, badrequest({'error': s.explain_data(::tx/transaction, context['tx'])}))
}

def str_to_map(s):
    try:
        return json.read_str(s).update(walk.keywordize_keys)
    except Exception as e:
        pass

parse_tx = {
    'name': 'parse-tx',
    'enter': lambda context: (
        tx := str_to_map(context['request']['body']),
        context.update({'tx': tx}) if tx else respond(context, badrequest({'error': 'Malformed JSON.'}))
    )
}

account_queryparam = {
    'name': 'account-queryparam',
    'enter': lambda context: (
        acc_id := context['request']['query-params']['account'],
        (
            id := b.ctx_to_id(context),
            log.debug("Querying account: %s", id),
            context.update({'account': id})
        ) if acc_id else (
            pk := context['customer']['public-key'],
            log.debug("Querying public-key %s", pk),
            context.update_in(['account', 'public-key'], pk)
        )
    )
}

transaction_queryparam = {
    'name': 'transaction-queryparam',
    'enter': lambda context: (
        tx_id := context['request']['path-params']['transaction-id'],
        (
            id := list(context['customer']['public-key']),
            tx_id = context['request']['path-params']['transaction-id'],
            (
                log.debug("Querying transaction: %s", id),
                context.update({'tx-id': id})
            ) if tx_id else respond(context, badrequest({'error': 'Missing transaction path parameter.'}))
        )
    )
}

pagination = {
    'name': 'pagination',
    'enter': lambda context: context.update({'starting-after': context['request']['query-params']['starting_after']}) if 'starting_after' in context['request']['query-params'] else context
}

list_transactions = {
    'name': 'list-transactions',
    'enter': lambda context: (
        transactions := tx.list_transactions(context['account'], list(context['starting-after'])),
        respond(context, ok(map(lambda x: st.select_spec(::tx/pub-transaction, x), transactions))) if transactions else respond(context, not_found({'error': 'Account not found.'}))
    )
}

list_balances = {
    'name': 'list-balances',
    'enter': lambda context: (
        balances := b.list_balances(context['account']),
        respond(context, ok(map(lambda x: st.select_spec(::b/pub-balance, x), balances)))) if balances else respond(context, not_found({'error': 'Account not found.'}))
    )
}

auth = {
    'name': 'auth',
    'enter': lambda context: (
        customer := sec.apikey_auth(context),
        (
            ctx := context.update({'customer': customer}),
            analytics.identify(ctx),
            ctx
        ) if customer else respond(context, forbidden(msg['creds']))
    )
}

from_balance = {
    'name': 'from-balance',
    'enter': lambda context: context.update({'from': {'balance': b.balance(b.ctx_to_id(context, 'from'))}}) if b.balance(b.ctx_to_id(context, 'from')) else context
}

routes = route.expand_routes(
    set([
        ["/v1/transactions", "POST", [
            http.json_body,
            auth,
            parse_tx,
            spec_tx,
            from_balance,
            genesis_balance,
            check_balance,
            hash_txs,
            chain_txs
        ], "transactions-post"],
        ["/v1/transactions/:transaction-id", "GET", [
            http.json_body,
            auth,
            transaction_queryparam
        ], "transactions-get"],
        ["/v1/transactions", "GET", [
            http.json_body,
            auth,
            account_queryparam,
            pagination,
            list_transactions
        ], "transactions-list"],
        ["/v1/balances", "GET", [
            http.json_body,
            auth,
            account_queryparam,
            list_balances
        ], "balances-get"]
    ])
)
