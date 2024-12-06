import os
import logging
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from pymongo import MongoClient
from dotenv import load_dotenv

import bcrypt
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "SECRET_KEY")
app.config["SESSION_PERMANENT"] = False

mongo_uri = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")
client = MongoClient(mongo_uri)
db = client["whatscookin"]
users_collection = db["users"]

EDAMAM_APP_ID = os.getenv("EDAMAM_APP_ID")
EDAMAM_APP_KEY = os.getenv("EDAMAM_APP_KEY")
EDAMAM_BASE_URL = "https://api.edamam.com/api/recipes/v2"

logging.basicConfig(level=logging.INFO)


def login_required(func):
    def wrapper(*args, **kwargs):
        if "username" not in session:
            flash("Please log in to access this page.")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper


@app.route("/")
def home():
    username = session.get("username")
    return render_template("home.html", username=username)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode("utf-8")

        user = users_collection.find_one({"username": username})
        if user and bcrypt.checkpw(password, user["password"]):
            session["username"] = username
            session.permanent = False
            return redirect(url_for("home"))
        flash("Invalid username or password. Please try again.")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"].encode("utf-8")

        if users_collection.find_one({"username": username}):
            flash("Username already exists. Please choose a different one.")
        else:
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
            users_collection.insert_one(
                {"username": username, "password": hashed_password}
            )
            flash("Registration successful! Please log in.")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


HEALTH_LABELS = [
    {"web_label": "Alcohol-Cocktail", "api_param": "alcohol-cocktail"},
    {"web_label": "Alcohol-Free", "api_param": "alcohol-free"},
    {"web_label": "Celery-Free", "api_param": "celery-free"},
    {"web_label": "Crustacean-Free", "api_param": "crustacean-free"},
    {"web_label": "Dairy-Free", "api_param": "dairy-free"},
    {"web_label": "DASH", "api_param": "DASH"},
    {"web_label": "Egg-Free", "api_param": "egg-free"},
    {"web_label": "Fish-Free", "api_param": "fish-free"},
    {"web_label": "FODMAP-Free", "api_param": "fodmap-free"},
    {"web_label": "Gluten-Free", "api_param": "gluten-free"},
    {"web_label": "Immuno-Supportive", "api_param": "immuno-supportive"},
    {"web_label": "Keto-Friendly", "api_param": "keto-friendly"},
    {"web_label": "Kidney-Friendly", "api_param": "kidney-friendly"},
    {"web_label": "Kosher", "api_param": "kosher"},
    {"web_label": "Low Potassium", "api_param": "low-potassium"},
    {"web_label": "Low Sugar", "api_param": "low-sugar"},
    {"web_label": "Lupine-Free", "api_param": "lupine-free"},
    {"web_label": "Mediterranean", "api_param": "Mediterranean"},
    {"web_label": "Mollusk-Free", "api_param": "mollusk-free"},
    {"web_label": "Mustard-Free", "api_param": "mustard-free"},
    {"web_label": "No oil added", "api_param": "No-oil-added"},
    {"web_label": "Paleo", "api_param": "paleo"},
    {"web_label": "Peanut-Free", "api_param": "peanut-free"},
    {"web_label": "Pescatarian", "api_param": "pecatarian"},
    {"web_label": "Pork-Free", "api_param": "pork-free"},
    {"web_label": "Red-Meat-Free", "api_param": "red-meat-free"},
    {"web_label": "Sesame-Free", "api_param": "sesame-free"},
    {"web_label": "Shellfish-Free", "api_param": "shellfish-free"},
    {"web_label": "Soy-Free", "api_param": "soy-free"},
    {"web_label": "Sugar-Conscious", "api_param": "sugar-conscious"},
    {"web_label": "Sulfite-Free", "api_param": "sulfite-free"},
    {"web_label": "Tree-Nut-Free", "api_param": "tree-nut-free"},
    {"web_label": "Vegan", "api_param": "vegan"},
    {"web_label": "Vegetarian", "api_param": "vegetarian"},
    {"web_label": "Wheat-Free", "api_param": "wheat-free"},
]


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    username = session["username"]

    if request.method == "POST":
        dietary_restrictions = request.form.getlist("restrictions")
        users_collection.update_one(
            {"username": username},
            {"$set": {"dietary_restrictions": dietary_restrictions}},
        )
        flash("Dietary restrictions updated successfully.")
        return redirect(url_for("profile"))

    user = users_collection.find_one({"username": username})
    dietary_restrictions = user.get("dietary_restrictions", []) if user else []

    return render_template(
        "profile.html",
        dietary_restrictions=dietary_restrictions,
        health_labels=HEALTH_LABELS,
    )


