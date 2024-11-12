# OPA-Tradebot
OPA Crypto Tradebot for Datascientest
## Description
A group Project for the bootcamp Data Engineering from Datascientest

## Table of Contents
- [Installation](#installation)
- [Work in Progress](#Work-in-Progress)
- [Usage](#usage)
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

# API access
Newly build API access. For docs look at:
http://your.VM.IP:8000/docs
# preprocess data 
``` bash
python3 preprocessing.py 
```

# (optionally) check for new collections containing preprocessed data
```bash
show collections #If everything went right new "preprocessed_data" is shown as new mongodb collection (accessed via mongo shell)
```


## Work in Progress
Next step is, to link the ML model to the newly created MongoDB running in a Docker Container

## Usage
Still in work

## Contributing
@waladhibi (Wala Dhibi)

@karanmoa-lab (Karan Moallim)

@saxenasneha (Neha Srivastava)

@Knoxxy (Ava Coban)

As this is a groupProject for a bootcamp, no further contributors are needed currently

