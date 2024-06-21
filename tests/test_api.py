
from fastapi.testclient import TestClient
from server import app, CreateRequest, CreateResponse, ListResponse
from http import HTTPStatus
from datetime import datetime, timezone

client = TestClient(app)

def test_simple():
    assert True

def test_alias():
    test_url = "http://test.com"
    params = CreateRequest(url=test_url)
    r = client.post('/create_url', content=params.json())
    assert r.status_code == HTTPStatus.OK
    
    o = CreateResponse(**r.json())
    assert o.alias is not None
    assert o.url is not None
    assert o.created_at is not None
    print(o.alias)
    alias = o.alias

    r = client.get(f'/list?search=test')
    assert r.status_code == HTTPStatus.OK

    o = ListResponse(**r.json())
    found = False
    assert len(o.data) > 0
    for item in o.data:
        if item.alias == alias:
            found = True
            assert item.created_at is not None
    assert found

    r = client.get(f'/find/{alias}', follow_redirects=False)
    assert r.status_code == HTTPStatus.TEMPORARY_REDIRECT, alias
    assert r.headers['location'] == test_url