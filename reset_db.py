import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

conn = psycopg2.connect(dbname='postgres', user='postgres', password='123456', host='localhost')
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()

try:
    cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'ats_db'")
    cur.execute('DROP DATABASE ats_db;')
    print('Dropped ats_db.')
except Exception as e:
    print('Drop failed:', e)

cur.execute('CREATE DATABASE ats_db;')
print('Created ats_db.')

cur.close()
conn.close()
