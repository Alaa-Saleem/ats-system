import sqlite3

def check_db():
    conn = sqlite3.connect('db.sqlite3')
    cur = conn.cursor()
    cur.execute("SELECT * FROM jobs_job")
    rows = cur.fetchall()
    print("JOB COUNT:", len(rows))
    print(rows)

if __name__ == "__main__":
    check_db()
