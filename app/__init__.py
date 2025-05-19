import psycopg2
import os
import boto3
import json


def get_secret():
    secret_name = "DBPassword"
    region_name = "us-east-1"
    client = boto3.client("secretsmanager", region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response["SecretString"])
    return secret

def get_db_connection():
    flask_env = os.environ.get('FLASK_ENV')

    if flask_env == 'development':
        return psycopg2.connect(
            host='localhost',         # Make sure to change this when running cfn stack
            database='recipe',
            user='khump',
            password='1qaz!QAZ'
        )
    else:
        secret = get_secret()
        return psycopg2.connect(
            host='mydatabaseinstance.cvyoiwaoia8r.us-east-1.rds.amazonaws.com',
            database='recipe',
            user=secret['username'],
            password=secret['password']
        )