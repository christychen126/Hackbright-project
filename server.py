from jinja2 import StrictUndefined, Template
from flask import Flask, render_template, redirect, request, flash, session, jsonify
from flask_debugtoolbar import DebugToolbarExtension
from flask_sqlalchemy import SQLAlchemy
from pprint import pprint
import json

# import db classes and tables from model file
from model import connect_to_db, db, Airport, User, Saved_trip, Flight, Lodging
# import my functions from functions file
import functions

import random



app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "ABC"

# undefined variable in Jinja2 raises an error
app.jinja_env.undefined = StrictUndefined
app.jinja_env.auto_reload = True



@app.route('/')
def index():
    """landing page"""

    if session.get("user_id"):
        return redirect('/home')
    else: 
        return render_template('index.html')


@app.route('/login', methods=["POST"])
def login():

    input_username = request.form.get("login-username")
    input_password = request.form.get("login-password")


    if User.query.filter(User.username==input_username).first():
        login_user = User.query.filter(User.username==input_username).one()
        if login_user.password == input_password:
            session["user_id"]=login_user.user_id
            return redirect('/home')

        else:
            flash("Oops, wrong password!")
            return redirect('/')
    else:
        flash("Username is not found. Do you want to register?")
        return redirect('/')



@app.route('/register', methods=["POST"])
def register():

    input_username = request.form.get("register-username")
    input_password = request.form.get("register-password") 
    input_user_airport = request.form.get("user-airport") #airport ---how to inforce this?

    if not User.query.filter(User.username==input_username).first():
        
        #instantiate user and add to db
        user = User(username=input_username,
                    password= input_password,
                    origin_airport_code=input_user_airport)
        db.session.add(user)
        db.session.commit()

        #add user in browser session
        session["user_id"]=User.query.filter(User.username==input_username).one().user_id
        flash("Welcom! Let's get you a vacation!!!")
        return redirect('/home')
    
    else: 
        flash("Username already exists. Pick another one or log in!")
        return redirect('/')



@app.route('/home')
def homepage():
    """user homepage"""

    if not session.get("user_id"):
        return redirect('/')

    print "this is user id in session **** ", session["user_id"]

    if Saved_trip.query.filter(Saved_trip.user_id==session["user_id"]).first():
        user_saved_trips = Saved_trip.query.filter(Saved_trip.user_id==session["user_id"]).all()

    else:  
        print "INSIDE ELSE" 
        user_saved_trips = None
        


    return render_template('homepage.html', saved_trip=user_saved_trips)


@app.route('/search_result', methods=["POST"])
def search_result():
    """send requests to APIs and display results"""


    departure_airport = User.query.filter(User.user_id==session["user_id"]).one().origin_airport_code
    

    airport_list = db.session.query(Airport.airport_code).all()
    

    airport_list.remove((departure_airport,))
    

    destination_airport = random.choice(airport_list)
    destination_city = db.session.query(Airport.city).filter(Airport.airport_code==destination_airport ).one()


    input_departure_date = request.form.get("input-departure-date")
    input_return_date =  request.form.get("input-return-date")

    
    #google static map

    flight_response_dict= functions.request_QPX(departure_airport, destination_airport, input_departure_date,input_return_date)
    flight_info_dict = functions.parse_QPX(flight_response_dict)

    lodging_response_dict = functions.request_Airbnb(destination_city, input_departure_date, input_return_date)
    lodging_info_dict = functions.parse_Airbnb(lodging_response_dict)


    return render_template('result_page.html', departure_airport=flight_info_dict["departure_airport"],
                        destination_airport=flight_info_dict["destination_airport"],
                        carrier=flight_info_dict["carrier"],
                        outbond_departure_time=flight_info_dict["outbond_departure_time"],
                        outbond_arrival_time=flight_info_dict["outbond_arrival_time"],
                        inbond_departure_time=flight_info_dict["inbond_departure_time"],
                        inbond_arrival_time=flight_info_dict["inbond_arrival_time"],
                        flight_price=flight_info_dict["flight_price"],
                        airbnb_id=lodging_info_dict["airbnb_id"],
                        address=lodging_info_dict["address"],
                        picture_url=lodging_info_dict["picture_url"],
                        price=lodging_info_dict["price"])




@app.route('/savetrip')
def save_trip():
    """save trip into db"""

    #take AJAX call and store the trip to db
    #not sure what to return 
    #change the button to saved



@app.route('/home/<int:trip_id>')
def saved_trip(trip_id):
    """dusplay saved trip with details"""

    #get trip info from db

    return render_template('saved_trip.html')



@app.route('/home/<int:trip_id>/delete', methods=["POST"])
def delete_trip(trip_id):
    """delete a saved trip"""

    #delete trip by id from db

    return redirect('/home')


@app.route('/logout')
def logout():
    """Log out user and flash confirmation message"""

    del session["user_id"]
    flash("You've been logged out successfully. Have a nice vacation!")

    return redirect('/')











################################################################################

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension

    # Do not debug for demo
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    #runs app
    app.run(host="0.0.0.0")
