#! /usr/bin/env python3
"""
create, read, update, delete with pylibcli
"""
import json
import logging
from pprint import pprint

from pylibcli import default, command, error, run
import pylibcli.opttools

logger = logging.getLogger('crud')
#pylibcli.opttools.DEBUG = True

@error(errno=1)
class KeyExisted(Exception):
    pass

@error(errno=2)
class KeyNotExist(Exception):
    pass

@default(filename=':str', verbose='v::=True')
class Storage():
    def __init__(self, *, filename=None, verbose=None):
        super().__init__()
        self.filename = filename or 'crud.log'
        self.data = None # lazy load
        self.dirty = None
        if verbose:
            logging.basicConfig(level = logging.DEBUG)

    def __del__(self):
        if self.dirty:
            self._save()

    def load(self):
        if self.data is not None:
            return
        try:
            logger.debug('Loading from file: "{}"'.format(self.filename))
            with open(self.filename, 'r') as f:
                self.data = json.load(f)
            logger.info('Successfully loaded.')
            return
        except OSError:
            logger.error('Failed to read file: "{}"'.format(self.filename))
        except json.JSONDecodeError:
            logger.error('Malformatted file: "{}"'.format(self.filename))
        logger.info('Using empty storage.')
        self.data = {}
        self.dirty = None

    def save(self): # lazy save
        self.dirty = True

    def _save(self):
        try:
            logger.debug('Saving to file: "{}"'.format(self.filename))
            with open(self.filename, 'w') as f:
                data = json.dump(self.data, f)
            logger.info('Successfully saved.')
        except (OSError):
            logger.error('Failed to write file: "{}"'.format(self.filename))

    @command(key='k:str', value='v:int,float,str')
    def create(self, *, key, value):
        self.load()
        logger.debug('Creating key: {} with value: {}'.format(repr(key), repr(value)))
        if key in self.data:
            raise KeyExisted(key)
        else:
            self.data[key] = value
            logger.info('Created.')
        self.save()
        return self # chainable

    @command(key='k:str', value='v:int,float,str')
    def read(self, *, key):
        self.load()
        logger.debug('Reading key: {}'.format(repr(key)))
        if key in self.data:
            value = self.data[key]
            logger.info('Read: {} -> {}'.format(repr(key), repr(value)))
            print(value)
        else:
            raise KeyNotExist(key)
        return self # chainable

    @command(key='k:str', value='v:int,float,str')
    def update(self, *, key, value):
        self.load()
        logger.debug('Updating key: {} with value: {}'.format(repr(key), repr(value)))
        if key in self.data:
            self.data[key] = value
            logger.info('Updated.')
        else:
            raise KeyNotExist(key)
        self.save()
        return self # chainable

    @command(key='k:str', value='v:int,float,str')
    def delete(self, *, key):
        self.load()
        logger.debug('Deleting key: {}'.format(repr(key)))
        if key in self.data:
            value = self.data[key]
            del self.data[key]
            logger.info('Deleted: {} -> {}'.format(repr(key), repr(value)))
        else:
            raise KeyNotExist()
        self.save()
        return self # chainable

    @command
    def list(self):
        self.load()
        logger.debug('Lisintg storage')
        pprint(self.data)
        return self # chainable

if __name__ == '__main__':
    run()
