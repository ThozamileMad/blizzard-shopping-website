from flask import Flask, render_template, request, redirect, url_for, abort
from database import sqlalchemy_class, user_database
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from countries import country_data
from random import choice

app = Flask(__name__)
app.config["SECRET_KEY"] = "ABC"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"

app.config["SQLALCHEMY_BINDS"] = {"carts": "sqlite:///carts.db",
                                  "product_data": "sqlite:///product_data.db",
                                  "user_input_data": "sqlite:///user_input_data.db"}

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = sqlalchemy_class(app)
databases = user_database(app, UserMixin, db)

User = databases[0]
Cart = databases[1]
ProductData = databases[2]
UserInputData = databases[3]

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def restrict_signup_login(function):
    @wraps(function)
    def inner_function(*args, **kwargs):
        if current_user.is_authenticated:
            return abort(403, "Unauthorised, access denied until user is logged out.")
        else:
            return function(*args, **kwargs)
    return inner_function


def restrict_page_if_not_logged_in(function):
    @wraps(function)
    def inner_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return abort(403, "Unauthorised, access denied until user is logged in.")
        else:
            return function(*args, **kwargs)
    return inner_function


def restrict_cart_page_if_not_user(function):
    @wraps(function)
    def inner_function(*args, **kwargs):
        if int(current_user.get_id()) != kwargs["user_id"]:
            return abort(401, "Access denied, login as the user to access this page.")
        else:
            return function(*args, **kwargs)
    return inner_function


def restrict_checkout_page_if_not_user(function):
    @wraps(function)
    def inner_function(*args, **kwargs):
        id_error_lst = kwargs["id_error"].split("*")
        if int(current_user.get_id()) != int(id_error_lst[0]):
            return abort(401, "Access denied, login as the user to access this page.")
        else:
            return function(*args, **kwargs)
    return inner_function


def restrict_checkout_page_if_cart_is_empty(function):
    @wraps(function)
    def inner_function(*args, **kwargs):
        user_id = int(current_user.get_id())
        cart = [data for data in db.session.query(Cart).all() if user_id == data.user_id]
        url_lst = kwargs["id_error"].split("*")
        if len(cart) == 0 and len(url_lst) != 3:
            return abort(403, "Access denied, cart is empty.")
        else:
            return function(*args, **kwargs)
    return inner_function


def len_cart():
    in_cart = 0
    try:
        user_id = int(current_user.get_id())
        if user_id is not None:
            in_cart = len([data for data in db.session.query(Cart).all() if data.user_id == user_id])
    except TypeError:
        pass

    return in_cart


@app.route("/")
def home():
    product_d = [data.image_url for data in db.session.query(ProductData).all()]
    img_sets = [[choice(product_d), choice(product_d), choice(product_d),
                 choice(product_d), choice(product_d), choice(product_d)]
                for num in range(3)]

    return render_template("home.html",
                           img_data=img_sets,
                           is_logged_in=current_user.is_authenticated,
                           show_logout=True)


@app.route("/categories", methods=["GET", "POST"])
def category_page():
    categories = ["All Departments", "Electronics", "Computers", "Smart Home", "Arts & Crafts", "Automotive", "Baby", "Beauty and personal care", "Women's Fashion", "Men's Fashion", "Girls' Fashion", "Boys' Fashion", "Health and Household", "Home and Kitchen", "Industrial and Scientific", "Luggage", "Movies & Television", "Pet supplies"]
    if request.method == "POST":
        results = request.form.get("search").replace("/", "@")
        return redirect(url_for("search", results=results))

    return render_template("category.html",
                           categories=categories,
                           is_logged_in=current_user.is_authenticated,
                           show_search=True,
                           user_id=current_user.get_id(),
                           in_cart=len_cart(),
                           show_cart=True,
                           show_logout=True)


