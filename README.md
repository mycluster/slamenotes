# CS3398-Arctic-F2016

Team Arctic's project for CS 3398, fall 2016: A web app for note-taking and sharing, geared towards students.

This project is hosted online at [Slam eNotes](http://slamenotes.com) (slamenotes.com).

We run our project on a CentOS 7.2 server using Python 3.4, with MariaDB and Apache, but thanks to the flexibility of Django, there are plentiful options when it comes to OS, database, and webserver selection.

Our project is built with Django 1.10 and Python 3.4+, and aims to follow naming conventions for locations of static files and templates.

## Installation:
First, [install Django](https://docs.djangoproject.com/en/1.10/intro/install/).

We control certain sensitive or machine-specific settings with environment variables.
Set at least the required environment variables below.

```
Required
- SECRET_KEY: Django secret key
- DATABASE_NAME: Database name
- DATABASE_USERNAME: Database username
- DATABASE_PASSWORD: Database password

Optional
- DATABASE_ENGINE: Set the database engine (defaults to django.db.backends.mysql)
- DEBUG: Enable debug mode by setting this to 'True' (defaults to False)
```

(Note: debug mode will remove the account activation requirement, and allow Django's runserver command to serve the project's static files.)

Now migrate and run the project with the following commands:

```
python manage.py collectstatic
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

You should see a message in the console with a URL and port number. Now just visit this URL in your web browser!

## Additional Information:
Sign-ups require a @txstate.edu email address for account creation.

### External JS/jQuery libraries used:
- [jQuery](https://jquery.com/)
- [Modernizr](https://modernizr.com/)
- [CommonMark.js](https://github.com/jgm/commonmark.js/)
- [ns-autogrow](https://github.com/ro31337/jquery.ns-autogrow/)

### HTML/CSS templates used:
- [Prism by TEMPLATED](https://templated.co/prism) (modified)
- [Initializr](http://www.initializr.com/) (modified)

### Contributors
- Peter Cassetta
- Michael Luster
- Tristan Thielemann
- Paul Lindsey
- Dillon Rowan
- Juan Ortiz
