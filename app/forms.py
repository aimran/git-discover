from flask.ext.wtf import Form
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from wtforms.fields.html5 import DateField
from wtforms.validators import Optional, Length, Required, URL, Email


class SearchForm(Form):
    languages = StringField('Languages', validators=[Required(), Length(1, 128)])
    #location = StringField('Location', validators=[Optional(), Length(1, 64)])
    submit = SubmitField('Search')

