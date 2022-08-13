from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SelectMultipleField, DateTimeField, BooleanField
from wtforms.validators import DataRequired, URL, Regexp, Optional
from enum import Enum
import re


class Genre(Enum):
    Alternative = 'Alternative'
    Blues = 'Blues'
    Classical = 'Classical'
    Country = 'Country'
    Electronic = 'Electronic'
    Folk = 'Folk'
    Funk = 'Funk'
    HipHop = 'Hip-Hop'
    HeavyMetal = 'Heavy Metal'
    Instrumental = 'Instrumental'
    Jazz = 'Jazz'
    MusicalTheatre = 'Musical Theatre'
    Pop = 'Pop'
    Punk = 'Punk'
    RB = 'R&B'
    Reggae = 'Reggae'
    RocknRoll = 'Rock n Roll'
    Soul = 'Soul'
    Swing = 'Swing'
    Other = 'Other'

    @classmethod
    def choices(cls):
        return [(choice, choice.value) for choice in cls]

    @classmethod
    def coerce(cls, item):
        return cls(item) if not isinstance(item, cls) else item

    def __str__(self):
        return str(self.value)


class State(Enum):
    AL = 'AL'
    AK = 'AK'
    AZ = 'AZ'
    AR = 'AR'
    CA = 'CA'
    CO = 'CO'
    CT = 'CT'
    DE = 'DE'
    DC = 'DC'
    FL = 'FL'
    GA = 'GA'
    HI = 'HI'
    ID = 'ID'
    IL = 'IL'
    IN = 'IN'
    IA = 'IA'
    KS = 'KS'
    KY = 'KY'
    LA = 'LA'
    ME = 'ME'
    MT = 'MT'
    NE = 'NE'
    NV = 'NV'
    NH = 'NH'
    NJ = 'NJ'
    NM = 'NM'
    NY = 'NY'
    NC = 'NC'
    ND = 'ND'
    OH = 'OH'
    OK = 'OK'
    OR = 'OR'
    MD = 'MD'
    MA = 'MA'
    MI = 'MI'
    MN = 'MN'
    MS = 'MS'
    MO = 'MO'
    PA = 'PA'
    RI = 'RI'
    SC = 'SC'
    SD = 'SD'
    TN = 'TN'
    TX = 'TX'
    UT = 'UT'
    VT = 'VT'
    VA = 'VA'
    WA = 'WA'
    WV = 'WV'
    WI = 'WI'
    WY = 'WY'

    @classmethod
    def choices(cls):
        return [(choice, choice.name) for choice in cls]

    @classmethod
    def coerce(cls, state):
        return cls(state) if not isinstance(state, cls) else state

    def __str__(self):
        return self.value


class ShowForm(FlaskForm):
    artist_id = StringField(
        'artist_id', validators=[
                                DataRequired(),
                                Regexp(
                                    regex='^[0-9]*$',
                                    message='must be a number')
        ]
    )
    venue_id = StringField(
        'venue_id', validators=[
                                DataRequired(),
                                Regexp(
                                    regex='^[0-9]*$',
                                    message='must be a number')
        ]
    )
    start_time = DateTimeField(
        'start_time',
        validators=[DataRequired()],
        default=datetime.today()
    )

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(ShowForm, self).__init__(*args, **kwargs)


class VenueForm(FlaskForm):
    name = StringField(
        'name', validators=[DataRequired()]
    )
    city = StringField(
        'city', validators=[DataRequired()]
    )
    state = SelectField(
        'state', validators=[DataRequired()],
        choices=State.choices(),
        coerce=State.coerce
    )
    address = StringField(
        'address', validators=[DataRequired()]
    )
    phone = StringField(
        'phone', validators=[
                    DataRequired(),
                    Regexp(regex='^[0-9]{3}-[0-9]{3}-[0-9]{4}$', message='Invalid phone number. must be xxx-xxx-xxxx')
        ]
    )
    image_link = StringField(
        'image_link', validators=[URL(message='Invalid link'), Optional()]
    )
    genres = SelectMultipleField(
        'genres', validators=[DataRequired()],
        choices=Genre.choices(),
        coerce=Genre.coerce
    )
    facebook_link = StringField(
        'facebook_link', validators=[URL(message='Invalid link'), Optional()]
    )
    website_link = StringField(
        'website_link', validators=[URL(message='Invalid link'), Optional()]
    )

    seeking_talent = BooleanField('seeking_talent')

    seeking_description = StringField(
        'seeking_description'
    )

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(VenueForm, self).__init__(*args, **kwargs)


class ArtistForm(FlaskForm):
    name = StringField(
        'name', validators=[DataRequired()]
    )
    city = StringField(
        'city', validators=[DataRequired()]
    )
    state = SelectField(
        'state', validators=[DataRequired()],
        choices=State.choices(),
        coerce=State.coerce
    )
    phone = StringField(
        'phone', validators=[
            DataRequired(),
            Regexp(regex='^[0-9]{3}-[0-9]{3}-[0-9]{4}$', message='Invalid phone number. must be xxx-xxx-xxxx')
        ]
    )
    image_link = StringField(
        'image_link', validators=[URL(message='Invalid link'), Optional()]
    )
    genres = SelectMultipleField(
        'genres', validators=[DataRequired()],
        choices=Genre.choices(),
        coerce=Genre.coerce
    )
    facebook_link = StringField(
        'facebook_link', validators=[URL(message='Invalid link'), Optional()]
    )
    website_link = StringField(
        'website_link', validators=[URL(message='Invalid link'), Optional()]
    )

    seeking_venue = BooleanField('seeking_venue')

    seeking_description = StringField(
        'seeking_description'
    )

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(ArtistForm, self).__init__(*args, **kwargs)
