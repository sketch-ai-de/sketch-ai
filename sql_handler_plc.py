from sqlalchemy import insert

from sql_handler_base import SQLHandlerBase


class SQLHandlerPLC(SQLHandlerBase):
    def insert_into_sql(self, insert_dict):
        _tmp_description_long = ""
        for dev_key in insert_dict.keys():
            _tm_tmp_description_longp = (
                _tmp_description_long
                + "\n"
                + str(dev_key)
                + ": "
                + str(insert_dict[dev_key])
            )
        insert_dict["product_description_long"] = _tmp_description_long
        insert_dict["product_description"] = (
            "Company name: "
            + insert_dict["company_name"]
            + "\n"
            + "Product name: "
            + insert_dict["product_name"]
            + "\n"
            + "Article number: "
            + insert_dict["article_number"]
            + "\n"
            + "Product description: "
            + insert_dict["product_description"]
            + "\n"
            + "Mandatory additional components: "
            + insert_dict["must_have_components"]
        )
        stmt = insert(self._sql_table).values(**insert_dict)
        with self._engine.connect() as connection:
            cursor = connection.execute(stmt)
            connection.commit()
