import io
import os
import random
import time

import dpkt
from locust import HttpUser, between, task
from locust.exception import StopUser


def _parse_ids(value: str) -> list[int]:
    result = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        try:
            result.append(int(part))
        except ValueError:
            pass
    return result


def _env_flag(name: str, default: str = "1") -> bool:
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "y", "on"}


LOGIN = os.getenv("LOADTEST_LOGIN", "admin000")
PASSWORD = os.getenv("LOADTEST_PASSWORD", "admin")

SEARCH_ORG = os.getenv("LOADTEST_SEARCH_ORG", "MSU")
ENABLE_UPLOADS = _env_flag("LOADTEST_ENABLE_UPLOADS", "1")

RAW_TRACE_IDS = _parse_ids(os.getenv("LOADTEST_RAW_TRACE_IDS", ""))
LABELED_TRACE_IDS = _parse_ids(os.getenv("LOADTEST_LABELED_TRACE_IDS", ""))


def make_pcap_bytes() -> bytes:
    bio = io.BytesIO()
    writer = dpkt.pcap.Writer(bio)
    writer.writepkt(b"\x00" * 60, ts=1751416864.0)
    writer.writepkt(b"\x01" * 60, ts=1751416865.0)
    writer.writepkt(b"\x02" * 60, ts=1751416870.0)
    return bio.getvalue()


def make_qos_csv_bytes() -> bytes:
    return (
        "seconds,nanoseconds,session_id,speed,RTT,jitter,loss\n"
        "1751416864,0,1,10.5,2.1,0.2,0.0\n"
        "1751416865,0,1,11.0,2.0,0.3,0.0\n"
    ).encode("utf-8")


