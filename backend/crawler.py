from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from backend.auth import login_required
from backend.db import get_db

from instagrapi import Client
from instagrapi.mixins.challenge import ChallengeChoice
import pandas as pd
import time 
import re

bp = Blueprint("crawler", __name__)


## MainPage
@bp.route("/crawler")
def index():
    db = get_db()
    ig_accs = db.execute(
        "SELECT i.id, i.username, i.password, i.user_id"
        " FROM ig_clone_account i JOIN user u ON i.user_id = u.id"
    ).fetchall()

    return render_template("crawler/index.html", ig_accs=ig_accs)


###----- IG Account --------##
## Add an IG Account
@bp.route("/crawler/add_ig", methods=("GET", "POST"))
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
            return redirect(url_for("crawler.index"))

    return render_template("crawler/add_ig.html")


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
@bp.route("/crawler/<int:id>/update", methods=("GET", "POST"))
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
            return redirect(url_for("crawler.index"))

    return render_template("crawler/update.html", ig_acc=ig_acc)


## Deleting an Account
@bp.route("/<int:id>/delete", methods=("POST",))
@login_required
def delete(id):
    get_ig_accs(id)
    db = get_db()
    db.execute("DELETE FROM ig_clone_account WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for("crawler.index"))


###----- IG Crawler --------##
 
        
@bp.route("/crawler/<int:id>/run", methods=("GET", "POST"))
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
    return render_template("crawler/run.html")
