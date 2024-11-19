# OPA-Tradebot
OPA Crypto Tradebot for Datascientest
## Description
A group Project for the bootcamp Data Engineering from Datascientest

## Table of Contents
- [Installation](#installation)
- [API access](#API-access)
- [Needs for Script running via API](#Needs-for-Script-running-via-API)
- [Architecture](#Architecture)
- [Contributing](#contributing)

## Installation
How to set up on our Ubuntu VM:

# Clone the repository:
```bash
git clone https://github.com/knoxxxy/OPA-Tradebot
cd ./OPA-Tradebot
```
# Update Docker and initiate MongoDB in a Docker container:
``` bash
./update_docker.sh #Dont use if Docker is not installed yet
docker-compose up

#In case of already existing dockerDB
docker-compose down
docker-compose up --build
```

# Read data from ZIPs in folder "Historical_data_Binance" and save it in the MongoDB
This step is now only nessesary at first startup. A Volume gets created and Docker loads in the existing data that was already read in during earlier use.
``` bash
python3 read_to_db.py
```

# Personal access to Binance Data in the MongoDB docker container
``` bash
docker exec -it mongodb_OPA mongosh
use OPA_Data
show collections #If everything went right, it should show "historical_trading_data"
db.historical_trading_data.find().pretty() #shows Data from the DB
```

# preprocess data 
``` bash
python3 preprocessing.py 
```

# (optionally) check for new collections containing preprocessed data
```bash
show collections #If everything went right new "preprocessed_data" is shown as new mongodb collection (accessed via mongo shell)
```
## API access
API Acess to have indirect access to the Bot
http://your.VM.IP:8000/docs

## Needs for Script running via API
``` python
def get_mongo_connection():
    try:
        client = MongoClient("mongodb://mongodb:27017/") # IP adress needs mongodb network defined in Docker-Compose
        db = client['OPA_Data'] # Currently, our DB is OPA_Data. This shouldnt change in the future
        collection = db['BTCUSD'] # The Idea is, to let the collection names reflect the Trading Pairs
        return collection
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        sys.exit(1)
```
To pass Arguments from the API to the script, use:
``` python
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Script for preprocessing.")
    parser.add_argument('arg1', type=str, help="Argument 1")
    parser.add_argument('arg2', type=str, help="Argument 2")
    parser.add_argument('--optionalArgument1', type=str, help="OptionalArgument", default=None)
    parser.add_argument('--optionalArgument2', type=str, help="OptionalArgument", default="Hey")

    # Parse the arguments
    args = parser.parse_args()
    
    # Call the main function with the parsed symbol
    main(args.arg1, args.arg2, args.optionalArgument1, args.optionalArgument2)
```

## Architecture
The Bot runs on three Containers.

The mongodb_OPA container runs the MongoDB Database for our data storage

The fastapi_app container runs FastAPI for outside of VM access.

The ubuntu_script_runner container runs Ubuntu for script running. Script running is seperate from the other
containers, in case of running a bad script. If the scriptrunner crahses, it shouldnt take down the entire VM, it should only stop the 
Script runner container. FastAPI and MongoDB should still be running.

# Volumes

/app Volume for FastAPI scripts. These Scripts are used by FastAPI to create Endpoints.
/scripts Volume for executable scripts on the Ubuntu Script Runner.
/data Volume for ZIP and CSV Data to insert into the database
mongo_data Volume for persistent Data between restarts of the MongoDB


## Contributing
@waladhibi (Wala Dhibi)

@karanmoa-lab (Karan Moallim)

@saxenasneha (Neha Srivastava)

@Knoxxy (Ava Coban)

As this is a groupProject for a bootcamp, no further contributors are needed currently

