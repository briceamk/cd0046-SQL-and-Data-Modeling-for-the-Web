from flask_sqlalchemy import SQLAlchemy
from forms import Genre
from datetime import datetime

db = SQLAlchemy()

'''
    Setup database
'''


def setup_db(app):
    db.app = app
    db.init_app(app)


# ---------------------------
# Models
# ---------------------------

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

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_venue(cls, venue_id):
        return Venue.query.get(venue_id)

    @classmethod
    def get_venues(cls):
        return Venue.query.all()

    @classmethod
    def search_venue_by_keyword(cls, keyword):
        return Venue.query.filter(Venue.name.ilike('%{}%'.format(keyword))).all()

    @classmethod
    def convert_genre_name_to_label(cls, genre_names):
        genres = []
        for genre in genre_names:
            genres.append(Genre[genre])
        return genres

    @classmethod
    def convert_genre_label_to_name(cls, genre_labels):
        genres = []
        for genre in genre_labels:
            genres.append(Genre.coerce(genre))
        return [genre.name for genre in genres]

    @classmethod
    def convert_genre_object_to_array(cls, genres):
        return genres.replace('{', '').replace('}', '').split(',')


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

    def insert(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        db.session.commit()

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def get_artist(cls, artist_id):
        return Artist.query.get(artist_id)

    @classmethod
    def get_artists(cls):
        return Artist.query.with_entities(Artist.id, Artist.name).all()

    @classmethod
    def search_artist_by_keyword(cls, keyword):
        return Artist.query.filter(Artist.name.ilike('%{}%'.format(keyword))).all()

    @classmethod
    def convert_genre_name_to_label(cls, genre_names):
        genres = []
        for genre in genre_names:
            genres.append(Genre[genre])
        return genres

    @classmethod
    def convert_genre_label_to_name(cls, genre_labels):
        genres = []
        for genre in genre_labels:
            genres.append(Genre.coerce(genre))
        return [genre.name for genre in genres]

    @classmethod
    def convert_genre_object_to_array(cls, genres):
        return genres.replace('{', '').replace('}', '').split(',')


class Show(db.Model):
    __tablename__ = 'Show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'))
    venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'))
    start_time = db.Column(db.DateTime, nullable=False)

    def insert(self):
        db.session.add(self)
        db.session.commit()

    @classmethod
    def get_shows(cls):
        return Show.query.join(Venue, Show.venue_id == Venue.id) \
            .add_columns(Show.venue_id, Venue.name) \
            .join(Artist, Show.artist_id == Artist.id) \
            .add_columns(Show.artist_id, Artist.name, Artist.image_link, Show.start_time) \
            .all()

    @classmethod
    def get_all_upcomming_show_by_venues(cls, venues):
        return Show.query.filter(Show.venue_id.in_([venue.id for venue in venues]),
                                 Show.start_time >= datetime.now()).all()

    @classmethod
    def get_show_by_venue_id(cls, venue_id):
        return Show.query \
            .join(Artist, Artist.id == Show.artist_id) \
            .add_columns(Artist.id, Artist.name, Artist.image_link, Show.start_time) \
            .filter(Show.venue_id == venue_id).all()

    @classmethod
    def get_show_by_artist_id(cls, artist_id):
        return Show.query \
            .join(Venue, Venue.id == Show.venue_id) \
            .add_columns(Venue.id, Venue.name, Venue.image_link, Show.start_time) \
            .filter(Show.artist_id == artist_id).all()

    @classmethod
    def get_upcomming_shows(cls, shows):
        return list(filter(lambda show: show.get('start_time') >= datetime.now(), shows))

    @classmethod
    def get_past_shows(cls, shows):
        return list(filter(lambda show: show.get('start_time') < datetime.now(), shows))

    @classmethod
    def search_show_by_keyword(cls, keyword):
        return Show.get_show_by_artist_or_venue_name(keyword)

    @classmethod
    def get_show_by_artist_or_venue_name(cls, keyword):
        if isinstance(keyword, str):
            shows = Show.query.join(Venue, Show.venue_id == Venue.id) \
                .join(Artist, Show.artist_id == Artist.id) \
                .filter((Venue.name.ilike('%' + keyword + '%') | Artist.name.ilike('%' + keyword + '%') | (Show.start_time == keyword)))\
                .all()
        elif isinstance(keyword, datetime):
            shows = Show.query.join(Venue, Show.venue_id == Venue.id) \
                .join(Artist, Show.artist_id == Artist.id) \
                .filter(Show.start_time == keyword) \
                .all()
        else:
            shows = []
        return shows
