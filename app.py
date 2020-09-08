from flask import Flask, render_template, redirect, request, session, send_from_directory, jsonify, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functions import gettitlefromyoutube, mainfunction
from threading import Thread
from os import path
from shutil import rmtree


app = Flask(__name__, template_folder='templates')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database/database.db'
app.config['SECRET_KEY'] = 'minstru_2835475_dimad'

db = SQLAlchemy(app)


usersong = db.Table('usersong',
                    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
                    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True)
                    )


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    songs = db.relationship('Song', secondary=usersong, backref=db.backref('owners', lazy='subquery'))


class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50))
    status = db.Column(db.String(30), default="downloading")
    url = db.Column(db.String(50), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow())
    users = db.relationship('User', secondary=usersong, backref=db.backref('mysongs', lazy='subquery'))


# TODO
@app.route("/", methods=["GET", "POST"])
def index():
    # TODO messages for added and errors
    # TODO refresh after finished downloading
    songs = None
    user = None
    if session.get('loggedIn'):
        user = User.query.filter_by(id=session.get('user')).first()
        if request.method == "POST":
            url = request.form['url']
            if "youtube.com/watch?v=" in url or "youtu.be/" in url:
                song = Song.query.filter_by(url=url).first()
                if song is None:
                    title = gettitlefromyoutube(url)
                    if title is not None:
                        song = Song(title=title, url=url)
                        db.session.add(song)
                        user.mysongs.append(song)
                        db.session.commit()
                        Thread(target=mainfunction, args=(song.id, song.url, db, app, )).start()

                else:
                    exists = False
                    for s in user.mysongs:
                        if s.url == song.url:
                            exists = True
                            break
                    if not exists:
                        user.mysongs.append(song)
                        db.session.commit()
        songs = user.mysongs
    return render_template("home.html", loggedIn=session.get('loggedIn'), user=user, songs=songs)


# TODO
@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get('loggedIn'):
        return redirect("/")
    if request.method == "POST":
        # TODO ADD HASH CHECK
        # TODO MAYBE ADD REMEMBER ME
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user is None:
            message = "username or password invalid"
            error = True
            return render_template("login.html", message=message, error=error)
        session['loggedIn'] = True
        session['user'] = user.id
        return redirect("/")
    else:
        return render_template("login.html")


# TODO
@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get('loggedIn'):
        return redirect("/")

    if request.method == "POST":
        # TODO: ADD VALIDATION
        # TODO: ADD PASSWORD HASHING
        # TODO: CHECK WHAT ERROR HAPPENED
        # TODO: ADD EMAIL VERIFICATION
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        passwordconfirmation = request.form['passwordconfirmation']
        if password != passwordconfirmation:
            message = "The password and confirmation don't match"
            error = True
            return render_template("register.html", message=message, error=error)
        new_user = User(username=username, password=password, email=email)
        try:
            db.session.add(new_user)
            db.session.commit()
        except:
            message = "there was an error creating a new account"
            error = True
            return render_template("register.html", message=message, error=error)
        message = "account created"
        error = False
        return render_template("register.html", message=message, error=error)
    else:
        return render_template("register.html")


# TODO
@app.route("/passreset", methods=["GET", "POST"])
def passreset():
    if request.method == "POST":
        # TODO
        message = "Please check your email for password reset link"
        error = False
        return render_template("passreset.html", message=message, error=error)
    else:
        if session.get('loggedIn'):
            return redirect("/")
        return render_template("passreset.html")


@app.route("/logout")
def logout():
    session['loggedIn'] = False
    session['user'] = None
    return redirect("/")


# TODO
@app.route("/delete/<int:song_id>")
def delete(song_id):
    # TODO: USE DELETE METHOD INSTEAD OF GET METHOD
    if not session.get('loggedIn'):
        return redirect("/")

    db.engine.execute("DELETE FROM usersong WHERE user_id={} AND song_id={}".format(session.get('user'), song_id))
    count = db.engine.execute("SELECT COUNT() FROM usersong WHERE song_id={}".format(song_id)).first()[0]
    if count == 0:
        db.engine.execute("DELETE FROM song WHERE id={}".format(song_id))
        try:
            rmtree(path.join(app.root_path, 'songs', str(song_id)))
        except:
            pass
    db.session.commit()
    return redirect("/")


@app.route("/download/<int:song_id>")
def download(song_id):
    count = db.engine.execute("SELECT COUNT() FROM usersong WHERE song_id={} AND user_id={}".format(song_id, session.get('user'))).first()[0]
    song = Song.query.filter_by(id=song_id).first()
    if count != 0 and song.status == "ready":
        return send_from_directory('songs', '{}/accompaniment.wav'.format(song_id))
    else:
        return redirect("/")


@app.route("/info/<int:song_id>")
def info(song_id):
    song = Song.query.filter_by(id=song_id).first()
    if song is not None:
        html = None
        if song.status == "ready":
            html = '''
                <a class="inline-block bg-gray-200 rounded-full px-3 py-1 text-sm font-semibold
                    text-gray-700 m-2 transform hover:scale-110 hover:bg-gray-400 transition transition-all 
                    duration-100" href="/download/{}"
                    >
                    <img src="{}" width="20">
                </a>
                 <a href="/delete/{}" class="text-red-600 font-bold hover:bg-red-600 hover:text-white 
                 rounded-full px-2 py-0 transition transition-all duration-100">X</a>
            '''.format(song_id, url_for('static', filename='images/download.svg'), song_id)
        return jsonify({'id': song_id, 'status': song.status, 'html': html})
    else:
        return jsonify({'id': song_id, 'status': 'invalid'})


if __name__ == "__main__":
    app.run(debug=True)
