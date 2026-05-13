def test_upload_single_pcap(client, admin_headers, created_group):
    group_id = created_group["id"]
    files = {
        "file": ("trace1.pcap", __import__("tests.conftest").conftest.make_pcap_bytes(), "application/vnd.tcpdump.pcap"),
    }

    resp = client.post(
        f"/raw-traces/group/{group_id}?point=Single",
        files=files,
        headers=admin_headers,
    )
    assert resp.status_code in (200, 201), resp.text
    data = resp.json()
    assert data["group_id"] == group_id
    assert data["point"] == "Single"


def test_upload_batch_pcap(client, admin_headers, created_group):
    group_id = created_group["id"]
    pcap1 = __import__("tests.conftest").conftest.make_pcap_bytes()
    pcap2 = __import__("tests.conftest").conftest.make_pcap_bytes()

    files = [
        ("files", ("dump_2025_07_02_00_41_04.pcap000", pcap1, "application/vnd.tcpdump.pcap")),
        ("files", ("dump_2025_07_02_00_41_04.pcap001", pcap2, "application/vnd.tcpdump.pcap")),
    ]

    resp = client.post(
        f"/raw-traces/group/{group_id}/batch?point=Single",
        files=files,
        headers=admin_headers,
    )
    assert resp.status_code in (200, 201), resp.text
    data = resp.json()
    assert len(data) == 2
    assert data[0]["group_id"] == group_id


def test_search_raw_traces_by_group(client, admin_headers, created_group):
    group_id = created_group["id"]
    files = {
        "file": ("trace1.pcap", __import__("tests.conftest").conftest.make_pcap_bytes(), "application/vnd.tcpdump.pcap"),
    }
    up = client.post(
        f"/raw-traces/group/{group_id}?point=Single",
        files=files,
        headers=admin_headers,
    )
    assert up.status_code in (200, 201), up.text

    resp = client.get(
        f"/raw-traces/search?group_id={group_id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["group_id"] == group_id


def test_download_raw_trace(client, admin_headers, created_group):
    group_id = created_group["id"]
    files = {
        "file": ("trace1.pcap", __import__("tests.conftest").conftest.make_pcap_bytes(), "application/vnd.tcpdump.pcap"),
    }
    up = client.post(
        f"/raw-traces/group/{group_id}?point=Single",
        files=files,
        headers=admin_headers,
    )
    trace_id = up.json()["id"]

    resp = client.get(f"/raw-traces/{trace_id}/download", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.content


def test_export_raw_trace_segment(client, admin_headers, created_group):
    group_id = created_group["id"]
    files = {
        "file": ("trace1.pcap", __import__("tests.conftest").conftest.make_pcap_bytes(), "application/vnd.tcpdump.pcap"),
    }
    up = client.post(
        f"/raw-traces/group/{group_id}?point=Single",
        files=files,
        headers=admin_headers,
    )
    trace_id = up.json()["id"]

    resp = client.get(
        f"/raw-traces/{trace_id}/export",
        params={
            "t_from": "2025-07-02T00:41:04",
            "t_to": "2025-07-02T00:41:10",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.content


def test_invalid_point_for_one_point_group(client, admin_headers, created_group):
    group_id = created_group["id"]
    files = {
        "file": ("trace1.pcap", __import__("tests.conftest").conftest.make_pcap_bytes(), "application/vnd.tcpdump.pcap"),
    }
    resp = client.post(
        f"/raw-traces/group/{group_id}?point=A",
        files=files,
        headers=admin_headers,
    )
    assert resp.status_code == 422