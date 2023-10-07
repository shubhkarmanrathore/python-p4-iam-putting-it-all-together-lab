#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe


class Signup(Resource):
    def post(self):
        json = request.get_json()
        try:
            json["username"]
        except KeyError:
            return {"Message": "Unprocessable Entity"}, 422

        try:
            json["image_url"]
        except KeyError:
            user = User(
                username=json["username"],
            )
        else:
            user = User(
                username=json["username"], image_url=json["image_url"], bio=json["bio"]
            )

        user.password_hash = json["password"]
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id

        return (
            {
                "id": user.id,
                "username": user.username,
                "image_url": user.image_url,
                "bio": user.bio,
            }
        ), 201


class CheckSession(Resource):
    def get(self):
        user = User.query.filter(User.id == session.get("user_id")).first()

        if user:
            return (
                {
                    "id": user.id,
                    "username": user.username,
                    "image_url": user.image_url,
                    "bio": user.bio,
                }
            ), 200
        else:
            return {"Message": "Unauthorized"}, 401


class Login(Resource):
    def post(self):
        username = request.get_json()["username"]
        user = User.query.filter(User.username == username).first()

        if user:
            # get password
            password = request.get_json()["password"]

            # if the password authenticates then set the session
            # with the user's id
            if user.authenticate(password):
                session["user_id"] = user.id
                return (
                    {
                        "id": user.id,
                        "username": user.username,
                        "image_url": user.image_url,
                        "bio": user.bio,
                    }
                ), 201
        return {"error": "Invalid username or password"}, 401


class Logout(Resource):
    def delete(self):
        if session.get("user_id"):
            session["user_id"] = None
            return {}, 204
        return {"message": "unauthorized"}, 401


class RecipeIndex(Resource):
    def get(self):
        user = User.query.filter(User.id == session.get("user_id")).first()

        if user:
            recipes = [recipe.to_dict() for recipe in Recipe.query.all()]
            return (recipes), 200
        else:
            return {"message": "unauthorized"}, 401

    def post(self):
        user = User.query.filter(User.id == session.get("user_id")).first()

        if user:
            json = request.get_json()

            try:
                recipe = Recipe(
                    title=json["title"],
                    instructions=json["instructions"],
                    minutes_to_complete=json["minutes_to_complete"],
                    user_id=session["user_id"],
                )
                db.session.add(recipe)
                db.session.commit()
            except IntegrityError:
                return {"message": "Unprocessable Entity"}, 422

            return (
                {
                    "title": recipe.title,
                    "instructions": recipe.instructions,
                    "minutes_to_complete": recipe.minutes_to_complete,
                    "user_id": recipe.user_id,
                }
            ), 201
        else:
            return {"message": "unauthorized"}, 401


api.add_resource(Signup, "/signup", endpoint="signup")
api.add_resource(CheckSession, "/check_session", endpoint="check_session")
api.add_resource(Login, "/login", endpoint="login")
api.add_resource(Logout, "/logout", endpoint="logout")
api.add_resource(RecipeIndex, "/recipes", endpoint="recipes")


if __name__ == "__main__":
    app.run(port=5555, debug=True)