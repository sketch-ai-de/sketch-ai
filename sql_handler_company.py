from sqlalchemy import MetaData, Table, insert, select

from sql_handler_base import SQLHandlerBase


class SQLHandlerCompany(SQLHandlerBase):
    def get_id(self, name):
        name_id = None
        with self._engine.connect() as connection:
            connection.commit()
            metadata = MetaData()
            table = Table(self._table_name, metadata, autoload_with=self._engine)
            stmt = select(table.c.id).where(table.c.company_name == name)
            with self._engine.connect() as conn:
                name_id = conn.execute(stmt).fetchall()

        return name_id[0][0] if name_id else None

    def insert_into_sql(self, insert_dict):
        stmt = insert(self._sql_table).values(**insert_dict)
        with self._engine.connect() as connection:
            cursor = connection.execute(stmt)
            connection.commit()
