import boto3

def query(k):
    client = boto3.client('dynamodb', endpoint_url=env['dynamodb_endpoint'])
    return client.query(TableName='decimals', KeyConditionExpression='PK = :k', ExpressionAttributeValues={':k': {'S': k}})

def query_balance(acc_id, currency):
    client = boto3.client('dynamodb', endpoint_url=env['dynamodb_endpoint'])
    return client.query(TableName='decimals', KeyConditionExpression='PK = :acc_id', QueryFilterExpression='currency = :currency', ExpressionAttributeValues={':acc_id': {'S': acc_id}, ':currency': {'S': currency}})[0]

def pagination(query, config):
    if query.get('starting_after'):
        sk = query['starting_after']
        response = client.get_item(TableName='decimals', Key={'PK': query['public_key'], 'SK': sk})
        if response['Item']:
            config['last_prim_kvs'] = {
                'PK': query['public_key'],
                'SK': sk,
                'GSI1_PK': query['public_key'],
                'GSI1_SK': response['Item']['timestamp']['S']
            }
    return config

def list_transactions(query):
    config = {}
    return (
        list(
            query.items()
        )
        + pagination(query, config)
        .get('Items', [])
    )

def list_with_genesis(query):
    pk = query['public_key']
    gens = query.get('gens', [])
    for gen in gens:
        gens.append(query_balance(pk, gen))
    return gens

def list_accounts(pk):
    return query(pk).get('Items', [])

def list_balances(query):
    if 'account' in query:
        return list_with_genesis(query)
    else:
        return list_accounts(query['public_key'])

def put(item):
    client = boto3.client('dynamodb', endpoint_url=env['dynamodb_endpoint'])
    return client.put_item(TableName='decimals', Item=item)

def transact_put(items):
    client = boto3.client('dynamodb', endpoint_url=env['dynamodb_endpoint'])
    return client.transact_write_items(Items=items)
