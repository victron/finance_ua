from curs_auto.mongo_worker.mongo_update import mongo_add_fields
from curs_auto.spiders_legacy.ukrstat import ukrstat, ukrstat_o
from curs_auto.mongo_worker.mongo_start import ukrstat as ukrstat_db


def ukrstat_shadow():
    mongo_add_fields(ukrstat().saldo(), ukrstat_db)
    mongo_add_fields(ukrstat_o().building_index())
    mongo_add_fields([ukrstat_o().housing_meters()])

