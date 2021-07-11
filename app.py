from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, current_user, logout_user, login_required

from passlib.hash import pbkdf2_sha256
from datetime import datetime

import os, math, random

from forms import *
from models import *
from mailing import *

app = Flask(__name__)

app.secret_key = "\xce\xd6\xb9\x89\xe4|\x01\xc0\x8e\xf5E\x8f\x94F\xdd\xa3\xe4\x8c^W\xfe\xef\x86Y/\x14\xfe\xf4\x9d\xc6" #os.environ.get('SECRET')

app.config['SQLALCHEMY_DATABASE_URI'] = "postgres://sxvryweiceigtz:838f3b7fe64bab13c53e87e8ab58174b1760cb3722d0dccb166cbe772fad59ef@ec2-34-195-143-54.compute-1.amazonaws.com:5432/dd0aoprd5r1b8p" #os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

"""psql --host=vhackathon.postgres.database.azure.com --port=5432 --username=prajwaldubey@vhackathon --dbname=vhackathon"""

EMAIL_ADDRESS = "prajwal.dubey@vit.edu.in" #os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = "Vidyalankar@1234" #os.environ.get('EMAIL_PASSWORD')

db = SQLAlchemy(app)

login = LoginManager(app)
login.init_app(app)

@app.errorhandler(404) 
def not_found(e): 

    return "<h1>404 Page not found</h1>"

@login.user_loader
def load_user(id):
    
    return User.query.get(int(id))

@app.route("/", methods = ['GET', 'POST'])
def main():

    signup = SignUp()

    return render_template("signup.html", form = signup)

@app.route("/signup", methods = ['GET', 'POST'])
def signup():

    signup = SignUp()

    if signup.validate_on_submit():
        
        email = signup.email.data
        username = signup.username.data
        password = signup.password.data
        position = signup.position.data

        branch = signup.branch.data
        college_name = signup.college_name.data

        hashed_password = pbkdf2_sha256.hash(password)

        user = User(email = email, username = username, password = hashed_password, position = position, branch = branch, college_name = college_name)
        db.session.add(user)
        db.session.commit() 

        flash("Registered Successfully!!", 'success')

        # return "{} {} {} {}".format(email, username, password, position)
        return redirect(url_for('login'))

    return render_template('signup.html', form = signup)

@app.route("/login", methods = ['GET', 'POST'])
def login():

    login = LogIn()

    if login.validate_on_submit():

        user = login.username.data

        user_object = User.query.filter_by(username = user).first()
        login_user(user_object)

        flash("Login Successfull!!", 'success')
        return redirect(url_for('home'))

    return render_template("login.html", form = login)


@app.route("/forgotpassword", methods = ["GET", "POST"])
def forgotpassword():

    forgot_password = ForgetPassword()
    login = LogIn()

    if forgot_password.validate_on_submit():

        email = forgot_password.email.data
        TO = email
        
        user_email = User.query.filter_by(email = email).first()
        if (user_email):

            user = User.query.filter_by(email = email).first()

            username = user.username

            string = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
            password = "" 
            length = len(string) 
            for i in range(10):  
                password += string[math.floor(random.random() * length)] 

            hashed_password = pbkdf2_sha256.hash(password)

            db.session.query(User).filter(User.email == email).update({User.password: hashed_password}, synchronize_session=False)
            db.session.commit()

            send_mail_password_forgot(TO, EMAIL_ADDRESS, EMAIL_PASSWORD, username, password)

            flash("Temporary Password has been sent to your registered email", "success")

            return render_template("login.html", form = login)
        else:
            flash("This email is not registered", "danger")
            return render_template("forgotpassword.html", form = forgot_password)

    return render_template("forgotpassword.html", form = forgot_password)


@app.route("/logout", methods = ['GET', 'POST'])
def logout():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    logout_user()
    flash("Logged out successfully!!", 'success')

    login = LogIn()

    return render_template("login.html", form = login)

##########################################################################################

##### PROJECTS

