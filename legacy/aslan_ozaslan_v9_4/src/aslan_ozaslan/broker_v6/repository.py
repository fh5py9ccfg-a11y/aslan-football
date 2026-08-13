import sqlite3,json
from pathlib import Path
class InboxOutboxRepository:
    def __init__(self,path): self.path=str(path); self._init()
    def con(self): c=sqlite3.connect(self.path); c.row_factory=sqlite3.Row; return c
    def _init(self):
        with self.con() as c:c.executescript("""CREATE TABLE IF NOT EXISTS inbox(topic TEXT,partition_id INT,offset_id INT,key TEXT,payload TEXT,status TEXT,error TEXT,PRIMARY KEY(topic,partition_id,offset_id));CREATE TABLE IF NOT EXISTS outbox(id INTEGER PRIMARY KEY AUTOINCREMENT,topic TEXT,key TEXT,payload TEXT,headers TEXT,published INT DEFAULT 0);CREATE TABLE IF NOT EXISTS dead_letter(id INTEGER PRIMARY KEY AUTOINCREMENT,topic TEXT,partition_id INT,offset_id INT,key TEXT,payload TEXT,error TEXT);""")
    def begin(self,m):
        try:
            with self.con() as c:c.execute('INSERT INTO inbox VALUES(?,?,?,?,?,?,NULL)',(m.topic,m.partition,m.offset,m.key,json.dumps(m.value),'PROCESSING'))
            return True
        except sqlite3.IntegrityError:return False
    def complete(self,m,items):
        with self.con() as c:
            c.execute("UPDATE inbox SET status='COMPLETED',error=NULL WHERE topic=? AND partition_id=? AND offset_id=?",(m.topic,m.partition,m.offset))
            for i in items:c.execute('INSERT INTO outbox(topic,key,payload,headers) VALUES(?,?,?,?)',(i['topic'],i['key'],json.dumps(i['value']),json.dumps(i.get('headers',{}))))
    def fail(self,m,e):
        with self.con() as c:
            c.execute("UPDATE inbox SET status='FAILED',error=? WHERE topic=? AND partition_id=? AND offset_id=?",(e,m.topic,m.partition,m.offset)); c.execute('INSERT INTO dead_letter(topic,partition_id,offset_id,key,payload,error) VALUES(?,?,?,?,?,?)',(m.topic,m.partition,m.offset,m.key,json.dumps(m.value),e))
    def pending(self):
        with self.con() as c:r=c.execute('SELECT * FROM outbox WHERE published=0 ORDER BY id').fetchall()
        return [dict(id=x['id'],topic=x['topic'],key=x['key'],value=json.loads(x['payload']),headers=json.loads(x['headers'])) for x in r]
    def mark(self,i):
        with self.con() as c:c.execute('UPDATE outbox SET published=1 WHERE id=?',(i,))
    def counts(self):
        with self.con() as c:return {'inbox':c.execute('SELECT COUNT(*) FROM inbox').fetchone()[0],'completed':c.execute("SELECT COUNT(*) FROM inbox WHERE status='COMPLETED'").fetchone()[0],'dead_letter':c.execute('SELECT COUNT(*) FROM dead_letter').fetchone()[0],'pending_outbox':c.execute('SELECT COUNT(*) FROM outbox WHERE published=0').fetchone()[0]}
