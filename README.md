# OPA-Tradebot
OPA Crypto Tradebot for Datascientest
## Description
A group Project for the bootcamp Data Engineering from Datascientest

## Table of Contents
- [Installation](#installation)
- [API access](#API-access)
- [Needs for Script running via API](Needs-for-Script-running-via-API)
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
./update_docker.sh
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
        db = client['OPA_Data'] # Currently, our DB is OPA_Data, and this shouldnt change in the future
        collection = db['BTCUSD'] # The Idea is, to let the collection names reflect the Trading Pairs
        return collection
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        sys.exit(1)
```




## Contributing
@waladhibi (Wala Dhibi)

@karanmoa-lab (Karan Moallim)

@saxenasneha (Neha Srivastava)

@Knoxxy (Ava Coban)

As this is a groupProject for a bootcamp, no further contributors are needed currently

