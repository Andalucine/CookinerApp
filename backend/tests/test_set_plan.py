from scripts import set_plan


def test_set_plan_changes_plan_and_limits(client, db_session, make_user):
    headers, _ = make_user("Beatriz", email="Beatriz@Correo.es")
    assert set_plan.main(["beatriz@correo.es", "individual"], db=db_session) == 0
    me = client.get("/auth/me", headers=headers).json()
    assert me["plan"] == "individual"
    assert me["max_recipes"] is None and me["max_shared_with"] == 2


def test_set_plan_rejects_unknown_plan_or_account(db_session, make_user, capsys):
    make_user("Ana")
    assert set_plan.main(["ana@example.com", "premium"], db=db_session) == 1
    assert set_plan.main(["nadie@example.com", "family"], db=db_session) == 1
    assert set_plan.main([], db=db_session) == 1
    out = capsys.readouterr().out
    assert "Plan desconocido" in out and "No hay ninguna cuenta" in out
