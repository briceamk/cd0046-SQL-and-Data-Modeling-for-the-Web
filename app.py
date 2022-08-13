# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, jsonify, flash, redirect, url_for
from flask_moment import Moment

from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from forms import *
from models import *
import os

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)

moment = Moment(app)

app.config.from_object('config')

setup_db(app)

migrate = Migrate(app, db)





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
    venues = Venue.get_venues()
    shows = Show.get_all_upcomming_show_by_venues(venues)
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
    keyword = request.form.get('search_term', '')
    venues = Venue.search_venue_by_keyword(keyword)
    response = {
        'count': len(venues),
        'data': list(map(
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
    venue = Venue.get_venue(venue_id)
    venue.genres = Venue.convert_genre_object_to_array(venue.genres)
    column = ['show', 'artist_id', 'artist_name', 'artist_image_link', 'start_time']
    rows = Show.get_show_by_venue_id(venue_id)
    shows = []
    if rows:
        for row in rows:
            shows.append(dict(zip(column, row)))
        upcoming_shows = Show.get_upcomming_shows(shows)
        past_shows = Show.get_past_shows(shows)
        data = {
            **dict(vars(venue)),
            'upcoming_shows': upcoming_shows,
            'past_shows': past_shows,
            'upcoming_shows_count': len(upcoming_shows),
            'past_shows_count': len(past_shows)
        }
    else:
        data = dict(vars(venue))
    data.update({'genres': Venue.convert_genre_name_to_label(data.get('genres'))})
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm()
    if not form.validate_on_submit():
        return render_template('forms/new_venue.html', form=form)
    try:
        form_data = request.form.to_dict(flat=False)
        venue_dict = {key: form_data[key][0] if len(form_data[key]) <= 1 else form_data[key] for key in form_data}
        print(str(venue_dict))
        # convert string value to boolean
        if venue_dict.get('seeking_talent') == 'y':
            venue_dict.update({'seeking_talent': True})
        else:
            venue_dict.update({'seeking_talent': False})
        # converting label enum to name enum
        if isinstance(venue_dict.get('genres'), str):
            venue_dict.update({'genres': Venue.convert_genre_label_to_name([venue_dict.get('genres')])})
        else:
            venue_dict.update({'genres': Venue.convert_genre_label_to_name(venue_dict.get('genres'))})
        venue = Venue(**venue_dict)
        venue.insert()
        #on successful db insert, flash success
        flash('Venue ' + venue.name + ' was successfully listed!')
    except Exception as e:
        print(e)
        flash('An error occurred. Venue with name ' + request.form.get('name') + ' could not be saved.')
        # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        venue = Venue.get_venue(venue_id)
        venue.delete()
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
    data = Artist.get_artists()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    keyword = request.form.get('search_term', '')
    artists = Artist.search_artist_by_keyword(keyword)
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
    artist = Artist.get_artist(artist_id)
    artist.genres = Artist.convert_genre_object_to_array(artist.genres)
    column = ['show', 'venue_id', 'venue_name', 'venue_image_link', 'start_time']
    rows = Show.get_show_by_artist_id(artist_id)
    shows = []
    if rows:
        for row in rows:
            shows.append(dict(zip(column, row)))
        upcoming_shows = Show.get_upcomming_shows(shows)
        past_shows = Show.get_past_shows(shows)
        data = {
            **dict(vars(artist)),
            'upcoming_shows': upcoming_shows,
            'past_shows': past_shows,
            'upcoming_shows_count': len(upcoming_shows),
            'past_shows_count': len(past_shows)
        }
    else:
        data = dict(vars(artist))
    data.update({'genres': Artist.convert_genre_name_to_label(data.get('genres'))})
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.get_artist(artist_id)
    form.process(obj=artist)
    form.genres.data = Artist.convert_genre_name_to_label(Artist.convert_genre_object_to_array(artist.genres))
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm()
    if not form.validate_on_submit():
        artist = Artist.get_artist(artist_id)
        return render_template('forms/edit_artist.html', form=form, artist=artist)
    form_data = request.form.to_dict(flat=False)
    artist_dict = {key: form_data[key][0] if len(form_data[key]) <= 1 else form_data[key] for key in form_data}
    artist = Artist.get_artist(artist_id)
    for key, value in artist_dict.items():
        if hasattr(artist, key) and value is not None:
            if key == 'seeking_venue':
                value = True if value == 'y' else False
            if key == 'genres':
                if isinstance(value, str):
                    value = Artist.convert_genre_label_to_name([value])
                else:
                    value = Artist.convert_genre_label_to_name(value)
            setattr(artist, key, value)
    artist.update()
    db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.get_venue(venue_id)
    form.process(obj=venue)
    form.genres.data = Venue.convert_genre_name_to_label(Venue.convert_genre_object_to_array(venue.genres))
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm()
    if not form.validate_on_submit():
        venue = Venue.get_venue(venue_id)
        return render_template('forms/edit_venue.html', form=form, venue=venue)
    form_data = request.form.to_dict(flat=False)
    venue_dict = {key: form_data[key][0] if len(form_data[key]) <= 1 else form_data[key] for key in form_data}
    venue = Venue.get_venue(venue_id)
    for key, value in venue_dict.items():
        if hasattr(venue, key):
            if key == 'seeking_talent':
                value = True if value == 'y' else False
            if key == 'genres':
                if isinstance(value, str):
                    value = Artist.convert_genre_label_to_name([value])
                else:
                    value = Artist.convert_genre_label_to_name(value)
            setattr(venue, key, value)
    venue.update()
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
    form = ArtistForm()
    if not form.validate_on_submit():
        return render_template('forms/new_artist.html', form=form)
    try:
        form_data = request.form.to_dict(flat=False)
        artist_dict = {key: form_data[key][0] if len(form_data[key]) <= 1 else form_data[key] for key in form_data}
        # Convert string to boolean
        if artist_dict.get('seeking_venue') == 'y':
            artist_dict.update({'seeking_venue': True})
        else:
            artist_dict.update({'seeking_venue': False})
        # converting label enum to name enum
            # converting label enum to name enum
            if isinstance(artist_dict.get('genres'), str):
                artist_dict.update({'genres': Venue.convert_genre_label_to_name([artist_dict.get('genres')])})
            else:
                artist_dict.update({'genres': Venue.convert_genre_label_to_name(artist_dict.get('genres'))})
        artist = Artist(**artist_dict)
        artist.insert()
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
    rows = Show.get_shows()
    data = []
    for row in rows:
        data.append(dict(zip(colmuns, row)))
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm()
    if not form.validate_on_submit():
        return render_template('forms/new_show.html', form=form)
    try:
        form_data = request.form.to_dict(flat=True)
        show_dict = {key: form_data[key][0] if len(form_data[key]) <= 1 else form_data[key] for key in form_data}
        show = Show(**show_dict)
        show.insert()
        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except Exception as e:
        print(e)
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/shows/search', methods=['POST'])
def search_shows():
    keyword = request.form.get('search_term', '')
    shows = Show.search_show_by_keyword(keyword)
    response = {
        "count": len(shows),
        "data": list(map(lambda show: {
            'id': show.id,
            'venue_id': show.venue_id,
            'venue_name': Venue.get_venue(show.venue_id).name,
            'artist_id': show.artist_id,
            'artist_name': Artist.get_artist(show.artist_id).name,
            'artist_image_link': Artist.get_artist(show.artist_id).image_link,
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