@app.route("/search/<results>", methods=["GET", "POST"])
def search(results):
    user_id = current_user.get_id()
    search_results = results.replace("@", "/")
    all_data = [(data.id, data.category, data.name, data.image_url, data.price) for data in db.session.query(ProductData).all()]
    sub_data = [{"data": data, "word_lst": data[2].split()} for data in all_data]
    new_data = []
    for sub_dict in sub_data:
        for word in sub_dict["word_lst"]:
            if sub_dict["data"] not in new_data and search_results.title() == word or search_results.upper() == word or search_results.lower() == word:
                new_data.append(sub_dict["data"])

    product_ids = [f"*{str(data[0])}" for data in new_data]
    if request.method == "POST":
        results = request.form.get("search").replace("/", "@")
        return redirect(url_for("search", results=results))

    if results == "not_found":
        return "<h1>Sorry</h1><p>Item doesn't exist.</p><a href='/'>Return to home page</a>"
    else:
        return render_template("search.html",
                               data=new_data,
                               data_len=len(new_data),
                               is_logged_in=current_user.is_authenticated,
                               show_search=True,
                               user_id=user_id,
                               str_user_id=str(user_id),
                               in_cart=len_cart(),
                               show_cart=True,
                               show_logout=True,
                               product_ids=product_ids)


@app.route("/display/<cate>", methods=["GET", "POST"])
def display(cate):
    all_data = [data for data in db.session.query(ProductData).all() if data.category == cate]
    product_ids = [f"*{str(data.id)}" for data in db.session.query(ProductData).all() if data.category == cate]

    if cate == "all departments":
        all_data = [data for data in db.session.query(ProductData).all()]
        product_ids = [f"*{str(data.id)}" for data in db.session.query(ProductData).all()]

    category = cate.title()
    if category == "Women'S Fashion" or category == "Men'S Fashion":
        category_letters = list(category)
        s_index = category_letters.index("'") + 1
        category_letters[s_index] = "s"
        category = "".join(category_letters)

    user_id = current_user.get_id()
    if request.method == "POST":
        results = request.form.get("search").replace("/", "@")
        return redirect(url_for("search", results=results))
    return render_template("display.html",
                           data=all_data,
                           data_len=len(all_data),
                           product_ids=product_ids,
                           category=category,
                           is_logged_in=current_user.is_authenticated,
                           show_search=True,
                           user_id=user_id,
                           str_user_id=str(user_id),
                           in_cart=len_cart(),
                           show_cart=True,
                           show_logout=True)


def db_add(data):
    item = data
    db.session.add(item)
    db.session.commit()


@app.route("/signup/<error>", methods=["GET", "POST"])
@restrict_signup_login
def signup(error):
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        hashed_password = generate_password_hash(password)

        user_emails = [user.email for user in db.session.query(User).all()]
        usernames = [user.name for user in db.session.query(User).all()]
        if email in user_emails:
            return redirect(url_for("signup", error="email"))
        elif name in usernames:
            return redirect(url_for("signup", error="username"))
        else:
            db_add(User(name=name, email=email, password=hashed_password))
            login_user(User.query.filter_by(email=email).first())
            db_add(UserInputData(country_region="", first_name="", last_name="", address="", city="", province="", postal_code="", phone_number="", card_number="", expiration_date="", security_code="", name_on_card="", sb_addr="", remember=False))
            return redirect(url_for("category_page"))
    return render_template("signup.html",
                           error=error,
                           show_login=True)


@app.route("/login/<error>", methods=["GET", "POST"])
@restrict_signup_login
def login(error):
    if request.method == "POST":
        emails = [data.email for data in db.session.query(User).all()]
        email = request.form.get("email")
        if email in emails:
            user = User.query.filter_by(email=email).first()
            password = request.form.get("password")
            hashed_password = user.password
            if check_password_hash(pwhash=hashed_password, password=password):
                login_user(user)
                return redirect(url_for("category_page"))
            else:
                return redirect(url_for("login", error="password"))
        else:
            return redirect(url_for("login", error="email"))
    return render_template("login.html",
                           error=error,
                           show_signup=True)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/add-to-cart/<int:cart_id>")
def add_to_cart(cart_id):
    user_id = int(current_user.get_id())
    item = ProductData.query.filter_by(id=cart_id).first()
    cart = [data.item for data in db.session.query(Cart).all() if data.user_id == user_id]

    if item.name not in cart:
        db_add(Cart(user_id=user_id, url=item.image_url, item=item.name, price=item.price, quantity=1))
        return redirect(url_for("cart", user_id=user_id))
    else:
        return "<h1>You can't</h1><p>Item exists in cart.</p><a href='/'>Return to home page</a>"


# Returns the user's shopping cart data from the shop_website/instance/user_input_data.db (database), including the total price of all items in the cart

def ret_cart_data(id):
    all_data = [{"id": data.id, "item": data.item, "url": data.url, "price": data.price, "quantity": data.quantity}
             for data in db.session.query(Cart).all()
             if id == data.user_id]

    total_price = sum([float(sub_data["price"][1:]) * sub_data["quantity"] for sub_data in all_data])
    rounded_total_price = round(total_price, 2)
    return {"data": all_data, "total_price": rounded_total_price, "data_len": len(all_data)}

