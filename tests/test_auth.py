def test_login_with_invalid_user(test_app):
    client = test_app.test_client()

    response = client.post("/token", data={
        "username": "nonexistent",
        "password": "wrongpass"
    })

    assert response.status_code == 400
    assert "Incorrect username or password" in response.json["detail"]

