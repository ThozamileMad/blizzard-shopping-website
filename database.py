from flask_sqlalchemy import SQLAlchemy


def sqlalchemy_class(app):
    return SQLAlchemy(app)


def user_database(app, usermixin, db):
    with app.app_context():
        class User(usermixin, db.Model):
            id = db.Column(db.Integer, primary_key=True)
            name = db.Column(db.String,  nullable=False, unique=False)
            email = db.Column(db.String, nullable=False, unique=True)
            password = db.Column(db.String, nullable=False, unique=False)

        class Cart(db.Model):
            __bind_key__ = "carts"
            id = db.Column(db.Integer, primary_key=True)
            user_id = db.Column(db.Integer, unique=False, nullable=False)
            item = db.Column(db.String, unique=False, nullable=True)
            price = db.Column(db.String, unique=False, nullable=True)
            url = db.Column(db.String, unique=False, nullable=True)
            quantity = db.Column(db.Integer, unique=False, nullable=False)

        class ProductData(db.Model):
            __bind_key__ = "product_data"
            id = db.Column(db.Integer, primary_key=True)
            category = db.Column(db.String, nullable=False)
            name = db.Column(db.String, unique=True, nullable=False)
            image_url = db.Column(db.String, unique=True, nullable=False)
            price = db.Column(db.String, nullable=False)

        class UserInputData(db.Model):
            __bind_key__ = "user_input_data"
            id = db.Column(db.Integer, primary_key=True)
            country_region = db.Column(db.String, nullable=True)
            first_name = db.Column(db.String, nullable=True)
            last_name = db.Column(db.String, nullable=True)
            address = db.Column(db.String, nullable=True)
            city = db.Column(db.String, nullable=True)
            province = db.Column(db.String, nullable=True)
            postal_code = db.Column(db.String, nullable=True)
            phone_number = db.Column(db.String, nullable=True)
            card_number = db.Column(db.String, nullable=True)
            expiration_date = db.Column(db.String, nullable=True)
            security_code = db.Column(db.String, nullable=True)
            name_on_card = db.Column(db.String, nullable=True)
            sb_addr = db.Column(db.String, nullable=True)
            remember = db.Column(db.Boolean, nullable=True)

        db.create_all()

    return [User, Cart, ProductData, UserInputData]
