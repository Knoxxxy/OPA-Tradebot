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
git clone https://github.com/knoxxy/OPA-Tradebot
cd ./OPA-Tradebot
```
# Update Docker and initiate MongoDB in a Docker container:
``` bash
./update_docker.sh
./start_mongo_docker.sh
```

# Read data from ZIPs in folder "Historical_data_Binance" and save it in the MongoDB
``` bash
python3 read_to_db.py
```

# Personal access to Binance Data in the MongoDB docker container
``` bash
docker exec -it mongodb_OPA mongosh
use binance_data
show collections #If everything went right, it should show "historical_trading_data"
db.historical_trading_data.find().pretty() #shows Data from the DB
```

# preprocess data 
''' bash
python3 preporcess.py 
'''

# check for new collections containing preprocessed data
show collections #If everything went right new "preprocessed_data" is shown
as new mongodb collection


## Work in Progress
Next step is, to link the ML model to the newly created MongoDB running in a Docker Container

## Usage
Still in work

## Contributing
@waladhibi (Wala Dhibi)

@karanmoa-lab (Karan Moallim)

@??? (Neha Srivastava)

@Knoxxy (Ava Coban)

As this is a groupProject for a bootcamp, no further contributors are needed currently

