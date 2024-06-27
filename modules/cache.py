from collections import OrderedDict
import logging

from modules.metrics import MetricsHandler

class Cache:
    def __init__(self, cacheSize):
        self.dict = OrderedDict()
        self.size = cacheSize

    def find(self, alias):
        if alias not in self.dict:
            MetricsHandler.cache_misses.inc()
            return None
        
        self.dict.move_to_end(alias, last=False) #move alias to front of cache
        logging.debug(f"alias: '{alias}' is grabbed from mapping")
        MetricsHandler.cache_hits.inc()
        return self.dict[alias]

    def delete(self, alias):
        if alias not in self.dict:
            logging.debug(f"alias {alias} was not found in cache")
            return None
        self.dict.pop(alias)
        logging.debug(f"deleted {alias} from cache")

    def add(self, alias, url_output):
        if len(self.dict) == self.size: 
            data = self.dict.popitem() #remove least used alias if size reaches max
            logging.debug(f"alias: {data[0]} has been removed from cache")
        self.dict[alias] = url_output
        MetricsHandler.cache_size.set(len(self.dict))
        logging.debug("set alias: '" + alias + "' to mapping")
