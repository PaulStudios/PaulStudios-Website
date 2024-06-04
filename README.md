# PaulStudios Website
 The Django edition of the official Website. (In Development)
## Usage
1. Download the `docker-compose.yml` file located in `src`.
2. Open terminal and run `docker-compose up`.

## Build and Run
1. Install requirements.
2. Set `MODE = "development"` in `src/PaulStudios/settings.py.`
3. Install Redis and run `redis-server`
4. Open terminal at `/src` and run the following command `celery -A PaulStudios worker -l info `
5. Open another terminal window and run: `python3 manage.py runserver_plus`

