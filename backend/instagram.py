from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from backend.auth import login_required
from backend.db import get_db

from instagrapi import Client
from instagrapi.mixins.challenge import ChallengeChoice
import pandas as pd
import time 
import re
import os

from backend.classes.Automation import Automation

bp = Blueprint("instagram", __name__)


## MainPage
@bp.route("/")
def index():
    db = get_db()
    ig_accs = db.execute(
        "SELECT i.id, i.username, i.password, i.user_id"
        " FROM ig_clone_account i JOIN user u ON i.user_id = u.id"
    ).fetchall()

    return render_template("instagram/index.html", ig_accs=ig_accs)


###----- IG Account --------##
## Add an IG Account
@bp.route("/add_ig", methods=("GET", "POST"))
@login_required
def add_ig():
    if request.method == "POST":
        ig_username = request.form["ig_username"]
        ig_password = request.form["ig_password"]
        error = None

        if not ig_username:
            error = "ig_username is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "INSERT INTO IG_Clone_Account (username, password,user_id )"
                " VALUES (?, ?, ?)",
                (ig_username, ig_password, g.user["id"]),
            )
            db.commit()
            return redirect(url_for("instagram.index"))

    return render_template("instagram/add_ig.html")


def get_ig_accs(id, check_ig_acc=True):
    ig_acc = (
        get_db()
        .execute(
            "SELECT i.id, i.username, i.password, user_id"
            " FROM ig_clone_account i JOIN user u ON i.user_id = u.id"
            " WHERE i.id = ?",
            (id,),
        )
        .fetchone()
    )

    if ig_acc is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_ig_acc and ig_acc["user_id"] != g.user["id"]:
        abort(403)

    return ig_acc


## Updating an Account
@bp.route("/<int:id>/update", methods=("GET", "POST"))
@login_required
def update(id):
    ig_acc = get_ig_accs(id)

    if request.method == "POST":
        ig_username = request.form["ig_username"]
        ig_password = request.form["ig_password"]
        error = None

        if not ig_username:
            error = "ig_username is required."

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                "UPDATE ig_clone_account SET username = ?, password = ?"
                " WHERE id = ?",
                (ig_username, ig_password, id),
            )
            db.commit()
            return redirect(url_for("instagram.index"))

    return render_template("instagram/update.html", ig_acc=ig_acc)


