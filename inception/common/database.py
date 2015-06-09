import sqlite3
import tempfile
import os
import sys
if sys.version_info >= (3,0):
    unicode = str

class TableIndex(object):
    SQL_INDEX = "CREATE INDEX {indexName} ON {tableName} ({columnName});"
    def __init__(self, tableColumn, indexName):
        self.tableColumn = tableColumn
        self.name = indexName

    def toSql(self):
        return self.__class__.SQL_INDEX.format(
            indexName = self.name,
            tableName = self.tableColumn.table.name,
            columnName = self.tableColumn.name
            )

class TableColumn(object):
    def __init__(self, table, name, type_, auto = False):
        self.table = table
        self.name = name
        self.auto = auto
        self.indices = []
        if not type(type_) is type:
            assert type(type_) in (str, unicode), "Invalid type %s" % type(type_)
            type_ = type_.upper()
            if type_ == "TEXT":
                self.type = str
            elif type_ == "INTEGER":
                self.type = int
            else:
                raise ValueError("Unsupported type %s" % type_)

    def __eq__(self, other):
        return self.name == other.name and self.type == other.type

    def isAuto(self):
        return self.auto

    def addIndex(self, indexName):
        self.indices.append(TableIndex(self, indexName))

    def toSql(self):
        return "{name} {type}".format(name = self.name, type = self.getSqlType())

    def getSqlType(self):
        return self.typeToSqlType(self.type)

    def typeToSqlType(self, type_):
        if type_ == int:
            return "INTEGER"

        if type_ == str:
            return "TEXT"

        raise ValueError("Unknown type %s" % type_)

    def __str__(self):
        return self.toSql()

class TableRow(object):
    SQL_INSERT = "INSERT INTO {tableName}({cols}) VALUES({vals});"
    def __init__(self, table, **kwargs):
        self.table = table
        self.cells = []
        for key,val in kwargs.items():
            col = table.getColumn(key)
            if not col:
                raise ValueError(table.name + " does not contain col %s" % key)

            self.cells.append(TableCell(self, col, val))

        for col in table.getColumns():
            if not col.isAuto() and col.name not in kwargs:
                self.cells.append(TableCell(self, col, None))

    def toDict(self):
        out = {}
        for cell in self.cells:
            out[cell.tableColumn.name] = cell.getValue()

        return out

    def getValueFor(self, colName):
        for cell in self.cells:
            if cell.tableColumn.name == colName:
                return cell.getValue()

        raise ValueError("Invalid column name %s" % colName)


    def toSql(self):
        columns = []
        values = []
        for cell in self.cells:
            columns.append(cell.tableColumn.name)
            values.append(cell.getSqlValue())

        return self.__class__.SQL_INSERT.format(
            tableName = self.table.name,
            cols = ",".join(columns),
            vals = ",".join(values)
            )

    def __str__(self):
        return self.toSql()


class TableCell(object):
    def __init__(self, tableRow, tableColumn, value):
        self.tableRow = tableRow
        self.tableColumn = tableColumn
        self.value = value


    def getValue(self):
        return self.value

    def getSqlValue(self):

        if self.value is None:
            if self.tableColumn.type is str:
                return "NULL"
            elif self.tableColumn.type is int:
                return "0"

        if self.tableColumn.type is str:
            return "'%s'" % self.value.replace("'", "\'")

        return str(self.value)

