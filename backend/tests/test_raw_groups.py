def test_create_raw_group(client, admin_headers, sample_group_payload):
    resp = client.post("/raw-groups", json=sample_group_payload, headers=admin_headers)
    assert resp.status_code in (200, 201), resp.text
    data = resp.json()
    assert data["org"] == "MSU"
    assert data["capture_points"] == 1
    assert "id" in data
    assert data["name"] == sample_group_payload["name"]


def test_upload_group_description(client, admin_headers, created_group):
    group_id = created_group["id"]
    files = {
        "file": ("description.md", b"# Test group\nSome text", "text/markdown"),
    }
    resp = client.post(
        f"/raw-groups/{group_id}/upload-description",
        files=files,
        headers=admin_headers,
    )
    assert resp.status_code in (200, 201), resp.text


def test_upload_group_schema(client, admin_headers, created_group):
    group_id = created_group["id"]
    files = {
        "file": ("schema.png", b"fake-image-content", "image/png"),
    }
    resp = client.post(
        f"/raw-groups/{group_id}/upload-schema",
        files=files,
        headers=admin_headers,
    )
    assert resp.status_code in (200, 201), resp.text