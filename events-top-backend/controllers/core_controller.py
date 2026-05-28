import os

from flask import Blueprint, current_app, send_from_directory


core_controller = Blueprint("core_controller", __name__)


@core_controller.route("/")
def home():
    return "Backend Events-TOP active"


@core_controller.route("/assets/<path:filename>")
def serve_asset(filename):
    assets_dir = current_app.config["ASSETS_DIR"]
    return send_from_directory(assets_dir, filename)
