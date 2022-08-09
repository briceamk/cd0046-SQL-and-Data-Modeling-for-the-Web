# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, jsonify, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import os

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.Text())
    shows = db.relationship('Show', backref='Venue', lazy=True)


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.Text())
    shows = db.relationship('Show', backref='Artist', lazy=True)


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    start_time = db.Column(db.DateTime, nullable=False)


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    if isinstance(value, str):
        date = dateutil.parser.parse(value)
    else:
        date = value
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    venues = Venue.query.all()
    shows = Show.query.filter(Show.venue_id.in_([venue.id for venue in venues]),
                              Show.start_time >= datetime.now()).all()
    states = list(set(map(lambda venue: (venue.state, venue.city), venues))) or []
    data = []
    for state, city in states:
        city_venues = list(map(lambda venue: {
            'id': venue.id,
            'name': venue.name,
            'num_upcoming_shows': len(list(filter(lambda show: show.venue_id == venue.id, shows)))},
                               filter(lambda venue: venue.state == state, venues)))
        data.append({
            'city': city,
            'state': state,
            'venues': city_venues,

        })
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    venues = Venue.query.filter(Venue.name.ilike('%' + request.form.get('search_term', '') + '%')).all()
    response = {
        "count": len(venues),
        "data": list(map(
            lambda venue: {
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': 0
            }, venues))
    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    venue.genres = venue.genres.replace('{', '').replace('}', '').split(',')
    column = ['show', 'artist_id', 'artist_name', 'artist_image_link', 'start_time']
    rows = Show.query \
        .join(Artist, Artist.id == Show.artist_id) \
        .add_columns(Artist.id, Artist.name, Artist.image_link, Show.start_time) \
        .filter(Show.venue_id == venue.id).all()
    shows = []
    if rows:
        for row in rows:
            shows.append(dict(zip(column, row)))
        upcoming_shows = list(filter(lambda show: show.get('start_time') >= datetime.now(), shows))
        past_shows = list(filter(lambda show: show.get('start_time') < datetime.now(), shows))
        data = {
            **dict(vars(venue)),
            'upcoming_shows': upcoming_shows,
            'past_shows': past_shows,
            'upcoming_shows_count': len(upcoming_shows),
            'past_shows_count': len(past_shows)
        }
    else:
        data = dict(vars(venue))
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    try:
        form_data = request.form.to_dict(flat=False)
        venue_dict = {key: form_data[key][0] if len(form_data[key]) <= 1 else form_data[key] for key in form_data}
        # convert string value to boolean
        if venue_dict.get('seeking_talent') == 'y':
            venue_dict.update({'seeking_talent': True})
        else:
            venue_dict.update({'seeking_talent': False})
        venue = Venue(**venue_dict)
        db.session.add(venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + venue.name + ' was successfully listed!')
    except:
        flash('An error occurred. Venue with name' + request.form.get('name') + ' could not be saved.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        Venue.query.filter(Venue.id == venue_id).delete()
        db.session.commit()
        success = True
        code = 200
        flash('Venue with the id {} deleted successfully'.format(str(venue_id)))
    except:
        flash('Venue with the id {} can\'t be deleted'.format(str(venue_id)))
        success = False
        code = 400
    finally:
        db.session.close()
    return jsonify({'success': success}), code


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = Artist.query.with_entities(Artist.id, Artist.name).all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    artists = Artist.query.filter(Artist.name.ilike('%' + request.form.get('search_term', '') + '%')).all()
    response = {
        "count": len(artists),
        "data": list(map(lambda artist: {
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows': 0}, artists))
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    artist.genres = artist.genres.replace('{', '').replace('}', '').split(',')
    column = ['show', 'venue_id', 'venue_name', 'venue_image_link', 'start_time']
    rows = Show.query \
        .join(Venue, Venue.id == Show.venue_id) \
        .add_columns(Venue.id, Venue.name, Venue.image_link, Show.start_time) \
        .filter(Show.artist_id == artist.id).all()
    shows = []
    if rows:
        for row in rows:
            shows.append(dict(zip(column, row)))
        upcoming_shows = list(filter(lambda show: show.get('start_time') >= datetime.now(), shows))
        past_shows = list(filter(lambda show: show.get('start_time') < datetime.now(), shows))
        data = {
            **dict(vars(artist)),
            'upcoming_shows': upcoming_shows,
            'past_shows': past_shows,
            'upcoming_shows_count': len(upcoming_shows),
            'past_shows_count': len(past_shows)
        }
    else:
        data = dict(vars(artist))
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    form.process(obj=artist)
    form.genres.data = artist.genres.replace('{', '').replace('}', '').split(',')
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form_data = request.form.to_dict(flat=False)
    artist_dict = {key: form_data[key][0] if len(form_data[key]) <= 1 else form_data[key] for key in form_data}
    artist = Artist.query.get(artist_id)
    for key, value in artist_dict.items():
        if hasattr(artist, key) and value is not None:
            if key == 'seeking_venue':
                value = True if value == 'y' else False
            setattr(artist, key, value)
    db.session.commit()
    db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    form.process(obj=venue)
    form.genres.data = venue.genres.replace('{', '').replace('}', '').split(',')
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form_data = request.form.to_dict(flat=False)
    venue_dict = {key: form_data[key][0] if len(form_data[key]) <= 1 else form_data[key] for key in form_data}
    venue = Venue.query.get(venue_id)
    for key, value in venue_dict.items():
        if hasattr(venue, key) and value is not None:
            if key == 'seeking_talent':
                value = True if value == 'y' else False
            setattr(venue, key, value)
    db.session.commit()
    db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    try:
        form_data = request.form.to_dict(flat=False)
        artist_dict = {key: form_data[key][0] if len(form_data[key]) <= 1 else form_data[key] for key in form_data}
        # Convert string to boolean
        if artist_dict.get('seeking_venue') == 'y':
            artist_dict.update({'seeking_venue': True})
        else:
            artist_dict.update({'seeking_venue': False})
        artist = Artist(**artist_dict)
        db.session.add(artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + artist.name + ' was successfully listed!')
    except:
        flash('An error occurred. Artist with name ' + request.form.get('name') + ' could not be saved.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    colmuns = ['show', 'venue_id', 'venue_name', 'artist_id', 'artist_name', 'artist_image_link', 'start_time']
    rows = Show.query.join(Venue, Show.venue_id == Venue.id) \
        .add_columns(Show.venue_id, Venue.name) \
        .join(Artist, Show.artist_id == Artist.id) \
        .add_columns(Show.artist_id, Artist.name, Artist.image_link, Show.start_time) \
        .all()
    data = []
    for row in rows:
        data.append(dict(zip(colmuns, row)))
    print(str(data))
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    try:
        form_data = request.form.to_dict(flat=True)
        show_dict = {key: form_data[key][0] if len(form_data[key]) <= 1 else form_data[key] for key in form_data}
        show = Show(**show_dict)
        db.session.add(show)
        db.session.commit()
        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except:
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/shows/search', methods=['POST'])
def search_shows():
    shows = Show.query.filter(Show.id == request.form.get('search_term', '')).all()
    colmuns = ['show', 'venue_id', 'venue_name', 'artist_id', 'artist_name', 'artist_image_link', 'start_time']
    response = {
        "count": len(shows),
        "data": list(map(lambda show: {
            'id': show.id,
            'venue_id': show.venue_id,
            'venue_name': Venue.query.get(show.venue_id).name,
            'artist_id': show.artist_id,
            'artist_name': Artist.query.get(show.artist_id).name,
            'artist_image_link': Artist.query.get(show.artist_id).image_link,
            'start_time': show.start_time,
            'num_upcoming_shows': 0}, shows))
    }
    return render_template('pages/search_shows.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
'''
if __name__ == '__main__':
    app.run()
'''
# Or specify port manually:
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port)
