from .submaker import Submaker
import sqlite3

class KeyValDBSubmaker(Submaker):
    def __init__(self, *args):
        super(KeyValDBSubmaker, self).__init__(*args)
        self.locale = "en_US"

    def setLocale(self, locale):
        self.locale = locale

    def apply(self, dbPath, version, tableKeyVals, colId = "_id", colKey = "name", colVal = "value", schema = ""):
        colKey = colKey or "name"
        colVal = colVal or "value"
        conn = sqlite3.connect(dbPath)
        conn.text_factory = str

        schema = ("PRAGMA user_version = %s;" % version) + schema

        conn.executescript(schema)
        # table = Table(tableName, colId, colKey, colVal)

        for tableName, data in tableKeyVals.items():

            xtable = XTable(tableName)
            if not schema:
                xtable.setPKColumn(colId)
                xtable.addColumn(colKey, str)
                xtable.addColumn(colVal, str)
                xtable.addIndex(colKey, tableName + "Index1")
                xtable.create()
            for key, val in data.items():
                kwargs = {
                    colKey: key,
                    colVal: val
                }
                xtable.insert(**kwargs)

            xtable.execute(conn)
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


class Column(object):

        _TYPE_MAP = {
            int: "INTEGER",
            str: "TEXT"
        }

        def __init__(self, name, typ):
            self.name = name
            self.typ = typ
            assert typ in self.__class__._TYPE_MAP, "%s is not supported" % typ
            self.unique = False
            self.conflictBehavior = "REPLACE"
            self.autoincrement = False
            self.pk = False

        def setPrimaryKey(self, pk):
            self.pk = pk

        def isPrimaryKey(self):
            return self.pk

        def isAutoIncerment(self):
            return self.autoincrement

        def setAutoIncrement(self, autoIncrement):
            if autoIncrement and not self.typ is int:
                raise Exception("CAN'T AUTOINCREMENT NON INT TYPE")
            self.autoincrement = autoIncrement

        def setUnique(self, conflict = "REPLACE"):
            self.unique = True
            self.conflictBehavior = conflict

        def unsetUnique(self):
            self.unique = False

        def isUnique(self):
            return self.unique

        def __str__(self):
            colStr = "{name} {typ} {pk} {autoincr} {unique}".format(
                name = self.name,
                typ = self.__class__._TYPE_MAP[self.typ],
                pk = "PRIMARY KEY"  if self.isPrimaryKey() else "",
                autoincr = "AUTOINCREMENT" if self.autoincrement else "",
                unique = ("UNIQUE ON CONFLICT %s" % self.conflictBehavior) if self.isUnique() else ""
            )

            return colStr

class PrimaryKeyColumn(Column):
    def __init__(self, name):
        super(PrimaryKeyColumn, self).__init__(name, int)
        self.setAutoIncrement(True)
        self.setPrimaryKey(True)

class XTable(object):
    _CREATE_QUERY = 'CREATE TABLE IF NOT EXISTS {table} ({cols});'
    _INDEX_QUERY =  'CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({column});'
    _INSERT_QUERY = 'INSERT INTO {table} ({cols}) VALUES ({vals})'

    def __init__(self, name):
        self.name = name
        self.primaryKey = None
        self.columns = []
        self.indices = {}
        self.queries = []


    def __str__(self, separator = "\n"):
        return separator.join([q.__str__() for q in self.queries])

    def setPKColumn(self, name):
        self.primaryKey = PrimaryKeyColumn(name)

    def addColumn(self, name, typ):
        self.columns.append(Column(name, typ))

    def addIndex(self, colName, indexName):
        for c in self.columns:
            if c.name == colName:
                self.indices[colName] = indexName
                return
        raise Exception("Column %s is not in table, can't set index" % colName)

    def create(self):
        cols = [col.__str__() for col in self.columns]
        if self.primaryKey:
            cols.insert(0, self.primaryKey.__str__())

        colsStr = ", ".join(cols)
        createQuery = self.__class__._CREATE_QUERY.format(table = self.name, cols = colsStr)
        self.queries.append(Query(createQuery))

        for colName, indexName in self.indices.items():
            indexQuery = self.__class__._INDEX_QUERY.format(index_name = indexName, column = colName, table = self.name)
            self.queries.append(Query(indexQuery))

    def insert(self, **kwargs):
        cols = kwargs.keys()
        colsStr = ", ".join(cols)
        argsStr = ", " .join(["?" for i in cols])
        preFormatedInsertQuery = self._INSERT_QUERY.format(cols = colsStr, vals = argsStr, table = self.name)
        self.queries.append(InsertQuery(preFormatedInsertQuery, (kwargs.values())))

    def execute(self, conn):
        for query in self.queries:
            query.execute(conn)

# class MetadataTable(object):
#     _CREATE_QUERY = 'CREATE TABLE IF NOT EXISTS android_metadata (locale TEXT);'

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

        self.queries.append(DeleteQuery(deleteQuery, (key,)))
        self.queries.append(InsertQuery(insertQuery, (str(self.id_), key, val)))
        self.id_ += 1