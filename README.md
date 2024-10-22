# OPA-Tradebot
OPA Crypto Tradebot for Datascientest
## Description
A group Project for the bootcamp Data Engineering from Datascientest

## Table of Contents
- [Installation](#installation)
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

## Usage
Still in work

## Contributing
@waladhibi (Wala Dhibi)
@karanmoa-lab (Karan Moallim)
@??? (Neha Srivastava)
@Knoxxy (Ava Coban)

