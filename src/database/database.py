import sqlite3


class Sqlite:
    def __init__(self, db_file="./data/anime.db", check_same_thread=False):
        c = self.conn = sqlite3.connect(db_file, check_same_thread=check_same_thread)

        c.execute('''CREATE TABLE IF NOT EXISTS preference (
	anime_name text,
	anime_id INTEGER,
	release_group text,
	uncensored BOOLEAN,
	last_episode INTEGER,
	folder_path text,
	CONSTRAINT preferrence_PK PRIMARY KEY (anime_id)
);
''')

    def insert(self, table, data):
        value = ""
        for v in data.values():
            if isinstance(v, (int, float)):
                value += f"{v},"
            else:
                v = str(v).replace("'", "''")
                value += f"'{v}',"

        sql = f"INSERT or REPLACE INTO {table} ({','.join(data.keys())}) VALUES ({value[:-1]})"
        self.conn.cursor().execute(sql)
        self.conn.commit()

    def delete(self, table, data):
        condition = []
        for key, value in data.items():
            condition.append(f"{key} = '{value}'")
        # Required condition, throw error if condition doesnt included
        sql = f"DELETE FROM {table} WHERE "
        sql += " AND ".join(condition)

        self.conn.cursor().execute(sql)
        self.conn.commit()

    def select(self, table, data) -> list:
        condition = []
        for key, value in data.items():
            condition.append(f"{key} = '{value}'")
        # Required condition, throw error if condition doesnt included
        sql = f"SELECT * FROM {table}"
        if condition:
            sql += " WHERE "
            sql += " AND ".join(condition)
        # need to create instance so we have something to return from the sql
        c = self.conn.cursor()
        c.execute(sql)
        result = []

        col_names = [tup[0] for tup in c.description]
        for row in c.fetchall():
            result.append(dict(zip(col_names, row)))
        return result
