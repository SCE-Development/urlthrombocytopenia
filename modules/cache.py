from collections import OrderedDict
import logging

from modules.metrics import MetricsHandler

class MappingLRUCache:
    def __init__(self, cacheSize):
        self.dict = OrderedDict()
        self.size = cacheSize

    def find(self, alias):
        if alias in self.dict:
            self.dict.move_to_end(alias, last=False) #move alias to front of cache
            logging.debug("alias: '" + alias + "' is grabbed from mapping")
            MetricsHandler.cache_hits.inc()
            return self.dict[alias]
        MetricsHandler.cache_misses.inc()
        return None

    def add(self, alias, url_output):
        if len(self.dict) == self.size: 
            data = self.dict.popitem() #remove least used alias if size is 100
            logging.debug("alias: '" + data[0] + "' has been removed from cache")
        else:
            MetricsHandler.cache_size.inc()
        self.dict[alias] = url_output
        logging.debug("set alias: '" + alias + "' to mapping")