@app.route("/projects", methods = ['GET', 'POST'])
#@login_required
def projects():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    add_posts = AddProjectPost()

    userid = current_user.get_id()
    user = User.query.filter_by(id = userid).first()
    user_name = user.username
    status = "1"

    users = User.query.all()

    posts = AddProject.query.all()
    comments = ProjectComments.query.all()

    return render_template("projects.html", users = users, username = user_name, add_project_form = add_posts, status = status, posts = posts[::-1], comments = comments)

##### ADD PROJECTS  

@app.route("/addproject", methods = ["POST"])
def addproject():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    add_posts = AddProjectPost()

    if add_posts.validate_on_submit():

        title = add_posts.title.data
        description = add_posts.description.data
        link = add_posts.link.data

        now = datetime.now()

        date = str(now.strftime("%d/%m/%Y"))
        time = str(now.strftime("%H:%M"))

        date_time = "{} {}".format(date, time)

        userid = current_user.get_id()
        user = User.query.filter_by(id = userid).first()
        username = user.username

        post = AddProject(title = title, description = description, link = link, date_time = date_time, userid = userid, username = username)
        db.session.add(post)
        db.session.commit() 

        # break

        add_posts = AddProjectPost()

        userid = current_user.get_id()
        user = User.query.filter_by(id = userid).first()
        user_name = user.username
        status = "1"

        posts = AddProject.query.all()
        comments = ProjectComments.query.all()

        return render_template("projects.html", username = user_name, add_project_form = add_posts, status = status, posts = posts[::-1], comments = comments)

####### ADD PROJECT COMMENTS

@app.route("/addprojectcomments", methods = ["GET", "POST"])
def addprojectcomments():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":

        comment = request.form["comment"]
        project_id = request.form["project"]

        now = datetime.now()

        date = str(now.strftime("%d/%m/%Y"))
        time = str(now.strftime("%H:%M"))

        date_time = "{} {}".format(date, time)

        userid = current_user.get_id()
        user = User.query.filter_by(id = userid).first()
        username = user.username

        comm = ProjectComments(comment = comment, date_time = date_time, userid = userid, username = username, projectid = project_id)
        db.session.add(comm)
        db.session.commit() 

        return "DONE"

    return "addprojectcomments"

########### EDIT PROJECT POST

@app.route("/editpostproject", methods = ["GET", "POST"])
def editpostproject():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        link = request.form["link"]

        projectid = request.form["projectid"]

        db.session.query(AddProject).filter(AddProject.id == projectid).update({AddProject.title: title, AddProject.description: description, AddProject.link: link}, synchronize_session=False)
        db.session.commit()

        return "DONE"

    return "edited"

########### DELETE PROJECTS

@app.route("/deleteproject", methods = ["POST"])
def deleteproject():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":

        projectid = request.form["projectid"]

        db.session.query(AddProject).filter(AddProject.id == projectid).delete()
        db.session.commit()

        return "DONE"

    return "edited"

##########################################################################################

##### Academics

@app.route("/academics", methods = ['GET', 'POST'])
#@login_required
def academics():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    add_posts = AddAcademicsPost()

    userid = current_user.get_id()
    user = User.query.filter_by(id = userid).first()
    user_name = user.username
    status = "1"

    posts = AddAcademics.query.all()
    comments = AcademicComments.query.all()

    users = User.query.all()

    return render_template("academics.html", users = users, username = user_name, add_project_form = add_posts, status = status, posts = posts[::-1], comments = comments)

##### ADD PROJECTS  

