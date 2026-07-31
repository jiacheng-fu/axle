"""Tests for the DynamoDB cache tier, run against a mocked DynamoDB (moto).

Verifies the tier without needing an AWS account, and pins the behaviours that
matter: it must never raise into a request path, and it must never serve a stale
row just because DynamoDB's TTL sweep has not run yet.

    python -m pytest backend/test_dynamo_cache.py -v
"""

import importlib
import os
import time

import boto3
import pytest
from moto import mock_aws

TABLE = "carscout-listings-cache-test"
REGION = "us-east-1"


def _fresh_module():
    """Re-import so the module-level _checked/_table memo does not leak across tests."""
    import dynamo_cache
    importlib.reload(dynamo_cache)
    return dynamo_cache


def _make_table():
    ddb = boto3.resource("dynamodb", region_name=REGION)
    ddb.create_table(
        TableName=TABLE,
        KeySchema=[{"AttributeName": "cache_key", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "cache_key", "AttributeType": "S"}],
        BillingMode="PAY_PER_REQUEST",
    ).wait_until_exists()


@pytest.fixture
def env(monkeypatch):
    monkeypatch.setenv("CARSCOUT_DYNAMO_TABLE", TABLE)
    monkeypatch.setenv("AWS_REGION", REGION)
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")


LISTINGS = [{"vin": "1FTFW1E50NFA00001", "price_usd": 24995},
            {"vin": "1FTFW1E50NFA00002", "price_usd": 31500}]


@mock_aws
def test_round_trip(env):
    _make_table()
    dc = _fresh_module()
    assert dc.is_enabled()
    assert dc.write("78750", 50, LISTINGS) is True
    assert dc.read("78750", 50) == LISTINGS


@mock_aws
def test_miss_returns_none(env):
    _make_table()
    dc = _fresh_module()
    assert dc.read("99999", 50) is None


@mock_aws
def test_key_includes_distance(env):
    """78750@50mi and 78750@100mi are different queries and must not collide."""
    _make_table()
    dc = _fresh_module()
    dc.write("78750", 50, LISTINGS)
    assert dc.read("78750", 100) is None


@mock_aws
def test_expired_row_is_not_served(env):
    """DynamoDB TTL deletion lags by up to ~48h, so read() must check expiry itself."""
    _make_table()
    dc = _fresh_module()
    dc.write("78750", 50, LISTINGS, ttl_seconds=-1)  # already expired
    assert dc.read("78750", 50) is None


@mock_aws
def test_empty_listings_are_not_cached(env):
    """Caching an empty result would pin a failed API call for the whole TTL."""
    _make_table()
    dc = _fresh_module()
    assert dc.write("78750", 50, []) is False
    assert dc.read("78750", 50) is None


def test_disabled_without_env(monkeypatch):
    """No table configured: every call is a silent no-op, nothing raises."""
    monkeypatch.delenv("CARSCOUT_DYNAMO_TABLE", raising=False)
    dc = _fresh_module()
    assert dc.is_enabled() is False
    assert dc.read("78750", 50) is None
    assert dc.write("78750", 50, LISTINGS) is False
    assert "disabled" in dc.status()


@mock_aws
def test_missing_table_does_not_raise(env, monkeypatch):
    """Table named but absent: disable cleanly rather than 500 the request."""
    monkeypatch.setenv("CARSCOUT_DYNAMO_TABLE", "does-not-exist")
    dc = _fresh_module()
    assert dc.is_enabled() is False
    assert dc.read("78750", 50) is None
    assert dc.write("78750", 50, LISTINGS) is False


@mock_aws
def test_corrupt_row_does_not_raise(env):
    """A malformed row must degrade to a miss, not blow up the caller."""
    _make_table()
    dc = _fresh_module()
    boto3.resource("dynamodb", region_name=REGION).Table(TABLE).put_item(Item={
        "cache_key": "78750#50",
        "listings": "{not json",
        "expires_at": int(time.time()) + 600,
    })
    assert dc.read("78750", 50) is None