class Table(object):
    SQL_INSERT = "INSERT INTO {tableName}({cols}) VALUES({vals});"
    SQL_TABLE_COLS = "PRAGMA table_info({tableName});"
    SQL_TABLE_INDEX = "PRAGMA index_info({indexName});"
    SQL_SELECT = "SELECT {cols} from {tableName};"
    def __init__(self, database, name):
        self.database = database
        self.name = name
        self.columns = []
        self.rows = []

        sql = self.__class__.SQL_TABLE_COLS.format(tableName = name)
        for item in self.database.execute(sql).fetchall():
            self.columns.append(TableColumn(self, item[1], item[2], auto= item[1] == "_id"))

    def __eq__(self, other):
        if len(self.columns) != len(other.columns):
            return False

        for col in self.columns:
            if col not in other.columns:
                return False

        return True


    def addIndex(self, columnName, indexName):
        self.getColumn(columnName).addIndex(indexName)

    def hasColumn(self, name):
        return True if self.getColumn(name) else False

    def getColumn(self, name):
        for col in self.columns:
            if col.name == name:
                return col

        return None

    def getColumns(self):
        return self.columns

    def toSql(self):
        return "CREATE TABLE {name}({cols})".format(name = self.name, cols = ", ".join([col.__str__() for col in self.columns]))

    def createRow(self, **kwargs):
        self.rows.append(TableRow(self, **kwargs))

    def getRows(self):
        return self.rows

    def selectRows(self, getQuery = False):
        cols = [col.name for col in self.columns]
        sql = self.__class__.SQL_SELECT.format(cols = ",".join(cols), tableName = self.name)
        if getQuery:
            return sql
        rows = []
        for row in self.database.execute(sql).fetchall():
            dataDict = {}
            for i in range(0, len(cols)):
                dataDict[cols[i]] = row[i]
            rows.append(TableRow(self, **dataDict))

        return rows

    def insert(self, **kwargs):
        for key in kwargs.keys():
            if not self.hasColumn(key):
                raise ValueError("Invalid column name %s" % key)

        insertColsList = kwargs.keys()[:]
        insertValsList= []
        for col in insertColsList:
            insertValsList.append(kwargs[col])


        self.database.query(self.__class__.SQL_INSERT.format(tableName = self.name,
            cols = ",".join(insertColsList),
            vals = ",".join(insertValsList)
            ))



    def __str__(self):
        return self.toSql()

class Database(object):
    SQL_TABLES = "SELECT  name from sqlite_master where type = 'table' and name <> 'sqlite_sequence';"
    def __init__(self, schemaOrDbPath):
        self.tables = []
        self.queries = []
        self.version = 0

        db = tempfile.mkstemp()[1]

        self.conn = sqlite3.connect(db)
        try:
            self.conn.executescript(schemaOrDbPath)
        except sqlite3.OperationalError:
            if not os.path.exists(schemaOrDbPath):
                raise
            self.conn.close()
            self.conn = sqlite3.connect(schemaOrDbPath)

        self.setVersion(self._getVersion())

        tableNames = [data[0] for data in self.conn.execute(self.__class__.SQL_TABLES).fetchall()]
        for tableName in tableNames:
            self.tables.append(Table(self, tableName))

    def isEqualSchema(self, database):
        if len(self.getTables()) != len(database.getTables()):
            return False

        dbTables = database.getTables()
        for table in self.getTables():
            if not table in dbTables:
                return False

        return True

    def getSchema(self):
        out = ""
        for row in self.execute("SELECT sql FROM sqlite_master where sql is not null and name <> 'sqlite_sequence'").fetchall():
            out += row[0] + ";"
        return out

    def setVersion(self, version):
        self.version = version

    def getVersion(self):
        return self.version

    def _getVersion(self):
        return self.conn.execute("pragma user_version").fetchone()[0]

    def getQueries(self):
        #return self.queries
        queries = []
        for table in self.tables:
            for row in table.rows:
                queries.append(row.toSql())

        return queries

    def getTables(self):
        return self.tables

    def execute(self, script):
        return self.conn.execute(script)

    def query(self, query):
        self.queries.append(query)

    def getTable(self, tableName):
        for t in self.tables:
            if t.name == tableName:
                return t
        return None

    def hasTable(self, name):
        for t in self.tables:
            if t.name == name:
                return True

        return False

    def toSql(self):
        return "\n".join([t.__str__() for t in self.tables])

    def __str__(self):
        return self.toSql()
