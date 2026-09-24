"""Photos sent from the phone (session 9): kept in the uploads folder, served without login."""

from app.core.config import get_settings

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def test_upload_and_get_a_photo(client, make_user, tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "uploads_dir", str(tmp_path))
    h, _ = make_user()
    r = client.post("/photos", files={"file": ("foto.jpg", JPEG, "image/jpeg")}, headers=h)
    assert r.status_code == 201, r.text
    url = r.json()["url"]
    assert url.startswith("/photos/") and url.endswith(".jpg")
    assert (tmp_path / url.split("/")[-1]).read_bytes() == JPEG

    got = client.get(url)  # no login needed to show it
    assert got.status_code == 200 and got.content == JPEG

    # the iPhone camera sends HEIC without a content type sometimes: the name decides
    r = client.post("/photos", files={"file": ("IMG_1.png", PNG, "")}, headers=h)
    assert r.status_code == 201 and r.json()["url"].endswith(".png")


def test_only_photos_and_only_ours(client, make_user, tmp_path, monkeypatch):
    monkeypatch.setattr(get_settings(), "uploads_dir", str(tmp_path))
    h, _ = make_user()
    r = client.post("/photos", files={"file": ("x.txt", b"hola", "text/plain")}, headers=h)
    assert r.status_code == 415
    r = client.post("/photos", files={"file": ("x.jpg", b"not really", "image/jpeg")}, headers=h)
    assert r.status_code == 415
    assert client.post("/photos", files={"file": ("x.jpg", JPEG, "image/jpeg")}).status_code == 401
    assert client.get("/photos/../pyproject.toml").status_code in (404, 400)
    assert client.get("/photos/" + "0" * 32 + ".jpg").status_code == 404


def test_photo_on_a_pantry_item_and_a_shopping_line(client, seeded, make_user):
    h, _ = make_user()
    item = client.post("/pantry/items", json={"name": "leche"}, headers=h).json()
    r = client.patch(f"/pantry/items/{item['id']}", json={"image_url": "/photos/a.jpg"}, headers=h)
    assert r.status_code == 200 and r.json()["image_url"] == "/photos/a.jpg"
    assert client.get("/pantry", headers=h).json()["items"][0]["image_url"] == "/photos/a.jpg"
    r = client.patch(f"/pantry/items/{item['id']}", json={"image_url": None}, headers=h)
    assert r.json()["image_url"] is None

    line = client.post("/shopping-list/items", json={"text": "tomate frito"}, headers=h).json()
    r = client.patch(
        f"/shopping-list/items/{line['id']}", json={"image_url": "/photos/b.jpg"}, headers=h
    )
    assert r.status_code == 200 and r.json()["image_url"] == "/photos/b.jpg"
    # moving it keeps the photo; the photo alone keeps the section
    r = client.patch(
        f"/shopping-list/items/{line['id']}", json={"section_code": "other"}, headers=h
    )
    assert r.json()["image_url"] == "/photos/b.jpg"
    sections = client.get("/shopping-list", headers=h).json()["sections"]
    assert [s["code"] for s in sections] == ["other"]
    assert sections[0]["items"][0]["image_url"] == "/photos/b.jpg"
