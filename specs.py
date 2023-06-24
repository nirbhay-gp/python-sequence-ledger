from marshmallow import Schema, fields, validate

class AccountSchema(Schema):
    from_ = fields.String(validate=validate.Length(min=2))
    to = fields.String(validate=validate.Length(min=2))

class TransactionSchema(Schema):
    id = fields.String(validate=validate.Length(min=2))
    date = fields.String(validate=validate.Length(min=2))
    from_ = fields.String(validate=validate.Length(min=2))
    to = fields.String(validate=validate.Length(min=2))
    amount = fields.Integer(validate=validate.Range(min=0))
    balance = fields.Integer(validate=validate.Range(min=0))
    currency = fields.String(validate=validate.Length(min=2))
    metadata = fields.Raw(allow_none=True)
    account = fields.Nested(AccountSchema)

class BalanceTransactionSchema(Schema):
    from_ = fields.String(validate=validate.Length(min=2))
    to = fields.String(validate=validate.Length(min=2))
    amount = fields.Integer(validate=validate.Range(min=0))
    currency = fields.String(validate=validate.Length(min=2))
    balance = fields.Integer(validate=validate.Range(min=0))
    public_key = fields.String(validate=validate.Length(min=2))
    date = fields.String(validate=validate.Length(min=2))

class BalanceSchema(Schema):
    balance = fields.Integer(validate=validate.Range(min=0))
    currency = fields.String(validate=validate.Length(min=2))
    account = fields.String(validate=validate.Length(min=2))

# Example usage:
transaction_data = {
    'id': '123',
    'date': '2023-06-23',
    'from_': 'Alice',
    'to': 'Bob',
    'amount': 100,
    'balance': 500,
    'currency': 'USD',
    'metadata': None,
    'account': {
        'from_': 'Alice',
        'to': 'Bob'
    }
}

# Validate the transaction data against the schema
try:
    TransactionSchema().load(transaction_data)
    print("Transaction data is valid.")
except Exception as e:
    print("Transaction data is invalid:", str(e))