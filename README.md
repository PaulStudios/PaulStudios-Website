# PaulStudios Website
 The Django edition of the official Website. (In Development)

## Usage
1. Install requirements.
2. Install Redis and run `redis-server`
3. Open terminal at `/src` and run the following command `celery -A PaulStudios worker -l info --without-gossip --without-mingle --without-heartbeat -Ofair`
4. Open another terminal window and run: `python3 manage.py runserver_plus`