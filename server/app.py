#!/usr/bin/env python3

from flask import request, session
from sqlalchemy.exc import IntegrityError

from config import app, db
from models import User, Recipe

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username:
        return {'message': 'username required'}, 422

    try:
        user = User(
            username=username,
            bio=data.get('bio'),
            image_url=data.get('image_url')
        )
        user.password_hash = password

        db.session.add(user)
        db.session.commit()

        session['user_id'] = user.id

        return user.to_dict(), 201

    except IntegrityError:
        db.session.rollback()
        return {'message': 'Username must be unique'}, 422
    except ValueError as e:
        db.session.rollback()
        return {'message': str(e)}, 422

@app.route('/check_session', methods=['GET'])
def check_session():
    user_id = session.get('user_id')
    if not user_id:
        return {'message': 'Unauthorized'}, 401

    user = User.query.get(user_id)
    if not user:
        return {'message': 'Unauthorized'}, 401

    return user.to_dict()

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter(User.username == username).first()
    if not user or not user.authenticate(password):
        return {'message': 'Invalid credentials'}, 401

    session['user_id'] = user.id
    return user.to_dict()

@app.route('/logout', methods=['DELETE'])
def logout():
    if not session.get('user_id'):
        return {'message': 'Unauthorized'}, 401

    session.pop('user_id')
    return {}, 204

@app.route('/recipes', methods=['GET', 'POST'])
def recipes_index():
    user_id = session.get('user_id')
    if not user_id:
        return {'message': 'Unauthorized'}, 401
    
    user = User.query.get(user_id)
    if not user:
        return {'message': 'Unauthorized'}, 401

    if request.method == 'GET':
        return [r.to_dict() for r in user.recipes], 200

    elif request.method == 'POST':
        data = request.get_json()
        try:
            recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete')
            )
            recipe.user = user

            db.session.add(recipe)
            db.session.commit()

            return recipe.to_dict(), 201

        except IntegrityError:
            db.session.rollback()
            return {'message': 'Title must be unique'}, 422
        except ValueError as e:
            db.session.rollback()
            return {'message': str(e)}, 422

@app.route('/recipes/<int:id>', methods=['GET', 'PATCH', 'DELETE'])
def recipe_by_id(id):
    recipe = Recipe.query.get(id)
    if not recipe:
        return {'message': 'Recipe not found'}, 404

    user_id = session.get('user_id')
    if not user_id or recipe.user_id != user_id:
        return {'message': 'Unauthorized'}, 401

    if request.method == 'GET':
        return recipe.to_dict()

    elif request.method == 'PATCH':
        data = request.get_json()
        try:
            for key, value in data.items():
                setattr(recipe, key, value)
            
            db.session.commit()
            return recipe.to_dict()
        except (IntegrityError, ValueError) as e:
            db.session.rollback()
            return {'message': str(e)}, 422

    elif request.method == 'DELETE':
        db.session.delete(recipe)
        db.session.commit()
        return {}, 204

if __name__ == '__main__':
    app.run(port=5555, debug=True)