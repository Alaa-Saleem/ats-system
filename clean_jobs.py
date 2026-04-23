import sqlite3

def clean_db():
    conn = sqlite3.connect('db.sqlite3')
    cur = conn.cursor()
    cur.execute("DELETE FROM jobs_job")
    conn.commit()
    print("Deleted all jobs")

if __name__ == "__main__":
    clean_db()
