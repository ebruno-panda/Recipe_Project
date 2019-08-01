from app import app
from flask import render_template, request, redirect, session, Flask
from app.models import model, formopener
from flask_pymongo import PyMongo
import os
import random
import requests

app.secret_key = os.urandom(32)

# name of database
app.config['MONGO_DBNAME'] = 'database'

# URI of database
app.config['MONGO_URI'] = 'mongodb+srv://admin:XSsYHTHo6aoTlPas@cluster0-nmrkr.mongodb.net/database?retryWrites=true&w=majority'
# app.config['MONGO_URI'] = 'mongodb+srv://reader:yGfrgHrFDhP0de8M@cluster0-nmrkr.mongodb.net/musicDatabase?retryWrites=true&w=majority'

mongo = PyMongo(app)

@app.route('/index')
def index():
    return "hi"

@app.route('/')
def home():
    '''
    Returns either login page (ie. landing page) or profile based on whether used logged in
    '''
    print(session)
    if "username" in session:
        return redirect("/search")
    return redirect('/login')

@app.route('/register')
def register():
    '''
    Returns Registration page if user is not logged in.
    '''
    if "username" in session:
        return redirect("/search")
    return render_template('register.html')

@app.route('/login', methods=['POST',"GET"])
def login():
    '''
    Returns Login page if user is not logged in.
    '''
    if "username" in session:
        return redirect("/search")
    return render_template('login.html')

@app.route('/authenticate', methods=['POST'])
def authenticate():
    accounts = mongo.db.accounts
    '''
    References db and handles authentication (logging in) and registration.
    '''
    if "username" in session:
        return redirect("/")
    # instantiates DB_Manager with path to DB_FILE
    # data = arms.DB_Manager(DB_FILE)

    # LOGGING IN
    if request.form["submit"] == "Login":
        username, password = request.form['username'], request.form['password']
        if username != "" and password != "" and list(accounts.find({"username":username,"password":password})):
            session["username"] = username
            session["password"] = password
            # data.save()
            return redirect("/")
        # user was found in DB but password did not match
        # elif data.findUser(username):
        #     flash('Incorrect password!')
        # # user not found in DB at all
        # else:
        #     flash('Incorrect username!')
        # data.save()
        return render_template("login_invalid.html")

    # REGISTRATION
    else:
        username, password, re_password = request.form['username'], request.form['password'], request.form["re_password"]
        print("set password")
        print(list(accounts.find({"username":username})))
        if len(username.strip()) != 0 and not list(accounts.find({"username":username})):
            if len(password.strip()) != 0 and password == re_password:
                # add account to DB
                accounts.insert({"username":username, "password":password,})
                saved = mongo.db.saved
                saved.insert({"username":username, "restaurants":[], "recipes":[]})
                return redirect("/login")
        return render_template('register_invalid.html')

@app.route('/logout')
def logout():
    '''
    Logs user out if they are logged in
    Basic page is login page, not logged in users can't use features.
    '''
    session.pop("username", None)
    session.pop("password", None)
    return redirect("/login")

@app.route('/search')
def search():
    print(session)
    return render_template("index.html",  len=0)

# This is a menu screen...it's under the 'home.html' file
@app.route('/menu')
def menu():
    return render_template("home.html")

# This is the about page...it's under the 'about.html' file
@app.route('/about')
def about():
    return redirect("https://www.fintechfocus.com/")

# This is a social media/tweet screen...it's under the 'tweet.html' file
@app.route('/tweet')
def tweet():
    return render_template("tweet.html")