# ----------------------------------------------------------------------------------------------------------------------

# Updates shop_website/instance/user_input_data.db (database) ----------------------------------------------------------

def modify_user_input_data(id, country, first_name, last_name, address, city, province, postal_code, phone_number,
                           card_number, ex_date, sec_code, card_name, sb_addr, remember_checkbox):
    user_input_data = UserInputData.query.filter_by(id=id).first()
    user_input_data.country_region = country
    user_input_data.first_name = first_name
    user_input_data.last_name = last_name
    user_input_data.address = address
    user_input_data.city = city
    user_input_data.province = province
    user_input_data.postal_code = postal_code
    user_input_data.phone_number = phone_number
    user_input_data.card_number = card_number
    user_input_data.expiration_date = ex_date
    user_input_data.security_code = sec_code
    user_input_data.name_on_card = card_name
    user_input_data.sb_addr = sb_addr

    if remember_checkbox == "True":
        user_input_data.remember = True
    else:
        user_input_data.remember = False

    db.session.commit()


# ----------------------------------------------------------------------------------------------------------------------

# Updates shop_website/instance/user_input_data.db (database) to empty strings if the remember checkbox is not checked -

def conditionally_modify_user_input_data(id):
    user_input_data = UserInputData.query.filter_by(id=id).first()
    if not user_input_data.remember:
        modify_user_input_data(id, "", "", "", "", "", "", "", "", "", "", "", "", "", "False")


# ----------------------------------------------------------------------------------------------------------------------

@app.route("/cart/<int:user_id>", methods=["GET", "POST"])
@restrict_page_if_not_logged_in
@restrict_cart_page_if_not_user
def cart(user_id):
    data = ret_cart_data(user_id)
    conditionally_modify_user_input_data(user_id)
    return render_template("cart.html",
                           is_logged_in=current_user.is_authenticated,
                           data=data["data"],
                           user_id=user_id,
                           str_user_id=str(user_id) + "*no_error",
                           total_price=data["total_price"],
                           cart_length=data["data_len"])


# Updates the quantity value of a specific block in the shop_website/instance/carts.db (database) ----------------------

def modify_quantity(product_id, number):
    cart = Cart.query.filter_by(id=product_id).first()
    cart.quantity = cart.quantity + number
    db.session.commit()


# ----------------------------------------------------------------------------------------------------------------------

# Increases the quantity value of a specific block in the shop_website/instance/carts.db (database) --------------------

@app.route("/add/<int:id>/<product_id>")
def add(id, product_id):
    modify_quantity(product_id, 1)
    return redirect(url_for("cart", user_id=id))


# ----------------------------------------------------------------------------------------------------------------------

# Decreases the quantity value of a specific block in the shop_website/instance/carts.db (database) --------------------

@app.route("/subtract/<int:id>/<product_id>")
def subtract(id, product_id):
    modify_quantity(product_id, -1)
    return redirect(url_for("cart", user_id=id))


# ----------------------------------------------------------------------------------------------------------------------

# Deletes specific row from shop_website/instance/carts.db (database) --------------------------------------------------

@app.route("/remove/<int:id>/<product_id>")
def remove(id, product_id):
    item = Cart.query.filter_by(id=product_id).first()
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for("cart", user_id=id))


# ----------------------------------------------------------------------------------------------------------------------


@app.route("/too_many")
def too_many():
    return "<h1>Sorry</h1><p>Unfortunately the cart is full.</p><a href='/'>Return to home page</a>"


def check_for_invalid_characters(*args, strings):
    invalid_str = ""
    for chars in args:
        for char in strings:
            if char in chars:
                invalid_str = chars
                return {"boolean": True, "index": args.index(invalid_str)}
    return False