@app.route("/addacademic", methods = ["POST"])
def addacademic():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    add_posts = AddAcademicsPost()

    if add_posts.validate_on_submit():

        title = add_posts.title.data
        description = add_posts.description.data
        link = add_posts.link.data

        now = datetime.now()

        date = str(now.strftime("%d/%m/%Y"))
        time = str(now.strftime("%H:%M"))

        date_time = "{} {}".format(date, time)

        userid = current_user.get_id()
        user = User.query.filter_by(id = userid).first()
        username = user.username

        post = AddAcademics(title = title, description = description, link = link, date_time = date_time, userid = userid, username = username)
        db.session.add(post)
        db.session.commit() 

        # break

        add_posts = AddAcademicsPost()

        userid = current_user.get_id()
        user = User.query.filter_by(id = userid).first()
        user_name = user.username
        status = "1"

        posts = AddAcademics.query.all()
        comments = AcademicComments.query.all()

        return render_template("academics.html", username = user_name, add_project_form = add_posts, status = status, posts = posts[::-1], comments = comments)

####### ADD PROJECT COMMENTS

@app.route("/addacademiccomments", methods = ["GET", "POST"])
def addacademiccomments():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":

        comment = request.form["comment"]
        project_id = request.form["project"]

        now = datetime.now()

        date = str(now.strftime("%d/%m/%Y"))
        time = str(now.strftime("%H:%M"))

        date_time = "{} {}".format(date, time)

        userid = current_user.get_id()
        user = User.query.filter_by(id = userid).first()
        username = user.username

        comm = AcademicComments(comment = comment, date_time = date_time, userid = userid, username = username, projectid = project_id)
        db.session.add(comm)
        db.session.commit() 

        return "DONE"

    return "addprojectcomments"

########### EDIT PROJECT POST

@app.route("/editpostacademic", methods = ["GET", "POST"])
def editpostacademic():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        link = request.form["link"]

        projectid = request.form["projectid"]

        db.session.query(AddAcademics).filter(AddAcademics.id == projectid).update({AddAcademics.title: title, AddAcademics.description: description, AddAcademics.link: link}, synchronize_session=False)
        db.session.commit()

        return "DONE"

    return "edited"

########### DELETE PROJECTS

@app.route("/deleteacademic", methods = ["POST"])
def deleteacademic():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":

        projectid = request.form["projectid"]

        db.session.query(AddAcademics).filter(AddAcademics.id == projectid).delete()
        db.session.commit()

        return "DONE"

    return "edited"


##########################################################################################

##### IDEAS

@app.route("/ideas", methods = ['GET', 'POST'])
#@login_required
def ideas():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    add_posts = AddIdeasPost()

    userid = current_user.get_id()
    user = User.query.filter_by(id = userid).first()
    user_name = user.username
    status = "1"

    posts = AddIdeas.query.all()
    comments = IdeasComments.query.all()

    users = User.query.all()

    return render_template("ideas.html", users = users, username = user_name, add_project_form = add_posts, status = status, posts = posts[::-1], comments = comments)

##### ADD Ideas  

@app.route("/addideas", methods = ["POST"])
def addideas():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    add_posts = AddIdeasPost()

    if add_posts.validate_on_submit():

        title = add_posts.title.data
        description = add_posts.description.data
        link = add_posts.link.data

        now = datetime.now()

        date = str(now.strftime("%d/%m/%Y"))
        time = str(now.strftime("%H:%M"))

        date_time = "{} {}".format(date, time)

        userid = current_user.get_id()
        user = User.query.filter_by(id = userid).first()
        username = user.username

        post = AddIdeas(title = title, description = description, link = link, date_time = date_time, userid = userid, username = username)
        db.session.add(post)
        db.session.commit() 

        # break

        add_posts = AddIdeasPost()

        userid = current_user.get_id()
        user = User.query.filter_by(id = userid).first()
        user_name = user.username
        status = "1"

        posts = AddIdeas.query.all()
        comments = IdeasComments.query.all()

        return render_template("ideas.html", username = user_name, add_project_form = add_posts, status = status, posts = posts[::-1], comments = comments)

####### ADD PROJECT COMMENTS

