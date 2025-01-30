"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints.
"""

from flask import request, jsonify, Blueprint
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from api.models import db, User, Favorite, Planet, People
from api.utils import generate_sitemap, APIException

api = Blueprint('api', __name__)  
CORS(api)  
bcrypt = Bcrypt()  


@api.route("/")
def sitemap():
    return generate_sitemap(api)


@api.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or 'name' not in data or 'email' not in data or 'password' not in data:
        raise APIException("Faltan datos obligatorios", status_code=400)

    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        raise APIException("El usuario ya está registrado", status_code=400)

    new_user = User(name=data['name'], email=data['email'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "Usuario registrado con éxito"}), 201

@api.route('/sign-in', methods=['POST'])
def sign_in():
    data = request.get_json()

    if not data or 'email' not in data or 'password' not in data:
        raise APIException("Correo y contraseña son obligatorios", status_code=400)

    user = User.query.filter_by(email=data['email']).first()

    if user and bcrypt.check_password_hash(user.password, data['password']):
        token = create_access_token(identity=user.id)
        return jsonify({"message": "Inicio de sesión exitoso", "token": token}), 200
    else:
        raise APIException("Credenciales inválidas", status_code=401)


@api.route('/sign-out', methods=['POST'])
def sign_out():
    return jsonify({"message": "Sesión cerrada exitosamente"}), 200  


@api.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        raise APIException("Usuario no encontrado", status_code=404)

    return jsonify({"id": user.id, "name": user.name, "email": user.email}), 200

@api.route('/favorites', methods=['GET'])
@jwt_required()
def get_favorites():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        raise APIException("Usuario no encontrado", status_code=404)

    favorites = Favorite.query.filter_by(user_id=user_id).all()
    
    return jsonify([favorite.serialize() for favorite in favorites]), 200

@api.route('/favorites', methods=['POST'])
@jwt_required()
def add_favorite():
    user_id = get_jwt_identity()
    data = request.get_json()

    if 'planet_id' not in data and 'people_id' not in data:
        raise APIException("Debe proporcionar un planet_id o people_id", status_code=400)

    planet_id = data.get('planet_id')
    people_id = data.get('people_id')

    if planet_id:
        planet = Planet.query.get(planet_id)
        if not planet:
            raise APIException("El planeta no existe", status_code=404)
        new_favorite = Favorite(user_id=user_id, planet_id=planet_id)

    elif people_id:
        person = People.query.get(people_id)
        if not person:
            raise APIException("El personaje no existe", status_code=404)
        new_favorite = Favorite(user_id=user_id, people_id=people_id)

    else:
        raise APIException("Debe incluir un planet_id o people_id válido", status_code=400)

    db.session.add(new_favorite)
    db.session.commit()

    return jsonify({"message": "Favorito agregado exitosamente"}), 201

@api.route('/favorites/<int:favorite_id>', methods=['DELETE'])
@jwt_required()
def delete_favorite(favorite_id):
    user_id = get_jwt_identity()
    favorite = Favorite.query.filter_by(id=favorite_id, user_id=user_id).first()

    if not favorite:
        raise APIException("Favorito no encontrado o no pertenece al usuario", status_code=404)

    db.session.delete(favorite)
    db.session.commit()

    return jsonify({"message": "Favorito eliminado exitosamente"}), 200