@app.route("/checkout/<id_error>", methods=["GET", "POST"])
@restrict_page_if_not_logged_in
@restrict_checkout_page_if_not_user
@restrict_checkout_page_if_cart_is_empty
def checkout(id_error):
    int_id = int(id_error[0])
    data = ret_cart_data(int_id)

    url_values = id_error.split("*")
    current_error = url_values[1]
    if len(url_values) == 3:
        product = ProductData.query.filter_by(id=int(url_values[-1])).first()
        data["data"] = [{"id": product.id, "item": product.name, "url": product.image_url, "price": product.price,
                         "quantity": 1}]
        data["total_price"] = product.price[1:]

    input_data = UserInputData.query.filter_by(id=int_id).first()
    url_appendages = [["first_name", "last_name", "city", "province", "card_name"],
                      ["postal_code", "phone_number", "card_number", "security_code"]]
    if request.method == "POST":
        country = request.form.get("countries")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        address = request.form.get("address")
        city = request.form.get("city")
        province = request.form.get("province")
        postal_code = request.form.get("postal-code")
        phone_number = request.form.get("phone-number")
        card_number = request.form.get("card-number")
        ex_date = request.form.get("ex-date")
        sec_code = request.form.get("sec_code")
        card_name = request.form.get("card-name")
        sb_addr = request.form.get("sb-addr")
        remember_checkbox = request.form.get("remember-checkbox")

        modify_user_input_data(int_id, country, first_name, last_name, address, city, province, postal_code, phone_number,
                               card_number, ex_date, sec_code, card_name, sb_addr, remember_checkbox)

        # Validates User Inputs / Detects and shows errors on payment form ---------------------------------------------

        syms = list("`~!@#$%^&*()_+=-`<>,.?/:;''{[}]|")
        sym_input_errors = ["first_name", "last_name", "address", "city", "province", "postal_code",  "phone_number",
                            "card_number", "security_code", "card_name"]
        invalid_sym = check_for_invalid_characters(first_name, last_name, address, city, province, postal_code,
                                                   phone_number, card_number, sec_code, card_name, strings=syms)
        if invalid_sym:
            if len(url_values) != 3:
                return redirect(url_for("checkout", id_error=f"{int_id}*{sym_input_errors[invalid_sym['index']]}"))
            else:
                return redirect(url_for("checkout", id_error=f"{int_id}*{sym_input_errors[invalid_sym['index']]}*{product.id}"))

        numbers = list("0123456789")
        num_input_errors = ["first_name", "last_name", "city", "province", "card_name"]
        invalid_num = check_for_invalid_characters(first_name, last_name, city, province, card_name, strings=numbers)
        if invalid_num:
            if len(url_values) != 3:
                return redirect(url_for("checkout", id_error=f"{int_id}*{num_input_errors[invalid_num['index']]}"))
            else:
                return redirect(url_for("checkout", id_error=f"{int_id}*{num_input_errors[invalid_num['index']]}*{product.id}"))


        letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
                   'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n',
                   'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

        let_input_errors = ["postal_code",  "phone_number", "card_number", "expiration_date", "security_code"]
        invalid_let = check_for_invalid_characters(postal_code, phone_number, card_number, ex_date, sec_code, strings=letters)
        if invalid_let:
            if len(url_values) != 3:
                return redirect(url_for("checkout", id_error=f"{int_id}*{let_input_errors[invalid_let['index']]}"))
            else:
                return redirect(url_for("checkout", id_error=f"{int_id}*{let_input_errors[invalid_let['index']]}*{product.id}"))

        # ---------------------------------------------------------------------------------------------------------------

        conditionally_modify_user_input_data(int_id)
        if len(url_values) != 3:
            return redirect(url_for("success", id_erase=f"{int_id}*True"))
        else:
            return redirect(url_for("success", id_erase=f"{int_id}*False"))

    return render_template("checkout.html",
                           is_logged_in=current_user.is_authenticated,
                           data=data["data"][::-1],
                           data_len=data["data_len"],
                           user_id=int_id,
                           total_price=data["total_price"],
                           country_dict=country_data,
                           show_checkout_cart=True,
                           error=current_error,
                           input_data=input_data,
                           input_names=url_appendages,
                           url_value_3=len(url_values) == 3)


def delete_all_items_in_cart():
    cart = [data for data in db.session.query(Cart).all() if data.user_id == int(current_user.get_id())]
    for item in cart:
        db.session.delete(item)
        db.session.commit()


@app.route("/success/<id_erase>", methods=["GET", "POST"])
@restrict_page_if_not_logged_in
def success(id_erase):
    id_erase_lst = id_erase.split("*")
    user_id = int(id_erase_lst[0])
    conditionally_modify_user_input_data(user_id)
    if id_erase_lst[-1] == "True":
        delete_all_items_in_cart()
    return render_template("success.html",
                           id=user_id)


if __name__ == "__main__":
    app.run(debug=True)
