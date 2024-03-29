from sqlalchemy import MetaData, Table, insert, select

from sql_handler_base import SQLHandlerBase


class SQLHandlerRobotArm(SQLHandlerBase):
    def get_id(self, name):
        id = None
        with self._engine.connect() as connection:
            connection.commit()
            metadata = MetaData()
            table = Table(self._table_name, metadata, autoload_with=self._engine)
            stmt = select(table.c.id).where(table.c.product_name == name)
            with self._engine.connect() as conn:
                id = conn.execute(stmt).fetchall()

        return id[0][0] if id else None

    def insert_into_sql(self, device_info):
        for dev_key in device_info.keys():
            device_info["product_description"] = (
                device_info["product_description"]
                + "\n"
                + str(dev_key)
                + ": "
                + str(device_info[dev_key])
            )

        stmt = insert(self._sql_table).values(**device_info)
        with self._engine.connect() as connection:
            cursor = connection.execute(stmt)
            connection.commit()
