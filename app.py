import falcon
from falcon import testing

api = falcon.API()


class TransactionsResource(object):

    def on_post(self, req, resp):
        transaction = req.media
        resp.status = falcon.HTTP_201
        resp.body = transaction


class BalancesResource(object):

    def on_get(self, req, resp):
        account = req.get_param('account')
        balances = [
            {
                'currency': 'usd',
                'amount': 1000,
            },
            {
                'currency': 'eur',
                'amount': 500,
            },
        ]
        resp.body = balances


api.add_route('/transactions', TransactionsResource())
api.add_route('/balances', BalancesResource())


if __name__ == '__main__':
    with testing.TestClient(api) as client:
        response = client.post('/transactions', json={'from': 'Alice', 'to': 'Bob', 'currency': 'usd', 'amount': 1000})
        assert response.status_code == falcon.HTTP_201
        assert response.json == {'from': 'Alice', 'to': 'Bob', 'currency': 'usd', 'amount': 1000}
        response = client.get('/balances?account=Alice')
        assert response.status_code == falcon.HTTP_200
        assert response.json == [{'currency': 'usd', 'amount': 1000}, {'currency': 'eur', 'amount': 500}]