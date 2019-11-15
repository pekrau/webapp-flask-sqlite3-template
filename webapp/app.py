"Web app template."

import flask

import webapp.about
import webapp.config
import webapp.user
import webapp.site

import webapp.api.about
import webapp.api.root
import webapp.api.schema
import webapp.api.user
from webapp import constants
from webapp import utils

app = flask.Flask(__name__)

# Add URL map converters.
app.url_map.converters['name'] = utils.NameConverter
app.url_map.converters['iuid'] = utils.IuidConverter

# Get the configuration.
webapp.config.init(app)

# Init the mail handler.
utils.mail.init_app(app)

# Add template filters.
app.add_template_filter(utils.thousands)

@app.context_processor
def setup_template_context():
    "Add useful stuff to the global context of Jinja2 templates."
    return dict(constants=constants,
                csrf_token=utils.csrf_token)

@app.before_first_request
def init_database():
    db = utils.get_db()
    logger = utils.get_logger()
    if db.put_design('logs', utils.LOGS_DESIGN_DOC):
        logger.info('Updated logs design document.')
    if db.put_design('users', webapp.user.USERS_DESIGN_DOC):
        logger.info('Updated users design document.')

@app.before_request
def prepare():
    "Open the database connection; get the current user."
    flask.g.dbserver = utils.get_dbserver()
    flask.g.db = utils.get_db(dbserver=flask.g.dbserver)
    flask.g.current_user = webapp.user.get_current_user()
    flask.g.is_admin = flask.g.current_user and \
                       flask.g.current_user['role'] == constants.ADMIN

app.after_request(utils.log_access)

@app.route('/')
def home():
    "Home page. Redirect to API root if JSON is accepted."
    if utils.accept_json():
        return flask.redirect(flask.url_for('api_root'))
    else:
        return flask.render_template('home.html')

# Set up the URL map.
app.register_blueprint(webapp.about.blueprint, url_prefix='/about')
app.register_blueprint(webapp.user.blueprint, url_prefix='/user')
app.register_blueprint(webapp.site.blueprint, url_prefix='/site')

app.register_blueprint(webapp.api.root.blueprint, url_prefix='/api')
app.register_blueprint(webapp.api.about.blueprint, url_prefix='/api/about')
app.register_blueprint(webapp.api.schema.blueprint, url_prefix='/api/schema')
app.register_blueprint(webapp.api.user.blueprint, url_prefix='/api/user')


# This code is used only during development.
if __name__ == '__main__':
    app.run()
