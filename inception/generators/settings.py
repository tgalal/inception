#PARTIALLY BASED ON sqlite3dbm
#https://github.com/Yelp/sqlite3dbm/blob/master/sqlite3dbm/dbm.py

from generator import Generator, GenerationFailedException
from ..constants import InceptionConstants
import sys, sqlite3 as lite

_GET_QUERY = 'SELECT {table}.{column_val},{table}._id FROM {table} WHERE {table}.{column_key} = ?'
_GET_ALL_QUERY = 'SELECT {table}.{column_key}, {table}.{column_val} FROM {table}'
_SET_QUERY = 'INSERT OR REPLACE INTO {table} (_id, {column_key}, {column_val}) VALUES (?, ?, ?)'
_DEL_QUERY = 'DELETE FROM {table} WHERE {table}.{column_key} = ?'
_COUNT_QUERY = 'SELECT COUNT(*) FROM {table}'
_CREATE_QUERY = 'CREATE TABLE IF NOT EXISTS {table} (_id INTEGER PRIMARY KEY AUTOINCREMENT,{column_key} TEXT UNIQUE ON CONFLICT REPLACE,{column_val} TEXT);'
_INDEX_QUERY =  'CREATE INDEX IF NOT EXISTS {table}Index1 ON {table} ({column_key});'


class SettingsGenerator(Generator):
    def __init__(self, settingDbPath):
        super(SettingsGenerator, self).__init__()
        self.settingDbPath = settingDbPath
        self.sdbf = SettingsDatabaseFactory(settingDbPath)

    def generate(self, bulkSettings):
        for k, settings in bulkSettings.items():
            dbDict = self.sdbf.getIterable(k)
            for key, value in settings.items():
                self.d(k, key, str(value))
                dbDict[key] = value


class SettingsDatabaseFactory(object):
    def __init__(self, dbPath):
        self.path = dbPath
        self.readonly = False
        try:
            self.conn = lite.connect(self.path)
            self.conn.text_factory = str
        except lite.Error as e:
            print("Error %s:" % e.args[0])
            sys.exit(1)

    def getIterable(self, name):
        return SettingsDatabaseFactory.SettingsDatabase(self.conn, name, readonly = self.readonly)

    def close(self):
        if self.conn:
            self.conn.close()

    class SettingsDatabase(object):
        def __init__(self, conn, tablename, readonly = False):
            self.conn = conn
            self.tablename = tablename
            self.columnKey = "name"
            self.columnVal = "value"
            self.readonly = True
            #self.conn.execute(self.formatQuery(_CREATE_QUERY))
            #self.conn.execute(self.formatQuery(_INDEX_QUERY))

        def formatQuery(self, q):
            q = q.format(
                table= self.tablename,
                column_key = self.columnKey,
                column_val = self.columnVal,
                )
            return q

        def __setitem__(self, k, v):
            if self.readonly:
                raise error('DB is readonly')

            row = self.conn.execute(self.formatQuery(_GET_QUERY), (k,)).fetchone()
            rowId = None
            if row:
                rowId = row[1]
            self.conn.execute(self.formatQuery(_SET_QUERY), (rowId, k, v))
            self.conn.commit()

        def __getitem__(self, k):
            row = self.conn.execute(self.formatQuery(_GET_QUERY), (k,)).fetchone()
            if row is None:
                raise KeyError(k)
            return row[0]


        def __contains__(self, k):
            """D.__contains__(k) -> True if D has a key k, else False"""
            try:
                self[k]
            except KeyError:
                return False
            else:
                return True


        def __delitem__(self, k):
            """x.__delitem__(k) <==> del x[k]"""
            if self.readonly:
                raise error('DB is readonly')

            self[k]

            self.conn.execute(self.formatQuery(_DEL_QUERY), (k,))
            self.conn.commit()

        def __iter__(self):
            """Iterate over the keys of D.  Consistent with dict."""
            return self.iterkeys()


        ## Iteration
        def iteritems(self):
            """D.iteritems() -> an iterator over the (key, value) items of D"""
            for key, val in self.conn.execute(self.formatQuery(_GET_ALL_QUERY)):
                yield key, val

        def items(self):
            """D.items() -> list of D's (key, value) pairs, as 2-tuples"""
            return [(k, v) for k, v in self.iteritems()]

        def iterkeys(self):
            """D.iterkeys() -> an iterator over the keys of D"""
            return (k for k, _ in self.iteritems())

        def keys(self):
            """D.iterkeys() -> an iterator over the keys of D"""
            return [k for k in self.iterkeys()]
        def itervalues(self):
            """D.itervalues() -> an iterator over the values of D"""
            return (v for _, v in self.iteritems())
        def values(self):
            """D.values() -> list of D's values"""
            return [v for v in self.itervalues()]

        def __len__(self):
            """x.__len__() <==> len(x)"""
            return self.conn.execute(self.formatQuery(_COUNT_QUERY)).fetchone()[0]