class TraceRepositoryUser(HttpUser):
    wait_time = between(1, 2)

    def on_start(self):
        self.token = None
        self.upload_group_id = None
        self.dynamic_raw_trace_ids = []
        self.dynamic_labeled_trace_ids = []
        self.login()

        if ENABLE_UPLOADS:
            self.ensure_upload_group()

    def auth_headers(self) -> dict:
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}

    def login(self):
        with self.client.post(
            "/auth/login",
            json={"login": LOGIN, "password": PASSWORD},
            name="/auth/login",
            catch_response=True,
        ) as resp:
            if resp.status_code == 422:
                pass
            elif resp.status_code != 200:
                resp.failure(f"Login failed: {resp.status_code} {resp.text}")
                raise StopUser()

            if resp.status_code == 200:
                data = resp.json()
                token = data.get("access_token") or data.get("token")
                if not token:
                    resp.failure("Login response has no token")
                    raise StopUser()
                self.token = token
                resp.success()
                return

        with self.client.post(
            "/auth/login",
            data={"login": LOGIN, "password": PASSWORD},
            name="/auth/login",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Login failed: {resp.status_code} {resp.text}")
                raise StopUser()

            data = resp.json()
            token = data.get("access_token") or data.get("token")
            if not token:
                resp.failure("Login response has no token")
                raise StopUser()

            self.token = token
            resp.success()

    def ensure_upload_group(self):
        if self.upload_group_id is not None:
            return

        suffix = f"{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
        payload = {
            "name": f"loadtest-group-{suffix}",
            "org": SEARCH_ORG,
            "data_character": f"loadtest-{suffix}",
            "hardware_desc": "Load test hardware",
            "software_desc": "Locust",
            "processing_degree": "headers only",
            "capture_points": 1,
            "capture_start": "2025-07-02T00:41:04",
            "capture_end": "2025-07-02T00:45:04",
        }

        with self.client.post(
            "/raw-groups",
            json=payload,
            headers=self.auth_headers(),
            name="/raw-groups [setup]",
            catch_response=True,
        ) as resp:
            if resp.status_code not in (200, 201):
                resp.failure(f"Group create failed: {resp.status_code} {resp.text}")
                raise StopUser()

            data = resp.json()
            group_id = data.get("id")
            if not group_id:
                resp.failure("Group creation response has no id")
                raise StopUser()

            self.upload_group_id = group_id
            resp.success()

    def _all_raw_trace_ids(self) -> list[int]:
        return list(RAW_TRACE_IDS) + list(self.dynamic_raw_trace_ids)

    def _all_labeled_trace_ids(self) -> list[int]:
        return list(LABELED_TRACE_IDS) + list(self.dynamic_labeled_trace_ids)

    @task(1)
    def health(self):
        with self.client.get("/health", name="/health", catch_response=True) as resp:
            if resp.status_code != 200:
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()

    @task(3)
    def current_user(self):
        with self.client.get(
            "/users/me",
            headers=self.auth_headers(),
            name="/users/me",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()

    @task(5)
    def search_raw_traces(self):
        with self.client.get(
            "/raw-traces/search",
            params={"limit": 20, "org": SEARCH_ORG},
            headers=self.auth_headers(),
            name="/raw-traces/search",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()

    @task(3)
    def get_raw_trace(self):
        all_ids = self._all_raw_trace_ids()
        if not all_ids:
            return

        trace_id = random.choice(all_ids)
        with self.client.get(
            f"/raw-traces/{trace_id}",
            headers=self.auth_headers(),
            name="/raw-traces/{id}",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()

    @task(1)
    def download_raw_trace(self):
        all_ids = self._all_raw_trace_ids()
        if not all_ids:
            return

        trace_id = random.choice(all_ids)
        with self.client.get(
            f"/raw-traces/{trace_id}/download",
            headers=self.auth_headers(),
            name="/raw-traces/{id}/download",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Unexpected status {resp.status_code}")
            elif not resp.content:
                resp.failure("Empty file body")
            else:
                resp.success()

    @task(4)
    def search_labeled_traces(self):
        with self.client.get(
            "/labeled-traces/search",
            params={"limit": 20},
            headers=self.auth_headers(),
            name="/labeled-traces/search",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Unexpected status {resp.status_code}")
            else:
                resp.success()

    @task(1)
    def download_labeled_trace(self):
        all_ids = self._all_labeled_trace_ids()
        if not all_ids:
            return

        labeled_id = random.choice(all_ids)
        with self.client.get(
            f"/labeled-traces/{labeled_id}/download",
            headers=self.auth_headers(),
            name="/labeled-traces/{id}/download",
            catch_response=True,
        ) as resp:
            if resp.status_code != 200:
                resp.failure(f"Unexpected status {resp.status_code}")
            elif not resp.content:
                resp.failure("Empty file body")
            else:
                resp.success()

    @task(1)
    def upload_raw_trace(self):
        if not ENABLE_UPLOADS:
            return

        self.ensure_upload_group()
        if self.upload_group_id is None:
            return

        suffix = f"{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
        files = {
            "file": (
                f"loadtest_{suffix}.pcap",
                make_pcap_bytes(),
                "application/vnd.tcpdump.pcap",
            )
        }

        with self.client.post(
            f"/raw-traces/group/{self.upload_group_id}?point=Single",
            files=files,
            headers=self.auth_headers(),
            name="/raw-traces/group/{group_id} [upload]",
            catch_response=True,
        ) as resp:
            if resp.status_code not in (200, 201):
                resp.failure(f"Unexpected status {resp.status_code}: {resp.text}")
                return

            data = resp.json()
            trace_id = data.get("id")
            if not trace_id:
                resp.failure("Upload response has no trace id")
                return

            self.dynamic_raw_trace_ids.append(trace_id)
            resp.success()

    @task(1)
    def upload_labeled_trace(self):
        if not ENABLE_UPLOADS:
            return

        donor_ids = self._all_raw_trace_ids()
        if not donor_ids:
            return

        donor_id = random.choice(donor_ids)
        suffix = f"{int(time.time() * 1000)}-{random.randint(1000, 9999)}"

        data = {
            "kind": "qos",
            "raw_trace_ids": str(donor_id),
            "software_desc": "loadtest-label-tool",
        }
        files = {
            "file": (
                f"loadtest_{suffix}.csv",
                make_qos_csv_bytes(),
                "text/csv",
            )
        }

        with self.client.post(
            "/labeled-traces",
            data=data,
            files=files,
            headers=self.auth_headers(),
            name="/labeled-traces [upload]",
            catch_response=True,
        ) as resp:
            if resp.status_code not in (200, 201):
                resp.failure(f"Unexpected status {resp.status_code}: {resp.text}")
                return

            payload = resp.json()
            labeled_id = payload.get("id")
            if not labeled_id:
                resp.failure("Upload labeled response has no id")
                return

            self.dynamic_labeled_trace_ids.append(labeled_id)
            resp.success()
