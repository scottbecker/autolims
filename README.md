# Project Title

autolims allows experiments to be executed by humans and lab robots working together

## setup dev environment (OSX)

#install db dependencies
brew install mysql postgres

# start mysql & postgres if not daemonized
mysql.server start
pg_ctl -D /usr/local/var/postgres start

# create autolims db user & db
# will need to update autolims/mysite/settings.py DATABASE field w/ user, db
createuser autolims --createdb -P
createdb autolims -U autolims

# to reset db (if desired):
# dropdb autolims; createdb autolims -U autolims
# clone repo
git clone https://github.com/scottbecker/autolims
cd autolims

# create python virtualenv to store dependencies locally
# I like to name mine '.pyenv' or `.py3env`
# use .pyenv/bin/<activation.script> to shim in the environment for your shell
virtualenv -p python .pyenv
. .pyenv/bin/activate.fish

# install requirements
pip install -r requirements.txt

# run migrations
python manage.py migrate

# make a django superuser
python manage.py createsuperuser

# check that the app works
python manage.py runserver
open http://localhost:8000/admin/autolims

# add test_db_fixture (kill server first)
python manage.py loaddata autolims/tests/data/test_db_fixture.json
python manage.py runserver

# create / admin autolims content at http://localhost:8000/admin/autolims
# play with app i.e. http://localhost:8000/default/1/runs/5#
