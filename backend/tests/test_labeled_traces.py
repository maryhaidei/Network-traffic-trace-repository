def upload_raw_trace(client, headers, group_id):
    files = {
        "file": ("trace1.pcap", __import__("tests.conftest").conftest.make_pcap_bytes(), "application/vnd.tcpdump.pcap"),
    }
    resp = client.post(
        f"/raw-traces/group/{group_id}?point=Single",
        files=files,
        headers=headers,
    )
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["id"]


def test_upload_qos_labeled_trace(client, admin_headers, created_group, qos_csv_bytes):
    group_id = created_group["id"]
    raw_trace_id = upload_raw_trace(client, admin_headers, group_id)

    resp = client.post(
        "/labeled-traces",
        data={
            "kind": "qos",
            "raw_trace_ids": str(raw_trace_id),
            "software_desc": "label-tool 1.0",
        },
        files={
            "file": ("qos.csv", qos_csv_bytes, "text/csv"),
        },
        headers=admin_headers,
    )
    assert resp.status_code in (200, 201), resp.text
    data = resp.json()
    assert data["kind"] == "qos"
    assert raw_trace_id in data["donor_raw_trace_ids"]


def test_upload_mac_labeled_trace(client, admin_headers, created_group, mac_csv_bytes):
    group_id = created_group["id"]
    raw_trace_id = upload_raw_trace(client, admin_headers, group_id)

    resp = client.post(
        "/labeled-traces",
        data={
            "kind": "mac_intensity",
            "raw_trace_ids": str(raw_trace_id),
            "software_desc": "mac-tool 1.0",
        },
        files={
            "file": ("mac.csv", mac_csv_bytes, "text/csv"),
        },
        headers=admin_headers,
    )
    assert resp.status_code in (200, 201), resp.text
    data = resp.json()
    assert data["kind"] == "mac_intensity"


def test_invalid_labeled_csv_is_rejected(client, admin_headers, created_group):
    group_id = created_group["id"]
    raw_trace_id = upload_raw_trace(client, admin_headers, group_id)

    bad_csv = b"bad,header\n1,2\n"

    resp = client.post(
        "/labeled-traces",
        data={
            "kind": "qos",
            "raw_trace_ids": str(raw_trace_id),
            "software_desc": "bad-tool",
        },
        files={
            "file": ("bad.csv", bad_csv, "text/csv"),
        },
        headers=admin_headers,
    )
    assert resp.status_code == 422


def test_search_labeled_by_donor(client, admin_headers, created_group, qos_csv_bytes):
    group_id = created_group["id"]
    raw_trace_id = upload_raw_trace(client, admin_headers, group_id)

    up = client.post(
        "/labeled-traces",
        data={
            "kind": "qos",
            "raw_trace_ids": str(raw_trace_id),
            "software_desc": "label-tool 1.0",
        },
        files={
            "file": ("qos.csv", qos_csv_bytes, "text/csv"),
        },
        headers=admin_headers,
    )
    assert up.status_code in (200, 201), up.text

    resp = client.get(
        "/labeled-traces/search",
        params={"donor_raw_trace_id": raw_trace_id},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert raw_trace_id in data[0]["donor_raw_trace_ids"]


def test_download_labeled_trace(client, admin_headers, created_group, qos_csv_bytes):
    group_id = created_group["id"]
    raw_trace_id = upload_raw_trace(client, admin_headers, group_id)

    up = client.post(
        "/labeled-traces",
        data={
            "kind": "qos",
            "raw_trace_ids": str(raw_trace_id),
            "software_desc": "label-tool 1.0",
        },
        files={
            "file": ("qos.csv", qos_csv_bytes, "text/csv"),
        },
        headers=admin_headers,
    )
    labeled_id = up.json()["id"]

    resp = client.get(f"/labeled-traces/{labeled_id}/download", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.content


def test_export_labeled_trace_segment(client, admin_headers, created_group, qos_csv_bytes):
    group_id = created_group["id"]
    raw_trace_id = upload_raw_trace(client, admin_headers, group_id)

    up = client.post(
        "/labeled-traces",
        data={
            "kind": "qos",
            "raw_trace_ids": str(raw_trace_id),
            "software_desc": "label-tool 1.0",
        },
        files={
            "file": ("qos.csv", qos_csv_bytes, "text/csv"),
        },
        headers=admin_headers,
    )
    labeled_id = up.json()["id"]

    resp = client.get(
        f"/labeled-traces/{labeled_id}/export",
        params={
            "t_from": "2025-07-02T00:41:04",
            "t_to": "2025-07-02T00:41:05",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.content