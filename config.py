import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    user = "postgres"
    password = "postgres"
    host = "localhost"
    port = "5432"
    database = "dump_db"
    SQLALCHEMY_DATABASE_URI = "postgresql://" + user + ":" + password + "@" + host + ":" + port + "/" + database
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    api_key = "0f47e74650a79cacc074c2b0a39fe61d"
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    city = 'Yekaterinburg'
    code = 'USD'

