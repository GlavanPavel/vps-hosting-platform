
import os
import time

import httpx
import pytest

BASE_URL = os.getenv("E2E_BASE_URL", "http://localhost:8000")
IMAGE = os.getenv("E2E_IMAGE", "cirros")
FLAVOR = os.getenv("E2E_FLAVOR", "m1.tiny")
ASSIGN_FIP = os.getenv("E2E_ASSIGN_FIP", "false").lower() in ("1", "true", "yes")
PROVISION_TIMEOUT = int(os.getenv("E2E_PROVISION_TIMEOUT", "300"))
PREREQ_TIMEOUT = int(os.getenv("E2E_PREREQ_TIMEOUT", "120"))
POLL_INTERVAL = float(os.getenv("E2E_POLL_INTERVAL", "5"))

_NO_REFRESH = ("/auth/login", "/auth/refresh", "/auth/register")

# call fetch every interval seconds until something true
def poll(fetch, ready, timeout, interval, what):
    deadline = time.monotonic() + timeout
    last = None
    while time.monotonic() < deadline:
        last = fetch()
        if ready(last):
            return last
        time.sleep(interval)
    raise AssertionError(f"Timed out after {timeout}s waiting for {what}; last seen: {last}")


def _api_reachable():
    try:
        httpx.get(f"{BASE_URL}/", timeout=3.0)
        return True
    except Exception:
        return False


class ApiClient:
    def __init__(self, base_url):
        self._c = httpx.Client(base_url=base_url, timeout=30.0)

    def _request(self, method, url, **kwargs):
        resp = self._c.request(method, url, **kwargs)
        if resp.status_code == 401 and url not in _NO_REFRESH:
            if self._c.post("/auth/refresh").status_code == 200:
                resp = self._c.request(method, url, **kwargs)
        return resp

    def get(self, url, **kwargs):
        return self._request("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._request("POST", url, **kwargs)

    def delete(self, url, **kwargs):
        return self._request("DELETE", url, **kwargs)

    def close(self):
        self._c.close()


@pytest.fixture(scope="session")
def client():
    if not _api_reachable():
        pytest.skip(
            f"API not reachable at {BASE_URL} — start the full stack "
            "(API + Celery worker + Beat + OpenStack) to run the E2E suite"
        )

    stamp = int(time.time())
    email = f"e2e_{stamp}@example.com"
    password = "e2e-password-123"

    api = ApiClient(BASE_URL)
    r = api.post(
        "/auth/register",
        json={"email": email, "password": password, "organization_name": f"E2E Org {stamp}"},
    )
    assert r.status_code == 201, f"register failed: {r.status_code} {r.text}"
    r = api.post("/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"

    yield api
    api.close()


@pytest.fixture(scope="session")
def ctx(client):
    state = {}
    yield state

    inst = state.get("instance_id")
    if inst is not None:
        try:
            client.delete(f"/instances/{inst}")
            poll(
                lambda: client.get(f"/instances/{inst}").status_code,
                lambda code: code == 404,
                PROVISION_TIMEOUT, POLL_INTERVAL, "instance deletion",
            )
        except Exception:
            pass
    for path, key in (("/security-groups", "sg_id"), ("/networks", "network_id"), ("/keypairs", "keypair_id")):
        rid = state.get(key)
        if rid is not None:
            try:
                client.delete(f"{path}/{rid}")
            except Exception:
                pass
