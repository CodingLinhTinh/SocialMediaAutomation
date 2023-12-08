from flask import Blueprint, flash, g, redirect, render_template, request, url_for
from werkzeug.exceptions import abort

from backend.auth import login_required
from backend.db import get_db

from instagrapi import Client
from instagrapi.mixins.challenge import ChallengeChoice
import pandas as pd
import time 
import re

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