@app.route('/restaurants', methods = ['GET','POST'])
def restaurants():
    if request.method == "GET":
        return render_template("restaurants.html",  len=0)
    else:
        geoKey = "SdGzhhEFAKAcwxVZAbGnGtpiuz5WnnGA"

        term = request.form["term"].strip()
        distance = 0
        if request.form["distance"].strip().isdecimal():
            distance = int(request.form["distance"].strip()) * 1000
        user_address = request.form["address"].strip()

        lat = None
        lng = None

        latlng_params = {"key":geoKey,
                          "outFormat":"json",
                          "location":user_address,
                          "maxResults":1
        }

        latlng = requests.get("https://www.mapquestapi.com/geocoding/v1/address?", params = latlng_params)
        latlng_data = latlng.json()

        if latlng_data["results"][0]["locations"]:
            lat = latlng_data["results"][0]["locations"][0]["latLng"]["lat"]
            lng = latlng_data["results"][0]["locations"][0]["latLng"]["lng"]

        headers = {"user-key":"97f9f42fa19bc08f9cfdefb874d94e65"}

        location_params = {}

        if not lat is None:
            location_params["lat"] = lat
            location_params["lon"] = lng

        location_response = requests.get("https://developers.zomato.com/api/v2.1/geocode",headers=headers, params = location_params)
        location_data = location_response.json()

        entity_type = location_data["location"]["entity_type"]
        entity_id = location_data["location"]["entity_id"]

        images = []
        names = []
        links = []
        location = []

        parameters = {"q":term,
                      "count":9,
                      "radius":distance,
                      "sort":"rating",
                      "order":"desc",
                      "entity_type":entity_type,
                      "entity_id":entity_id
        }

        if not lat is None:
            parameters["lat"] = lat
            parameters["lon"] = lng

        response = requests.get("https://developers.zomato.com/api/v2.1/search",headers=headers, params = parameters)
        data = response.json()
        # print(data)
        for dic in data["restaurants"]:
            if len(dic["restaurant"]["name"].strip()) > 25:
                names.append(dic["restaurant"]["name"].strip().upper()[:24]+"...")
            else:
                names.append(dic["restaurant"]["name"].strip().upper())
            images.append(dic["restaurant"]["featured_image"])
            links.append(dic["restaurant"]["url"])
            location.append(dic["restaurant"]["location"]["address"])
        if not names:
            return render_template("restaurant_not_found.html")
        # return data
        logged_in = False
        if "username" in session:
            logged_in = True
        return render_template("restaurants.html", term = term, len = len(names), names = names, images = images, links = links, logged_in = logged_in)

@app.route('/results', methods = ['GET','POST'])
def result():
    if request.method == "GET":
        return redirect("/search")
    else:
        ingredient = request.form["ingredient"].strip()
        images = []
        recipes = []
        links = []

        parameters = {"app_id": "$f4118168",
                  "app_key": "$684f7ea2d63b6584768c1499c1a2407f",
                  "q":ingredient,
                  "to":9
        }

        response = requests.get("https://api.edamam.com/search", params = parameters)
        data = response.json()
        for dic in data["hits"]:
            if len(dic["recipe"]["label"].strip()) > 25:
                recipes.append(dic["recipe"]["label"].strip().upper()[:24]+"...")
            else:
                recipes.append(dic["recipe"]["label"].strip().upper())
            images.append(dic["recipe"]["image"])
            links.append(dic["recipe"]["url"])
        if not recipes:
            return render_template("recipe_not_found.html")
        logged_in = False
        if "username" in session:
            logged_in = True
        return render_template("index.html", craving = ingredient, len = len(recipes), recipes = recipes, images = images, links = links, logged_in = logged_in)

@app.route('/save', methods = ['POST'])
def save():
    saved = mongo.db.saved
    username = session["username"]

    saved_type = "restaurants"
    if request.form["submit"] == "Save Recipe(s)":
        saved_type = "recipes"

    saved_items = list(saved.find({"username":username}))[0][saved_type]
    print(saved_items)

    print(request.form)
    for i in range(0,9):
        if "choice"+str(i) in request.form:
            current_item = request.form["choice"+str(i)].split("`")
            current_dic = {saved_type:current_item[0],"link":current_item[1],"image":current_item[2]}
            if current_dic not in saved_items:
                saved_items.append(current_dic)

    saved.update_one({"username":username},{"$set":{saved_type:saved_items}})
    return redirect("/saved")

@app.route('/delete', methods = ['POST'])
def delete():
    saved = mongo.db.saved
    username = session["username"]

    saved_type = "restaurants"
    if request.form["submit"] == "Delete Recipe(s)":
        saved_type = "recipes"

    saved_items = list(saved.find({"username":username}))[0][saved_type]
    print(saved_items)

    print(request.form)
    for i in range(0,len(saved_items)):
        if "choice"+str(i) in request.form:
            current_item = request.form["choice"+str(i)].split("`")
            current_dic = {saved_type:current_item[0],"link":current_item[1],"image":current_item[2]}
            saved_items.remove(current_dic)

    saved.update_one({"username":username},{"$set":{saved_type:saved_items}})
    return redirect("/saved")

@app.route('/saved', methods = ['GET','POST'])
def saved():
    if "username" not in session:
        return redirect("/")
    saved = mongo.db.saved
    username = session["username"]
    saved_recipes = list(saved.find({"username":username}))[0]["recipes"]
    saved_restaurants = list(saved.find({"username":username}))[0]["restaurants"]
    print(saved_restaurants)
    print("\n\n\n\n\n")
    print(saved_recipes)
    return render_template("saved.html", restaurants =saved_restaurants, recipes = saved_recipes, len_restaurants = len(saved_restaurants), len_recipes = len(saved_recipes))