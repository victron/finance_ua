#!/usr/bin/env bash

DB_NAME="fin_ua"
host="192.168.1.125"

function get_collections {
python3 << END
from pymongo import MongoClient

DB_NAME = 'fin_ua'

client = MongoClient()
DATABASE = client[DB_NAME]

collection_list = DATABASE.collection_names(include_system_collections=False)

for collection in collection_list:
    print(collection, end=' ')
END
}

collections_list=$(get_collections)
#collections_list=`python3 collections_list.py`
for collection in ${collections_list}; do
    echo "exporting ${collection}"
    mongoexport --host ${host} --db ${DB_NAME} --collection ${collection} --out ./${collection}.csv
#    mongoexport --db ${DB_NAME} --collection ${collection} --out ./${collection}.csv
done
exit 0