@app.route("/search", methods=["GET"])
@login_required
def search_recipes():
    username = session["username"]

    user = users_collection.find_one({"username": username})
    if not user:
        flash("User not found.")
        return redirect(url_for("home"))

    pantry_items = user.get("pantry", [])
    dietary_restrictions = user.get("dietary_restrictions", [])

    if not pantry_items:
        flash("Your pantry is empty. Add items to your pantry to search recipes.")
        return render_template("recipes.html", recipes=[], query="")

    recipes = fetch_recipes_from_api(pantry_items, dietary_restrictions)
    return render_template(
        "recipes.html", recipes=recipes, pantry_items=pantry_items
    )


def fetch_recipes_from_api(pantry_items, dietary_restrictions):
    recipes_dict = {}
    common_params = {
        "type": "public",
        "app_id": EDAMAM_APP_ID,
        "app_key": EDAMAM_APP_KEY,
        "from": 0,
        "to": 10,
    }

    if dietary_restrictions:
        common_params["health"] = dietary_restrictions

    try:
        for item in pantry_items:
            params = common_params.copy()
            params["q"] = item
            response = requests.get(EDAMAM_BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            hits = response.json().get("hits", [])

            for recipe_data in hits:
                recipe = recipe_data["recipe"]
                recipe_uri = recipe.get("uri", "")
                recipe_id = recipe_uri.split("#")[-1]

                if recipe_id not in recipes_dict:
                    recipes_dict[recipe_id] = {
                        "recipe_id": recipe_id,
                        "name": recipe.get("label", "N/A"),
                        "image": recipe.get("image", ""),
                        "source": recipe.get("source", "Unknown"),
                        "url": recipe.get("url", "#"),
                        "dietary_restrictions": recipe.get("healthLabels", []),
                    }
        return list(recipes_dict.values())
    except requests.exceptions.RequestException as e:
        flash(f"An error occurred while fetching recipes: {str(e)}")
        return []


@app.route("/pantry", methods=["GET", "POST"])
@login_required
def pantry():
    username = session["username"]

    if request.method == "POST":
        ingredient = request.form.get("ingredient")
        if ingredient:
            users_collection.update_one(
                {"username": username}, {"$addToSet": {"pantry": ingredient}}
            )
        return redirect(url_for("pantry"))

    user = users_collection.find_one({"username": username})
    pantry_items = user.get("pantry", []) if user else []

    return render_template("pantry.html", pantry_items=pantry_items)


@app.route("/pantry/delete", methods=["POST"])
@login_required
def delete_pantry_item():
    username = session["username"]
    ingredient = request.form.get("ingredient")
    if ingredient:
        users_collection.update_one(
            {"username": username}, {"$pull": {"pantry": ingredient}}
        )
        flash(f"Removed '{ingredient}' from your pantry.")
    return redirect(url_for("pantry"))


@app.route("/save_recipe", methods=["POST"])
@login_required
def save_recipe():
    username = session["username"]
    recipe_data = request.json

    if not recipe_data or "recipe_id" not in recipe_data:
        return jsonify({"message": "Invalid recipe data."}), 400

    user = users_collection.find_one({"username": username})

    if user:
        user_saved_recipes = user.get("saved_recipes", [])
        if any(recipe["recipe_id"] == recipe_data["recipe_id"] for recipe in user_saved_recipes):
            return jsonify({"message": "Recipe already saved."}), 400

        users_collection.update_one(
            {"username": username}, {"$push": {"saved_recipes": recipe_data}}
        )
        return jsonify({"message": "Recipe saved successfully."}), 200

    return jsonify({"message": "User not found."}), 404


@app.route("/unsave_recipe", methods=["POST"])
@login_required
def unsave_recipe():
    username = session["username"]
    recipe_id = request.form.get("recipe_id")

    users_collection.update_one(
        {"username": username}, {"$pull": {"saved_recipes": {"recipe_id": recipe_id}}}
    )
    flash("Recipe removed from saved list.")
    return redirect(url_for("saved_recipes"))


@app.route("/recipe/<recipe_id>", methods=["GET"])
@login_required
def get_recipe_details(recipe_id):
    try:
        response = requests.get(
            f"{EDAMAM_BASE_URL}/{recipe_id}",
            params={
                "type": "public",
                "app_id": EDAMAM_APP_ID,
                "app_key": EDAMAM_APP_KEY,
            },
            timeout=10,
        )
        response.raise_for_status()
        recipe = response.json().get("recipe", {})
        return jsonify(recipe)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


@app.route("/made_recipe", methods=["POST"])
@login_required
def made_recipe():
    username = session["username"]
    data = request.get_json()
    recipe_id = data.get("recipe_id")
    liked = data.get("liked", False)

    if not recipe_id:
        return jsonify({"success": False, "message": "No recipe_id provided."}), 400

    user = users_collection.find_one({"username": username})
    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    user_saved_recipes = user.get("saved_recipes", [])
    recipe_to_move = None
    for recipe in user_saved_recipes:
        if recipe["recipe_id"] == recipe_id:
            recipe_to_move = recipe
            break

    if not recipe_to_move:
        return jsonify({"success": False, "message": "Recipe not found in saved recipes."}), 404

    recipe_to_move["liked"] = liked

    users_collection.update_one(
        {"username": username},
        {"$pull": {"saved_recipes": {"recipe_id": recipe_id}}}
    )
    users_collection.update_one(
        {"username": username},
        {"$addToSet": {"made_recipes": recipe_to_move}}
    )

    return jsonify({"success": True, "message": "Recipe marked as made.", "liked": liked}), 200


@app.route("/unsave_made_recipe", methods=["POST"])
@login_required
def unsave_made_recipe():
    username = session["username"]
    recipe_id = request.form.get("recipe_id")

    users_collection.update_one(
        {"username": username}, {"$pull": {"made_recipes": {"recipe_id": recipe_id}}}
    )
    flash("Recipe removed from made recipes.")
    return redirect(url_for("saved_recipes"))

@app.route("/reset_recipe", methods=["POST"])
@login_required
def reset_recipe():
    username = session["username"]
    recipe_id = request.form.get("recipe_id")

    user = users_collection.find_one({"username": username})
    if not user:
        flash("User not found.")
        return redirect(url_for("saved_recipes"))

    made_recipes = user.get("made_recipes", [])
    recipe_to_reset = None
    for recipe in made_recipes:
        if recipe["recipe_id"] == recipe_id:
            recipe_to_reset = recipe
            break

    if recipe_to_reset:
        recipe_to_reset.pop("liked", None)
        users_collection.update_one(
            {"username": username},
            {"$pull": {"made_recipes": {"recipe_id": recipe_id}}}
        )
        users_collection.update_one(
            {"username": username},
            {"$push": {"saved_recipes": recipe_to_reset}}
        )
        flash("Recipe reset to default state.")
    else:
        flash("Recipe not found in made recipes.")

    return redirect(url_for("saved_recipes"))


@app.route("/saved_recipes")
@login_required
def saved_recipes():
    username = session["username"]
    user = users_collection.find_one({"username": username})

    if user:
        user_saved_recipes = user.get("saved_recipes", [])
        made_recipes = user.get("made_recipes", [])
        return render_template(
            "saved_recipes.html",
            saved_recipes=user_saved_recipes,
            made_recipes=made_recipes,
        )
    flash("User not found.")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
