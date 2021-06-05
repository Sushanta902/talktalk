import os
import tkinter
import re
import io
from tkinter import messagebox
from itertools import islice
from werkzeug.utils import secure_filename
from flask import Response
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session ,url_for
from flask_socketio import SocketIO, join_room, leave_room ,send ,emit
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime



from helpers import apology, login_required

# Configure application
app = Flask(__name__)
#configure flask-socketio
socketio=SocketIO(app)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///data.db")


@app.route("/")
@login_required
def home():


    return redirect("/home")

@app.route("/home")
@login_required
def index():


    pic = db.execute("SELECT pp FROM users WHERE id = :user_id",user_id=session["user_id"])[0]["pp"]
    user = db.execute("SELECT id FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["id"]
    with open('static/{}.jpg'.format(user), 'wb') as f:
        f.write(pic)
    

    return render_template("index.html",image = user)



@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Assign inputs to variables
        input_username = request.form.get("username")
        input_password = request.form.get("password")

        # Ensure username was submitted
        if not input_username:
            return render_template("login.html",messager = 1)



        # Ensure password was submitted
        elif not input_password:
             return render_template("login.html",messager = 2)

        # Query database for username
        username = db.execute("SELECT * FROM users WHERE username = :username",
                              username=input_username)

        # Ensure username exists and password is correct
        if len(username) != 1 or not check_password_hash(username[0]["hash"], input_password):
            return render_template("login.html",messager = 3)

        # Remember which user has logged in
        session["user_id"] = username[0]["id"]



        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/feedback",methods=["GET", "POST"])
@login_required
def support():
    if request.method == "POST":

        # Assign inputs to variables
        input_username = db.execute("SELECT username FROM users WHERE id = :user_id",
                             user_id=session["user_id"])[0]["username"]
        commententry = request.form.get("comment")
        now = datetime.now()
        formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')
        

        comment = db.execute("INSERT INTO comment (username, comment,id, datetime) VALUES (:username, :commententry, :userid, :datentime)",
                                  username=input_username,
                                  commententry = commententry,
                                  userid = session["user_id"],
                                  datentime = formatted_date)

        user = db.execute("SELECT id FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["id"]

        return render_template("support.html",image = user)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
         user = db.execute("SELECT id FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["id"]
         return render_template("support.html",image = user)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Assign inputs to variables
        input_username = request.form.get("username")
        input_password = request.form.get("password")
        input_confirmation = request.form.get("confirmation")
        pic = request.files['pic']

        if not pic:
            return "no pic"

        filename = secure_filename(pic.filename)



        # Ensure username was submitted
        if not input_username:
            return render_template("register.html",messager = 1)

        # Ensure password was submitted
        elif not input_password:
            return render_template("register.html",messager = 2)

        # Ensure passwsord confirmation was submitted
        elif not input_confirmation:
            return render_template("register.html",messager = 4)

        elif not input_password == input_confirmation:
            return render_template("register.html",messager = 3)

        # Query database for username
        username = db.execute("SELECT username FROM users WHERE username = :username",
                              username=input_username)

        # Ensure username is not already taken
        if len(username) == 1:
            return render_template("register.html",messager = 5)

        # Query database to insert new user
        else:
            new_user = db.execute("INSERT INTO users (username, hash ,pp ,filename) VALUES (:username, :password , :pp, :filename)",
                                  username=input_username,
                                  password=generate_password_hash(input_password, method="pbkdf2:sha256", salt_length=8),
                                  pp = pic.read(),
                                  filename = filename)

            if new_user:
                # Keep newly registered user logged in
                session["user_id"] = new_user

            # Flash info for the user
            flash(f"Registered as {input_username}")

            # Redirect user to homepage
            return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")



@app.route("/comment", methods=["GET", "POST"])
@login_required
def display():
    b = session["user_id"]
    a = db.execute("select * from comment ORDER BY datetime DESC")
    con = db.execute("select count(username) as counter from comment")[0]["counter"]
    user = db.execute("SELECT id FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["id"]


    return render_template("display.html",b=b,a=a,con=con,image = user)



@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():

   sn = request.form.get("sn")
   check_id = request.form.get("check_id")


   try:
    user = db.execute("SELECT id FROM comment WHERE id = :user_id", user_id=session["user_id"])[0]["id"]
   except:
        return render_template("other.html")


   userid = str(user)
   if userid == check_id:
        db.execute("delete from comment where sn = :syn",syn=sn)

        return redirect("/comment")

   else:
        return render_template("other.html") 



@app.route("/update", methods=["GET", "POST"])
@login_required
def update():

    sn = request.form.get("sn")
    check_id = request.form.get("check_id")
    comment = request.form.get("comment")
    try:
    
        user = db.execute("SELECT id FROM comment WHERE id = :user_id", user_id=session["user_id"])[0]["id"]
    except:
        return render_template("other.html")




    userid = str(user)
    if not userid == check_id:
        return render_template("other.html")


    if not comment:

        return 'blank comment<a href="/comment"><br>return</a>'




    user = db.execute("SELECT id FROM comment WHERE id = :user_id", user_id=session["user_id"])[0]["id"]


    userid = str(user)
    if userid == check_id:
        db.execute("UPDATE comment set comment=:com where sn = :syn",syn=sn,com= comment)

        return redirect("/comment")

    else:
        return render_template("other.html") 
@app.route("/join", methods=["GET", "POST"])
@login_required
def join():
    if request.method == "POST":

        # Assign inputs to variables
        username = db.execute("SELECT username FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["username"]
        room = request.form.get('jgroup')
        input_id = db.execute("SELECT id FROM users WHERE id = :user_id",
                             user_id=session["user_id"])[0]["id"]
        jgroup = request.form.get("jgroup")
        user = db.execute("SELECT id FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["id"]

        code = db.execute("SELECT code FROM room WHERE groupname = :group", group=jgroup)
        if len(code) == 1 :
            a = code[0]['code'].split()
            cast = 0
            for i in a:
                if int(i) == input_id:
                    cast += 1

            if cast == 1 or cast > 1:
                return render_template('chat.html', username=username, room=room,image=user)
            else:
                broadcast = 2
        else:
            broadcast = 3
        return render_template("join.html",image = user,broadcast = broadcast)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        
        user = db.execute("SELECT id FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["id"]
        return render_template("join.html",image = user)

   
@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":

        # Assign inputs to variables
        broadcast = 0
        input_id = db.execute("SELECT id FROM users WHERE id = :user_id",
                             user_id=session["user_id"])[0]["id"]
        gname = request.form.get("cgroup")
        ids = request.form.get("a_id")
        group = db.execute("SELECT groupname FROM room WHERE groupname = :user_id", user_id=gname)
        ygroup = db.execute("SELECT groupname FROM room WHERE id = :user_id", user_id=session["user_id"])
        code = db.execute("SELECT code FROM room WHERE id = :ids", ids=session["user_id"])
       
        if len(group)==1:
            broadcast = 1
        else:
            
            comment = db.execute("INSERT INTO room (id,groupname,code) VALUES (:id, :gname, :code)",
                                  id=session["user_id"],
                                  gname= gname,
                                  code= ids )
        user = db.execute("SELECT id FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["id"]
        return render_template("create.html",image = user,broadcast=broadcast,ygroup=ygroup,code=code,p=len(ygroup))

    
    else:
        code = db.execute("SELECT code FROM room WHERE id = :ids", ids=session["user_id"])
        ygroup = db.execute("SELECT groupname FROM room WHERE id = :user_id", user_id=session["user_id"])
        user = db.execute("SELECT id FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["id"]
        print(code)
        return render_template("create.html",image = user,ygroup=ygroup,code=code,p=len(ygroup))




@app.route("/deletecode", methods=["GET", "POST"])
@login_required
def deletecode():
    group = request.form.get("dcode")

    db.execute("DELETE FROM room WHERE groupname = :syn",syn=group)     
    return redirect("/create") 

@app.route("/editcode", methods=["GET", "POST"])
@login_required
def editcode():
    group = request.form.get("egroup")
    editcode = request.form.get("ecode")

    db.execute("UPDATE room set code=:com where groupname = :syn",syn=group,com= editcode)     
    return redirect("/create") 
    
@app.route("/detail", methods=["GET", "POST"])
@login_required
def detail():
    pic = db.execute("SELECT pp FROM users WHERE id = :user_id",user_id=session["user_id"])[0]["pp"]
    name = db.execute("SELECT username FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["username"]
    user = db.execute("SELECT id FROM users WHERE id = :user_id", user_id=session["user_id"])[0]["id"]
    with open('static/{}.jpg'.format(user), 'wb') as f:
        f.write(pic)
    

    return render_template("detail.html",image = user,pic=pic,username= name)

@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info("{} has sent ther message {}: {}".format(data['username'],
                                                                    data['room'],
                                                                    data['message']))
    socketio.emit('receive_message', data, room=data['room'])


@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info("{} has joined the room {}".format(data['username'], data['room']))
    join_room(data['room'])
    socketio.emit('join_room_announcement', data, room=data['room'])


@socketio.on('leave_room')
def handle_leave_room_event(data):
    app.logger.info("{} has left the room {}".format(data['username'], data['room']))
    leave_room(data['room'])
    socketio.emit('leave_room_announcement', data, room=data['room'])



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return render_template("error.html",e = e)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

if __name__ == '__main__':
    socketio.run(app)