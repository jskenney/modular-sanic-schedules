#!/usr/bin/python3

# MySQL helper for the schedule scripts.  It uses PyMySQL (installed with
# modular-sanic, through aiomysql) and the database settings from
# modular-sanic's .env file (see sanic_env.py).

import pymysql
from sanic_env import db_settings

# To import from this library,
#   from db6 import db

# To use the db object
#   Example 1.
#     col, data, lastrow, error, warnings = db.query("select * from session")
#   Example 2.
#     values = ("user1", "test", )  <-- note the final / extra comma
#     col, data, lastrow, error, warnings = db.query("select * from session where user=%s and password=%s", values)
#   query_dict returns (rows, error, warnings), each row a dict of strings.

# Database connection class
class connectdb:
    def __init__(self, dbuser, dbpass, dbhost, dbname, dbport=3306):
        self.dblink = pymysql
        self.db = pymysql.connect(user=dbuser, password=dbpass, host=dbhost, port=dbport, database=dbname,
                                  charset='utf8mb4', autocommit=True)
        self.mode = "pymysql"

    # GRADING: return tables
    def getTables(self):
        q = "SHOW TABLES"
        results = []
        columns, data, lastrow, error, warning = self.query(q)
        for line in data:
            results.append(line[0])
        return results

    # GRADING: return columns
    def getFields(self, table):
        q = "SHOW FIELDS IN "+table
        results = []
        columns, data, lastrow, error, warning = self.query(q)
        x = self.rows_to_dict(columns, data)
        for line in x:
            f = line['Field']
            results.append(f)
        return results

    # GRADING: return primary keys
    def getPK(self, table):
        q = "SHOW FIELDS IN "+table
        results = []
        columns, data, lastrow, error, warning = self.query(q)
        x = self.rows_to_dict(columns, data)
        for line in x:
            f = line['Field']
            k = line['Key']
            if k == 'PRI':
                results.append(f)
        return results

    # GRADING: return foreign keys
    def getFK(self, table):
        q = "SHOW CREATE TABLE "+table
        results = {}
        columns, data, lastrow, error, warning = self.query(q)
        if len(data) != 1:
            return results
        data = data[0][1].split('\n')
        for line in data:
            if line.find('FOREIGN KEY') != -1:
                line = line.strip().replace('`','')
                local = line.split('(')[1].split(')')[0]
                ft = line.split('REFERENCES ')[1].split(' ')[0]
                fk = line.split('REFERENCES ')[1].split('(')[1].split(')')[0]
                if not local in results:
                    results[local] = []
                results[local].append([ft, fk])
        return results

    # GRADING: get a single row
    def getRowCount(self, table):
        q = "SELECT COUNT(*) FROM "+table
        results = 0
        columns, data, lastrow, error, warning = self.query(q)
        if len(data) == 1:
            results = int(data[0][0])
        return results

    # Query the database, returns (columns, rows, lastrowid, error, warnings).
    # error is '' on success; warnings is None, or the server's warnings.
    def query(self, sql, *prepare):
        cursor = self.db.cursor()
        error = ""
        warning = None
        try:
            if prepare:
                cursor.execute(sql, prepare[0])
            else:
                cursor.execute(sql)
            # Rows are already buffered, so the warnings can be read now
            if getattr(cursor._result, 'warning_count', 0):
                warning = self.db.show_warnings()
        except self.dblink.Error as e:
            error = str(e)      # DB will prevent issue

        lastrow = cursor.lastrowid
        columns = cursor.description

        try:                    # Check for no results due to an error in SQL
            data = cursor.fetchall()
        except self.dblink.Error:
            data = []
        if columns is None:
            data = []
            columns = []

        cursor.close()

        return columns, list(data), lastrow, error, warning

    def query_dict(self, sql, *prepare):
        if prepare:
            columns, data, lastrow, error, warning = self.query(sql, prepare[0])
        else:
            columns, data, lastrow, error, warning = self.query(sql)
        results = self.rows_to_dict(columns, data)
        return results, error, warning

    def rows_to_dict(self, columns, data):
        results = []
        for line in data:
            newline = self.row_to_dict(columns, [line])
            results.append(newline)
        return results

    # Values are returned as strings (None becomes 'None'), as before
    def row_to_dict(self, columns, data):
        results = {}
        for column in columns:
            column = column[0]
            results[column] = ''
        for line in data:
            for i in range(len(columns)):
                item = line[i]
                results[columns[i][0]] = str(item)
        return results

    def get_value(self, columns, data, column, *default):
        results = ''
        if default:
            results = default
        if len(data) == 0:
            return results
        for row in data:
            for i in range(len(row)):
                if columns[i][0] == column:
                    if str(row[i]) != '':
                        return str(row[i])
        return results

    def clean_columns(self, columns):
        results = []
        for col in columns:
            results.append(col[0])
        return results

    def trim(self, columns, data, chkcolumns):
        results = []
        for row in data:
            toprint = []
            for col in chkcolumns:
                for i in range(len(columns)):
                    if col == columns[i][0]:
                        toprint.append(row[i])
            results.append(toprint)
        return chkcolumns, results

    def print_header_dash(self, column_names, column_size):
        results = '+'
        for i in range(len(column_names)):
            col = column_names[i]
            size= column_size[col]
            for ii in range(size+2):
                results = results + '-'
            results = results + '+'
        results = results[:-1] + '+'
        print(results)

    def print_row(self, column_names, column_size, row):
        results = ''
        for i in range(len(column_names)):
            col = column_names[i]
            size= column_size[col]
            results = results + '| ' + str(row[i]).strip().ljust(size) + ' '
        results = results + '|'
        print(results)

    def print_results(self, columns, data, *html):
        if columns != [] and data != []:
            column_names = []
            column_size = {}
            if html:
                print('<pre>')
            for col in columns:
                col = col[0]
                column_names.append(col)
                column_size[col] = len(col)
            for row in data:
                for i in range(len(columns)):
                    col = column_names[i]
                    if len(str(row[i])) > column_size[col]:
                        column_size[col] = len(str(row[i]))
            self.print_header_dash(column_names, column_size)
            self.print_row(column_names, column_size, column_names)
            self.print_header_dash(column_names, column_size)
            for row in data:
                self.print_row(column_names, column_size, row)
            self.print_header_dash(column_names, column_size)
            if html:
                print('</pre>')

    def print_results_bycols(self, columns, data, chkcolumns, *html):
        if columns != [] and data != []:
            column_names = []
            column_size = {}
            if html:
                print('<pre>')
            for col in columns:
                col = col[0]
                column_names.append(col)
                column_size[col] = len(col)
            for row in data:
                for i in range(len(columns)):
                    col = column_names[i]
                    if len(str(row[i]).string()) > column_size[col]:
                        column_size[col] = len(str(row[i]))
            self.print_header_dash(chkcolumns, column_size)
            self.print_row(chkcolumns, column_size, chkcolumns)
            self.print_header_dash(chkcolumns, column_size)
            for row in data:
                toprint = []
                for col in chkcolumns:
                    for i in range(len(columns)):
                        if col == columns[i][0]:
                            toprint.append(row[i])
                self.print_row(chkcolumns, column_size, toprint)
            self.print_header_dash(chkcolumns, column_size)
            if html:
                print('</pre>')

# Establish the connection to the Database
db = connectdb(db_settings['DB_USER'], db_settings['DB_PASS'], db_settings['DB_HOST'], db_settings['DB_NAME'], db_settings['DB_PORT'])
