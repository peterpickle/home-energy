# home-energy

## Setup

### Redis database

1. Install redis
2. Install redis time series
3. Create rules
   - For Redis time series, rules need to be created.
     Execute each rule in the redis-cli beofr starting one of the input scripts.

#### Commands

Electricity

Per second, keep 1 week.
Per minute, keep 6 months.
Per 15 minutes, keep forever.

```
TS.CREATE electricity_down_sec RETENTION 604800000 DUPLICATE_POLICY SUM LABELS dir down type down granularity 1s

TS.CREATE electricity_down_1min RETENTION 15768000000 LABELS dir down type down granularity 1m
TS.CREATERULE electricity_down_sec electricity_down_1min AGGREGATION avg 60000

TS.CREATE electricity_down_15min LABELS dir down type down granularity 15m
TS.CREATERULE electricity_down_sec electricity_down_15min AGGREGATION avg 900000

TS.CREATE electricity_down_1h LABELS dir down type down granularity 1h
TS.CREATERULE electricity_down_sec electricity_down_1h AGGREGATION avg 3600000


TS.CREATE electricity_up_sec RETENTION 604800000 DUPLICATE_POLICY SUM LABELS dir up type up granularity 1s

TS.CREATE electricity_up_1min RETENTION 15768000000 LABELS dir up type up granularity 1m
TS.CREATERULE electricity_up_sec electricity_up_1min AGGREGATION avg 60000

TS.CREATE electricity_up_15min LABELS dir up type up granularity 15m
TS.CREATERULE electricity_up_sec electricity_up_15min AGGREGATION avg 900000

TS.CREATE electricity_up_1h LABELS dir up type up granularity 1h
TS.CREATERULE electricity_up_sec electricity_up_1h AGGREGATION avg 3600000
```

Production

Per minute, keep 6 months.
Per 15 minutes, keep forever.

```
TS.CREATE electricity_prod_1min RETENTION 15768000000 DUPLICATE_POLICY MAX LABELS type prod granularity 1m

TS.CREATE electricity_prod_15min LABELS type prod granularity 15m
TS.CREATERULE electricity_prod_1min electricity_prod_15min AGGREGATION avg 900000
```

Production daily

Per minute, keep 2 days.
Per day, keep forever.

```
TS.CREATE electricity_prod_gen_daily_1min RETENTION 172800000 DUPLICATE_POLICY MAX LABELS type prod value dayGen

TS.CREATE electricity_prod_gen_daily_1day LABELS type prod value dayGen granularity 1d
TS.CREATERULE electricity_prod_gen_daily_1min electricity_prod_gen_daily_1day AGGREGATION max 86400000
```

Gas

Per 5 minutes, keep 6 months.
Per 15 minutes, keep forever.

```
TS.CREATE gas_5min RETENTION 15768000000 DUPLICATE_POLICY SUM LABELS type gas granularity 5m

TS.CREATE gas_15min LABELS type gas granularity 15m
TS.CREATERULE gas_5min gas_15min AGGREGATION sum 900000
```

Disable the expiry of 1 minute data (optional)
```
TS.ALTER electricity_down_1min RETENTION 0
TS.ALTER electricity_up_1min RETENTION 0 
TS.ALTER electricity_prod_1min RETENTION 0
```

## Launch the application

1. start the redis-server
```
cd input
redis-server redis.conf
```

The redis-server can be started from anywhere. Just make sure to use the redis.conf file provided.
The location of the redis time series might need adjustment.
This will create a file dump.rdb. This is your database. If you remove it, your data will be lost.

2. start p1-reader

3. optionally: start production reader

4. start the GUI
   - deploy the directory 'web' with django (See "First Deploy" section below)

## First deploy with Django and Apache

These instructions are without virtual python environment.

#### 1. Install Django.
```
python -m pip install django
sudo python -m pip install django
#Install django for the user of the webserver
sudo -H -u www-data python -m pip install django
```

#### 2. Modify settings for production. (CHECKOUT_DIR/web/home_portal/settings.py)
It's best to store these changes in a diff. You will need to apply these if you update to a newer version.

```
DEBUG = False
ALLOWED_HOSTS = ['yourdomainname.org', '192.168.0.XXX', 'localhost']
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# The location of the static files.
STATIC_URL = '/static/'
STATIC_ROOT = '/var/www/html/static/'
```

#### 3. Create the deploy location (/deploy).
It's advised to not have to deploy location in a home directory.
```
sudo mkdir /deploy
```

#### 4. Create the directory where the static files will be served.
This has to match with what you set in "STATIC_ROOT" of settings.py.
```
sudo mkdir /var/www/html/static
```

#### 5. Copy the django project to the deploy location.
```
cd CHECKOUT_DIR
sudo cp -r web/* /deploy
```

#### 6. Create the DB and super user.
```
cd /deploy
sudo python manage.py migrate
sudo python manage.py createsuperuser
```

#### 7. Collect the static files with django.
All static files will be copied to the location set in "STATIC_ROOT" of settings.py
```
cd /deploy
sudo python manage.py collectstatic
```

#### 8. Create a secret key file or set it in /deploy/home_portal/settings.py.
```
sudo sh -c "python manage.py shell -c 'from django.core.management import utils; print(utils.get_random_secret_key())' > /deploy/secret_key.txt"
```

#### 9. Change the owner of the database and the deploy location to the user the server is using.
For apache the user is usually "www-data" or "deamon"
```
sudo chown www-data /deploy/db.sqlite3
sudo chown www-data /deploy
```

### Apache

#### 10. Install mod_wsgi for apache
Important: "mod_wsgi" needs to be compiled for the python version that will be used.

#### 11. Tell apache where to find the project.
```
sudo nano /etc/apache2/apache2.conf
```

```
WSGIScriptAlias / /deploy/home_portal/wsgi.py
WSGIPythonPath /deploy

<Directory /deploy/home_portal>
    <Files wsgi.py>
        Require all granted
    </Files>
</Directory>
```

#### 12. Make an alias to access the static files
If WSGIScriptAlias uses "/" as a first argument (like we did above), then the site will be deployed in the root of the web server.
In this case, you will need an alias to access other (static) files in the root dir.
Add the line below to /etc/apache2/apache2.conf.
```
Alias /static /var/www/html/static
```

#### 13. Restart Apache.
`sudo service apache2 restart` or `sudo systemctl restart apache2`

#### 14. Check the error log.
```
tail -n 30 /var/log/apache2/error.log
```

## Upgrade Django project

### Stash you current changes.
```
cd CHECKOUT_DIR
git stash
```

### Checkout a new version of the home-energy repo.
`git pull`

### Apply you changes again. (Or perform step 2 of the first deploy instructions.)
`git stash pop`

### Copy the django project to the deploy location. (Step 5 of first deploy instructions.)
```
cd CHECKOUT_DIR
sudo cp -r web/* /deploy
```

### Collect static files. (Step 7 of first deploy instructions.)
```
cd /deploy
sudo python manage.py collectstatic
```

### Restart Apache (Step 13 of first deploy instructions.)
`sudo service apache2 restart` or `sudo systemctl restart apache2`
