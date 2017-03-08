from mongo_collector.mongo_update import mongo_add_fields
from spiders.ukrstat import ukrstat, ukrstat_o
from mongo_collector.mongo_start import ukrstat as ukrstat_db




def ukrstat_shadow():
    mongo_add_fields(ukrstat().saldo(), ukrstat_db)
    mongo_add_fields(ukrstat_o().building_index())
    mongo_add_fields([ukrstat_o().housing_meters()])

