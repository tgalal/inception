from .submaker import Submaker
import sqlite3

class KeyValDBSubmaker(Submaker):
    def __init__(self, *args):
        super(KeyValDBSubmaker, self).__init__(*args)

    def apply(self, dbPath, tableName, keyvals, colId = "_id", colKey = "name", colVal = "value"):
        conn = sqlite3.connect(dbPath)
        conn.text_factory = str
        table = Table(tableName, colId, colKey, colVal)
        print("Creating %s:\t%s" % (dbPath, tableName))
        for key, val in keyvals.items():
            table.insert(key, val)
        table.execute(conn)
        conn.commit()
        conn.close()

class Query(object):
    def __init__(self, baseQuery):
        self.baseQuery = baseQuery

    def __str__(self):
        return self.baseQuery

    def execute(self, conn):
        conn.execute(self.baseQuery)

class QueryWithParams(Query):
    def __init__(self, baseQuery, values):
        super(QueryWithParams, self).__init__(baseQuery)
        self.values = values

    def __str__(self):
        return self.baseQuery + ": " + ",".join(self.values)

    def execute(self, conn):
        conn.execute(self.baseQuery, self.values)

class DeleteQuery(QueryWithParams):
    pass

class InsertQuery(QueryWithParams):
    pass

class Table(object):
    _CREATE_QUERY = 'CREATE TABLE IF NOT EXISTS {table} ({column_id} INTEGER PRIMARY KEY AUTOINCREMENT,{column_key} TEXT UNIQUE ON CONFLICT REPLACE,{column_val} TEXT);'
    _INDEX_QUERY =  'CREATE INDEX IF NOT EXISTS {table}Index1 ON {table} ({column_key});'
    _SET_QUERY = 'INSERT INTO {table} ({column_id}, {column_key}, {column_val}) VALUES (?, ?, ?)'
    _DEL_QUERY = 'DELETE FROM {table} WHERE {table}.{column_key} = ?'

    def __init__(self, name, colId, colKey, colVal):
        self.id_ = 1
        self.queries = []
        self.name = name
        self.colId = colId
        self.colKey = colKey
        self.colVal = colVal
        self._create()

    def execute(self, conn):
        for query in self.queries:
            query.execute(conn)

    def __str__(self, separator = "\n"):
        return separator.join([q.__str__() for q in self.queries])

    def _create(self):
        createQuery = self.__class__._CREATE_QUERY.format(table = self.name, column_id = self.colId, column_key = self.colKey, column_val = self.colVal)
        indexQuery = self.__class__._INDEX_QUERY.format(table = self.name, column_key = self.colKey)

        self.queries.append(Query(createQuery))
        self.queries.append(Query(indexQuery))

    def insert(self, key, val):
        insertQuery = self.__class__._SET_QUERY.format(
            table = self.name,
            column_id = self.colId,
            column_key = self.colKey,
            column_val = self.colVal
        )

        deleteQuery = self.__class__._DEL_QUERY.format(
           table = self.name,
           column_key = self.colKey,
        )

        self.queries.append(InsertQuery(insertQuery, (str(self.id_), key, val)))
        self.queries.append(DeleteQuery(deleteQuery, (key,)))
        self.id_ += 1