## Deleting an Account
@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    get_ig_accs(id)
    db = get_db()
    db.execute("DELETE FROM ig_clone_account WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("instagram.index"))


###----- IG Crawler --------##    
@bp.route("/<int:id>/run", methods=("GET", "POST"))
@login_required
def run(id):
    client = Client()
    ig_acc = get_ig_accs(id)
    
    username            = None
    full_name           = None 
    biography           = None
    follower_count      = None
    email               = None
    phone               = None
    
    if request.method == "POST":
        try:
            client.login(str(ig_acc["username"]),  str(ig_acc["password"]))
            print("Logged In.")

            time.sleep(3)  
            
            keywords = str( request.form["keywords"] )
            
            error = None

            if not keywords:
                error = "keywords is required."

            if error is not None:
                flash(error)
            else:
                try:
                    data = client.hashtag_medias_top(keywords, amount=10)
                    time.sleep(3)  
                    
                    for d in data:
                        data            = d.dict()
                        try:
                            pk          = int( data["user"]["pk"] )
                        except TypeError:
                            print("Value cannot be converted to an integer.")
                            pass
                        username        = data['user']['username']
                        full_name       = data['user']['full_name']
                        biography       = data['caption_text']
                            
                        more_data       = client.user_info_by_username(username).dict()
                            
                        follower_count = more_data["follower_count"]

                        email           = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', biography)
                        phone           = re.findall(r'\b\d{10,11}\b', biography)
                        
                        ##----
                        sql_query = (
                            "SELECT c.id, c.user_id, c.username, c.full_name, c.phone, c.email "
                            "FROM crawler c JOIN user u ON c.user_id = u.id"
                        )

                        crawler_data = get_db().execute(sql_query).fetchall()
                        
                        print(crawler_data)
                            
                        ##----
                        if username not in crawler_data:
                            if follower_count > 0:
                                print("getUserFollowersData")
                                ids                 = client.user_followers(user_id=pk, amount= 50).keys()  
                                username            = None
                                full_name           = None 
                                biography           = None
                                follower_count      = None
                                email               = None
                                phone               = None
            
                                for id in ids:
                                    try:
                                        data = client.user_info(id).dict() 
                                        try:
                                            pk          = int( data["user"]["pk"] )
                                        except TypeError:
                                            print("Value cannot be converted to an integer.")
                                            pass
                                        username        = data['user']['username']
                                        full_name       = data['user']['full_name']
                                        biography       = data['caption_text']
                                        
                                        email           = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', biography)
                                        phone           = re.findall(r'\b\d{10,11}\b', biography)
                                    except Exception as e:
                                        pass 
                                    
                                    if email != None or phone != None:
                                        ## Add to db    
                                        db = get_db()
                                        db.execute(
                                            "INSERT INTO crawler (user_id, username,full_name,phone,email)"
                                            " VALUES (?, ?, ?, ?, ?)",
                                            (g.user["id"],username, full_name, phone, email),
                                        )
                                        db.commit()
                                        print(f"Added {username}") 
                            else:  
                                if email != None or phone != None:
                                    ## Add to db    
                                    db = get_db()
                                    db.execute(
                                        "INSERT INTO crawler (user_id, username,full_name,phone,email)"
                                        " VALUES (?, ?, ?, ?, ?)",
                                        (g.user["id"],username, full_name, phone, email),
                                    )
                                    db.commit() 
                                    print(f"Added {username}")   
                except Exception as e:
                    print(e)
                    pass  
            
        except Exception as e:
            print(e)
            pass    
    return render_template("instagram/run.html")

###----- IG Automation --------##   
@bp.route("/<int:id>/automate", methods=("GET", "POST"))
@login_required
def automate(id):
    client = Client()
    ig_acc = get_ig_accs(id)
    
    if request.method == "POST":
        try:
            form_type = request.form.get('form_type')

            if form_type == 'target_username':
                # Handle the first form
                ## IG login :v
                automation.clientLogin(str(ig_acc["username"]), str(ig_acc["password"]))

                print("Logged In.")
                target_username = str(request.form["target_username"])
                follow_followers = bool(request.form.get('follow_followers'))
                unfollow_followers = bool(request.form.get('unfollow_followers'))

                # Your logic for the first form
                
                if follow_followers and not unfollow_followers:
                    pass 
                
                if unfollow_followers and not follow_followers:
                    pass

            elif form_type == 'upload_photos':
                automation = Automation()
                ## IG login :v
                automation.clientLogin(str(ig_acc["username"]), str(ig_acc["password"]))
                print("Logged In.")
                time.sleep(5)
                
                # Handle the second form
                caption = str(request.form["caption"])
                custom_accessibility_caption = str(request.form["custom_accessibility_caption"])
                like_and_view_counts_disabled = bool(request.form.get('like_and_view_counts_disabled'))
                disable_comments = bool(request.form.get('disable_comments'))
                
                if 'image' in request.files:
                    image = request.files['image']

                    # Ensure the directory exists
                    upload_directory = './static/img/'
                    if not os.path.exists(upload_directory):
                        os.makedirs(upload_directory)

                    # Save the file to the specified directory
                    destination_path = os.path.join(upload_directory, image.filename)
                    
                    # Save the content of the uploaded file to the destination file
                    with open(destination_path, 'wb') as file:
                        file.write(image.read())
                    
                    automation.PhotoUpload(
                        path=destination_path,
                        caption=caption,
                        custom_accessibility_caption=custom_accessibility_caption,
                        like_and_view_counts_disabled= int( like_and_view_counts_disabled ),
                        disable_comments=int( disable_comments )
                    )
                    print("Uploaded.")
            else:
                # Handle other cases or show an error
                pass

        except Exception as e:
            print(e)
            pass

    return render_template("instagram/automation.html")  