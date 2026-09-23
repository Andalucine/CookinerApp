def test_notes_crud_and_search(client, seeded, make_user):
    h, user = make_user()
    r = client.post(
        "/notes", json={"title": "Menú de Nochebuena", "content": "Sopa de marisco, cordero"},
        headers=h,
    )  # fmt: skip
    assert r.status_code == 201, r.text
    note = r.json()
    assert note["notebook_id"] == user["notebook_id"] and note["added_by"] is None
    client.post(
        "/notes", json={"title": "Pescadería Manolo", "content": "Martes y jueves"}, headers=h
    )

    assert len(client.get("/notes", headers=h).json()) == 2
    found = client.get("/notes?q=cordero", headers=h).json()
    assert [n["title"] for n in found] == ["Menú de Nochebuena"]
    assert found[0]["preview"] == "Sopa de marisco, cordero"

    r = client.put(f"/notes/{note['id']}", json={"title": "Nochebuena 2026"}, headers=h)
    assert r.json()["title"] == "Nochebuena 2026" and r.json()["content"] is None
    assert client.delete(f"/notes/{note['id']}", headers=h).status_code == 200
    assert client.get(f"/notes/{note['id']}", headers=h).status_code == 404


def test_notes_roles(client, seeded, make_user, share):
    ana_h, _ = make_user("Ana")
    luis_h, _ = make_user("Luis")
    eva_h, _ = make_user("Eva")
    nb = share(ana_h, "ana@example.com", luis_h, role="editor")
    share(ana_h, "ana@example.com", eva_h, role="viewer")
    ana_note = client.post("/notes", json={"title": "Trucos"}, headers=ana_h).json()

    # Editor adds a note in Ana's notebook and edits Ana's note
    r = client.post("/notes", json={"title": "Idea de Luis", "notebook_id": nb}, headers=luis_h)
    assert r.status_code == 201 and r.json()["added_by"] == "Luis"
    luis_note = r.json()
    r = client.put(f"/notes/{ana_note['id']}", json={"title": "Trucos de casa"}, headers=luis_h)
    assert r.json()["edited_by"] == "Luis" and r.json()["added_by"] is None
    # ...but cannot delete Ana's note; Ana can delete Luis's
    assert client.delete(f"/notes/{ana_note['id']}", headers=luis_h).status_code == 403
    assert client.delete(f"/notes/{luis_note['id']}", headers=ana_h).status_code == 200

    # Viewer reads, does not write
    assert len(client.get(f"/notes?notebook_id={nb}", headers=eva_h).json()) == 1
    assert client.get(f"/notes/{ana_note['id']}", headers=eva_h).status_code == 200
    r = client.post("/notes", json={"title": "x", "notebook_id": nb}, headers=eva_h)
    assert r.status_code == 404
    assert (
        client.put(f"/notes/{ana_note['id']}", json={"title": "x"}, headers=eva_h).status_code
        == 404
    )

    # A stranger sees nothing
    pepe_h, _ = make_user("Pepe")
    assert client.get(f"/notes?notebook_id={nb}", headers=pepe_h).status_code == 404
    assert client.get(f"/notes/{ana_note['id']}", headers=pepe_h).status_code == 404