@app.route("/addideacomments", methods = ["GET", "POST"])
def addideacomments():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":

        comment = request.form["comment"]
        project_id = request.form["project"]

        now = datetime.now()

        date = str(now.strftime("%d/%m/%Y"))
        time = str(now.strftime("%H:%M"))

        date_time = "{} {}".format(date, time)

        userid = current_user.get_id()
        user = User.query.filter_by(id = userid).first()
        username = user.username

        comm = IdeasComments(comment = comment, date_time = date_time, userid = userid, username = username, projectid = project_id)
        db.session.add(comm)
        db.session.commit() 

        return "DONE"

    return "addprojectcomments"

########### EDIT PROJECT POST

@app.route("/editpostidea", methods = ["GET", "POST"])
def editpostidea():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":

        title = request.form["title"]
        description = request.form["description"]
        link = request.form["link"]

        projectid = request.form["projectid"]

        db.session.query(AddIdeas).filter(AddIdeas.id == projectid).update({AddIdeas.title: title, AddIdeas.description: description, AddIdeas.link: link}, synchronize_session=False)
        db.session.commit()

        return "DONE"

    return "edited"

########### DELETE PROJECTS

@app.route("/deleteidea", methods = ["POST"])
def deleteidea():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":

        projectid = request.form["projectid"]

        db.session.query(AddIdeas).filter(AddIdeas.id == projectid).delete()
        db.session.commit()

        return "DONE"

    return "edited"

@app.route("/filterproject", methods = ["GET", "POST"])
def filterproject():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":

        branch = request.form["branch"]
        college_name = request.form["college_name"]

        add_posts = AddProjectPost()

        userid = current_user.get_id()
        user = User.query.filter_by(id = userid).first()
        user_name = user.username
        status = "1"

        if(branch and college_name):
            filtered = User.query.filter_by(branch = branch, college_name = college_name).all()
        elif(college_name):
            filtered = User.query.filter_by(college_name = college_name).all()
        elif(branch):
            filtered = User.query.filter_by(branch = branch).all()
        else:
            filtered = 0

        posts = AddProject.query.filter_by().all()
        comments = ProjectComments.query.all()

        userid = current_user.get_id()
        user = User.query.filter_by(id = userid).first()
        user_name = user.username
        status = "1"

        add_posts = AddProjectPost()

        users = User.query.all()


        # if not current_user.is_authenticated:

        #     flash("Please Login!!", 'danger')
        #     status = "0"
        #     return render_template("projects.html", username = "username", add_project_form = add_posts, status = status, posts = posts, comments = comments)

        return render_template("filtered.html", users = users, filtered = filtered, posts = posts[::-1], comments = comments, username = user_name, add_project_form = add_posts, status = status)

@app.route("/filteracademics", methods = ["GET", "POST"])
def filteracademics():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":

        branch = request.form["branch"]
        college_name = request.form["college_name"]

        add_posts = AddAcademicsPost()

        userid = current_user.get_id()
        user = User.query.filter_by(id = userid).first()
        user_name = user.username
        status = "1"

        if(branch and college_name):
            filtered = User.query.filter_by(branch = branch, college_name = college_name).all()
        elif(college_name):
            filtered = User.query.filter_by(college_name = college_name).all()
        elif(branch):
            filtered = User.query.filter_by(branch = branch).all()
        else:
            filtered = 0

        posts = AddAcademics.query.filter_by().all()
        comments = AcademicComments.query.all()

        userid = current_user.get_id()
        user = User.query.filter_by(id = userid).first()
        user_name = user.username
        status = "1"

        add_posts = AddAcademicsPost()
        users = User.query.all()

        # if not current_user.is_authenticated:

        #     flash("Please Login!!", 'danger')
        #     status = "0"
        #     return render_template("projects.html", username = "username", add_project_form = add_posts, status = status, posts = posts, comments = comments)

        return render_template("filtered.html", users = users, filtered = filtered, posts = posts[::-1], comments = comments, username = user_name, add_project_form = add_posts, status = status)

