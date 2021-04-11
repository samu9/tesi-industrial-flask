# Industrial Backend
Before launching the app you need to export the variable containing the path to the configuration file.
```bash
export INDUSTRIAL_CONFIG=/home/user/app/config.ini 
```

## Configuration file
Create a file with the following properties:
* API_KEY: Secret Key used in _Authorization_ header to be checked when the client will make a request
* SQLALCHEMY_DATABASE_URI: used to connect to the database with SQLAlchemy
* AREA_ID, SECTOR_ID: Based on the data in the database, the application will retrieve the only machines relative to the specified Area and Sector
* IMAGE_FORMAT: "jpg"
* UPLOAD_FOLDER: directory where are stored images uploaded by the client
* USER_IMG_DIR: direcotory where are stored users images

## Database
To initialize the database with sample data, simply run
```bash
python industrial/database/create.py
```

to create the database, then

```bash
python script/populate.py
```
to populate it.