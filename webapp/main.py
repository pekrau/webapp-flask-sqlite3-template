"Web app template; main."

import flask
import jinja2.utils

import webapp.about
import webapp.config
import webapp.user
import webapp.site
# To be developed.
# import webapp.entity

import webapp.api.about
import webapp.api.root
import webapp.api.schema
import webapp.api.user
from webapp import constants
from webapp import utils

app = flask.Flask(__name__)

# Add URL map converters.
app.url_map.converters["identifier"] = utils.IdentifierConverter
app.url_map.converters["iuid"] = utils.IuidConverter

# Get the configuration, and initialize modules (database).
webapp.config.init(app)
utils.init(app)
webapp.user.init(app)
utils.mail.init_app(app)

@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context of Jinja2 templates."
    return dict(constants=constants,
                csrf_token=utils.csrf_token)

@app.before_request
def prepare():
    "Open the database connection; get the current user."
    flask.g.db = utils.get_db()
    flask.g.current_user = webapp.user.get_current_user()
    flask.g.am_admin = flask.g.current_user and \
                       flask.g.current_user["role"] == constants.ADMIN

app.after_request(utils.log_access)

@app.route("/")
def home():
    "Home page. Redirect to API root if JSON is accepted."
    if utils.accept_json():
        return flask.redirect(flask.url_for("api_root"))
    else:
        return flask.render_template("home.html")

@app.route("/debug")
@utils.admin_required
def debug():
    "Return some debug info for admin."
    result = [f"<h1>Debug  {constants.VERSION}</h2>"]
    result.append("<h2>headers</h2>")
    result.append("<table>")
    for key, value in sorted(flask.request.headers.items()):
        result.append(f"<tr><td>{key}</td><td>{value}</td></tr>")
    result.append("</table>")
    result.append("<h2>environ</h2>")
    result.append("<table>")
    for key, value in sorted(flask.request.environ.items()):
        result.append(f"<tr><td>{key}</td><td>{value}</td></tr>")
    result.append("</table>")
    return jinja2.utils.Markup("\n".join(result))

@app.route("/status")
def status():
    "Return JSON for the current status."
    return dict(status="ok")


# Set up the URL map.
app.register_blueprint(webapp.about.blueprint, url_prefix="/about")
app.register_blueprint(webapp.user.blueprint, url_prefix="/user")
app.register_blueprint(webapp.site.blueprint, url_prefix="/site")
# To be developed.
# app.register_blueprint(webapp.entity.blueprint, url_prefix="/entity")

app.register_blueprint(webapp.api.root.blueprint, url_prefix="/api")
app.register_blueprint(webapp.api.about.blueprint, url_prefix="/api/about")
app.register_blueprint(webapp.api.schema.blueprint, url_prefix="/api/schema")
app.register_blueprint(webapp.api.user.blueprint, url_prefix="/api/user")
# To be developed
# app.register_blueprint(webapp.api.entity.blueprint, url_prefix="/api/entity")


# This code is used only during development.
if __name__ == "__main__":
    app.run()
