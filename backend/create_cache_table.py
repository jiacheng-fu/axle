"""Create the DynamoDB listings cache table.

One-time setup. Safe to re-run: it exits cleanly if the table already exists.

    export AWS_REGION=us-east-1
    export CARSCOUT_DYNAMO_TABLE=carscout-listings-cache
    python backend/create_cache_table.py

PAY_PER_REQUEST rather than provisioned capacity because this workload is spiky
and low volume; there is nothing to right-size and no idle cost. The whole cache
sits far inside the 25GB free tier.

TTL is enabled on ``expires_at`` so DynamoDB reclaims expired rows itself instead
of the app sweeping them.
"""

import os
import sys

import boto3
from botocore.exceptions import ClientError

TABLE = os.getenv("CARSCOUT_DYNAMO_TABLE", "carscout-listings-cache")
REGION = os.getenv("AWS_REGION", "us-east-1")


def main() -> int:
    ddb = boto3.client("dynamodb", region_name=REGION)

    try:
        ddb.describe_table(TableName=TABLE)
        print(f"table '{TABLE}' already exists in {REGION}; nothing to do")
        return 0
    except ClientError as exc:
        if exc.response["Error"]["Code"] != "ResourceNotFoundException":
            print(f"could not describe table: {exc}", file=sys.stderr)
            return 1

    print(f"creating '{TABLE}' in {REGION} ...")
    ddb.create_table(
        TableName=TABLE,
        KeySchema=[{"AttributeName": "cache_key", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "cache_key", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    )
    ddb.get_waiter("table_exists").wait(TableName=TABLE)
    print("table created")

    ddb.update_time_to_live(
        TableName=TABLE,
        TimeToLiveSpecification={"Enabled": True, "AttributeName": "expires_at"},
    )
    print("TTL enabled on 'expires_at'")
    print(f"\nset CARSCOUT_DYNAMO_TABLE={TABLE} and AWS_REGION={REGION} in the backend env")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
