"""
This module contains a unit tests for the Flask application.
"""

import pytest
from app import app, users_collection


@pytest.fixture
def client():
    """Set up the test client for Flask."""
    app.config["TESTING"] = True

    test_users_collection = app.config["TEST_USERS_COLLECTION"] = (
        users_collection.database["test_users"]
    )

    with app.test_client() as client:
        with app.app_context():
            test_users_collection.delete_many({})
        yield client

    with app.app_context():
        test_users_collection.drop()


@pytest.fixture
def test_users():
    """Provide a reference to the test users collection."""
    return app.config["TEST_USERS_COLLECTION"]


def test_home(client):
    """Test the home page."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome" in response.data


def test_register_existing_user(client, test_users):
    """Test registration with an existing username."""
    test_users.insert_one({"username": "existinguser", "password": "mockpassword"})
    response = client.post(
        "/register",
        data={"username": "existinguser", "password": "newpassword"},
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_login_failure(client):
    response = client.post(
        "/login",
        data={"username": "wronguser", "password": "wrongpassword"},
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_logout(client):
    """Test the logout functionality."""
    with client.session_transaction() as sess:
        sess["username"] = "testuser"
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200


def test_profile(client, test_users):
    """Test profile updates."""
    with client.session_transaction() as sess:
        sess["username"] = "testuser"
    test_users.insert_one({"username": "testuser", "dietary_restrictions": []})
    response = client.post(
        "/profile",
        data={"restrictions": ["vegan", "gluten-free"]},
        follow_redirects=True,
    )
    assert response.status_code == 200


def test_pantry(client, test_users):
    """Test pantry functionality."""
    with client.session_transaction() as sess:
        sess["username"] = "testuser"
    test_users.insert_one({"username": "testuser", "pantry": []})
    response = client.post(
        "/pantry", data={"ingredient": "onion"}, follow_redirects=True
    )
    assert response.status_code == 200


def test_remove_pantry_item(client, test_users):
    """Test removing an item from the pantry."""
    with client.session_transaction() as sess:
        sess["username"] = "testuser"
    test_users.insert_one({"username": "testuser", "pantry": ["onion"]})
    response = client.post(
        "/pantry/delete", data={"ingredient": "onion"}, follow_redirects=True
    )
    assert response.status_code == 200


def test_unsave_recipe(client, test_users):
    """Test unsaving a recipe."""
    with client.session_transaction() as sess:
        sess["username"] = "testuser"
    test_users.insert_one(
        {
            "username": "testuser",
            "saved_recipes": [{"recipe_id": "recipe123", "name": "Test Recipe"}],
        }
    )
    response = client.post(
        "/unsave_recipe", data={"recipe_id": "recipe123"}, follow_redirects=True
    )
    assert response.status_code == 200


def test_search_recipes_empty_pantry(client, test_users):
    """Test searching recipes with an empty pantry."""
    with client.session_transaction() as sess:
        sess["username"] = "testuser"
    test_users.insert_one({"username": "testuser", "pantry": []})
    response = client.get("/search", follow_redirects=True)
    assert response.status_code == 200


def test_search_recipes_with_pantry(client, test_users):
    """Test searching recipes with items in the pantry."""
    with client.session_transaction() as sess:
        sess["username"] = "testuser"
    test_users.insert_one({"username": "testuser", "pantry": ["chicken"]})
    response = client.get("/search", follow_redirects=True)
    assert response.status_code == 200


def test_mark_recipe_as_made(client):
    """Test marking a recipe as made."""
    with client.session_transaction() as sess:
        sess["username"] = "testuser"
    users_collection.insert_one(
        {
            "username": "testuser",
            "saved_recipes": [{"recipe_id": "recipe123", "name": "Test Recipe"}],
        }
    )
    response = client.post(
        "/made_recipes", data={"recipe_id": "recipe123"}, follow_redirects=True
    )
    assert response.status_code == 200
    assert response.status_code == 200


def test_remove_made_recipe(client, test_users):
    """Test removing a recipe from made recipes."""
    with client.session_transaction() as sess:
        sess["username"] = "testuser"
    test_users.insert_one(
        {
            "username": "testuser",
            "made_recipes": [{"recipe_id": "recipe123", "name": "Test Recipe"}],
        }
    )
    response = client.post(
        "/unmade_made_recipe", data={"recipe_id": "recipe123"}, follow_redirects=True
    )
    assert response.status_code == 200


def test_access_profile_without_login(client):
    """Test accessing the profile page without logging in."""
    response = client.get("/profile", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data


def test_access_saved_recipes_without_login(client):
    """Test accessing saved recipes without logging in."""
    response = client.get("/saved_recipes", follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data


def test_update_pantry(client, test_users):
    """Test updating the pantry."""
    with client.session_transaction() as sess:
        sess["username"] = "testuser"
    test_users.insert_one({"username": "testuser", "pantry": []})
    response = client.post(
        "/pantry", data={"ingredient": "tomato"}, follow_redirects=True
    )

    assert response.status_code == 200
