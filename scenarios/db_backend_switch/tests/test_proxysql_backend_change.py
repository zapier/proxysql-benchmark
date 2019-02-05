import  unittest
import MySQLdb
import time


class TestProxysqlTransactionDuringBackendChange(unittest.TestCase):

    def setUp(self):
        db1 = self.get_db_connection('db1')
        db1.cursor().execute('CREATE TABLE IF NOT EXISTS count (count INTEGER);')

        db2 = self.get_db_connection('db2')
        db2.cursor().execute('CREATE TABLE IF NOT EXISTS count (count INTEGER);')

    def get_proxysql_db_connection(self):
        db = MySQLdb.connect(
            host='proxysql',
            port=6033,
            user='sbtest1',
            passwd='password',
            db='sbtest')
        return db

    def get_proxysql_admin_connection(self):
        db = MySQLdb.connect(
            host='proxysql',
            port=6032,
            user='admin1',
            passwd='admin1',
            db='main')
        return db

    def get_db_connection(self, host, port=None, user=None, passwd=None, db=None):
        db = MySQLdb.connect(
            host=host,
            port=port or 3306,
            user=user or 'sbtest1',
            passwd=passwd or 'password',
            db=db or 'sbtest')
        return db

    def tearDown(self):
        proxysql = self.get_proxysql_admin_connection()
        proxysql.cursor().execute('LOAD MYSQL QUERY RULES FROM DISK;')
        proxysql.cursor().execute('LOAD MYSQL QUERY RULES TO RUNTIME;')
        db = self.get_db_connection('db1')
        cursor = db.cursor()
        cursor.execute("DELETE FROM count;")
        db.commit()
        db.close()

        db = self.get_db_connection('db2')
        cursor = db.cursor()
        cursor.execute("DELETE FROM count;")
        db.commit()
        db.close()

    def test_inserts(self):
        proxysql = self.get_proxysql_db_connection()
        proxysql.autocommit(False)
        cursor = proxysql.cursor()

        db1 = self.get_db_connection('db1')
        db2 = self.get_db_connection('db2')

        db_cursors = {
            'db1': db1.cursor(),
            'db2': db2.cursor()
        }

        db_values_inserted = {
            'db1': [],
            'db2': []
        }
        values_inserted = []


        transaction_db = self.get_proxysql_backend_db()
        print("Transaction started with db: %s" % transaction_db)

        for i in range(30):
            cursor.execute('INSERT INTO count VALUES (%s);', (i,))
            values_inserted.append((i,))
            if (i + 1) % 10 == 0:
                proxysql.commit()
                print("Values inserted in transaction: %s" % values_inserted)
                db_cursors[transaction_db].execute("SELECT * FROM count;")
                results = db_cursors[transaction_db].fetchall()
                print("Data in 'count' table in transaction db: %s\n%s" % (transaction_db, results))
                db_values_inserted[transaction_db].extend(values_inserted)
                values_inserted = []
                transaction_db = self.get_proxysql_backend_db()
                print("Transaction started with db: %s" % transaction_db)
            if (i + 1) % 5 == 0 and (i + 1) % 2 != 0:
                self.switch_proxysql_backend()
                print("Runtime backend db changed to: %s" % self.get_proxysql_backend_db())
            time.sleep(1)

        self.assertEqual(db_values_inserted['db1'], self.get_count_rows_for_db('db1'))
        self.assertEqual(db_values_inserted['db2'], self.get_count_rows_for_db('db2'))

        db1.close()
        db2.close()
        proxysql.close()

    def get_count_rows_for_db(self, host):
        db = self.get_db_connection(host)
        cursor = db.cursor()
        cursor.execute("SELECT * FROM count;")
        return list(cursor.fetchall())

    def print_proxysql_runtime_config(self):
        db = self.get_proxysql_admin_connection()
        cursor = db.cursor()
        cursor.execute('select default_hostgroup from runtime_mysql_users;')
        print cursor.fetchall()
        cursor.execute('select destination_hostgroup from runtime_mysql_query_rules;')
        print cursor.fetchall()

    def get_proxysql_backend_db(self):
        db = self.get_proxysql_admin_connection()
        cursor = db.cursor()
        cursor.execute("SELECT destination_hostgroup FROM runtime_mysql_query_rules WHERE username=%s;", ('sbtest1',))
        destination_hostgroup = cursor.fetchall()[0][0]
        cursor.execute("SELECT hostname FROM runtime_mysql_servers WHERE hostgroup_id=%s", (destination_hostgroup,))
        return cursor.fetchall()[0][0]

    def switch_proxysql_backend(self):
        db = self.get_proxysql_admin_connection()
        cursor = db.cursor()
        cursor.execute("SELECT destination_hostgroup,apply FROM mysql_query_rules WHERE username=%s;", ('sbtest1',))
        rows =  cursor.fetchall()
        destination_hostgroup = rows[0][0]
        if destination_hostgroup == '10':
            destination_hostgroup = '20'
        else:
            destination_hostgroup = '10'
        cursor.execute("UPDATE mysql_query_rules SET destination_hostgroup=%s WHERE username=%s;", (destination_hostgroup, 'sbtest1'))
        cursor.execute("LOAD MYSQL QUERY RULES TO RUNTIME;")