@app.route("/filterideas", methods = ["GET", "POST"])
def filterideas():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":

        branch = request.form["branch"]
        college_name = request.form["college_name"]

        add_posts = AddIdeasPost()

        userid = current_user.get_id()
        user = User.query.filter_by(id = userid).first()
        user_name = user.username
        status = "1"

        if(branch and college_name):
            filtered = User.query.filter_by(branch = branch, college_name = college_name).all()
        elif(college_name):
            filtered = User.query.filter_by(college_name = college_name).all()
        elif(branch):
            filtered = User.query.filter_by(branch = branch).all()
        else:
            filtered = 0

        posts = AddIdeas.query.filter_by().all()
        comments = IdeasComments.query.all()

        userid = current_user.get_id()
        user = User.query.filter_by(id = userid).first()
        user_name = user.username
        status = "1"

        add_posts = AddIdeasPost()

        users = User.query.all()

        # if not current_user.is_authenticated:

        #     flash("Please Login!!", 'danger')
        #     status = "0"
        #     return render_template("projects.html", username = "username", add_project_form = add_posts, status = status, posts = posts, comments = comments)

        return render_template("filtered.html", users = users, filtered = filtered, posts = posts[::-1], comments = comments, username = user_name, add_project_form = add_posts, status = status)


@app.route("/collab", methods = ["GET", "POST"])
def collab():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":

        followed_id = request.form["followed_id"]
        followed_username = request.form["followed_username"]

        userid = current_user.get_id()
        user = User.query.filter_by(id = userid).first()
        user_name = user.username
        
        comm = Collab(follower_id = userid, follower_username = user_name, followed_id = followed_id, followed_username = followed_username, response = "R")
        db.session.add(comm)
        db.session.commit() 

        return "Requested"

    return " collab "

@app.route("/profile", methods = ["GET", "POST"])
def profile():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    add_posts = AddProjectPost()

    userid = current_user.get_id()
    user = User.query.filter_by(id = userid).first()
    user_name = user.username
    status = "1"

    posts = AddProject.query.all()
    comments = ProjectComments.query.all()

    postacademics = AddAcademics.query.all()
    postacademicscomment = AcademicComments.query.all()

    postideas = AddIdeas.query.all()
    postideascomments = IdeasComments.query.all()

    users = User.query.all()

    collab = Collab.query.all()

    return render_template("profile.html", users = users, postacademics = postacademics, postacademicscomment = postacademicscomment, postideas = postideas, postideascomments = postideascomments, username = user_name, add_project_form = add_posts, status = status, posts = posts[::-1], comments = comments, collab = collab, myid = userid)

@app.route("/accept", methods = ["GET", "POST"])
def accept():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":

        id = request.form["id"]
        
        db.session.query(Collab).filter(Collab.id == id).update({Collab.response: 'A'}, synchronize_session=False)
        db.session.commit()

        return "ACCEPTED"

    return "Afm"

@app.route("/reject", methods = ["GET", "POST"])
def reject():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":

        ids = request.form["id"]
        
        db.session.query(Collab).filter(Collab.id == ids).delete()
        db.session.commit()

        return "Delete"

    return "Afm"

@app.route("/home", methods = ["GET", "POST"])
def home():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    add_posts = AddProjectPost()

    userid = current_user.get_id()
    user = User.query.filter_by(id = userid).first()
    user_name = user.username
    status = "1"

    posts = AddProject.query.all()
    comments = ProjectComments.query.all()

    collab = Collab.query.all()

    return render_template("home.html", username = user_name, add_project_form = add_posts, status = status, posts = posts[::-1], comments = comments, collab = collab)

@app.route("/update", methods = ["GET", "POST"])
def update():

    if not current_user.is_authenticated:

        flash("Please Login!!", 'danger')
        return redirect(url_for('login'))

    if request.method == "POST":

        linkedin = request.form["linkedin"]
        github = request.form["github"]

        userid = current_user.get_id()

        db.session.query(User).filter(User.id == userid).update({User.linkedin: linkedin, User.github: github}, synchronize_session=False)
        db.session.commit()

        return redirect(url_for('profile'))

    return "Update Route"

if __name__ == "__main__":

    app.run(debug = True)
