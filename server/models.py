from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin

from config import db, bcrypt

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'
    
    serialize_rules = ('-_password_hash', '-recipes.user',)
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    _password_hash = db.Column('password_hash', db.String)
    image_url = db.Column(db.String)
    bio = db.Column(db.String)
    
    recipes = db.relationship('Recipe', back_populates='user', cascade='all, delete')
    
    @hybrid_property
    def password_hash(self):
        raise AttributeError('password_hash is not readable')
    
    @password_hash.setter
    def password_hash(self, password):
        self._password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'
    
    serialize_rules = ('-user.recipes',)
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    minutes_to_complete = db.Column(db.Integer)
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship('User', back_populates='recipes')
    
    @validates('instructions')
    def validate_instructions(self, key, instructions):
        if not instructions or len(instructions) < 50:
            raise ValueError('instructions must be at least 50 characters')
        return instructions