from typing import Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from urllib.parse import quote_plus # 用于对URL进行编码

def get_db_schema(
        db_type: str,
        host: str,
        port: int,
        database: str,
        username: str,
        password: str,
        table_names: str | None = None
) -> dict[str, Any] | None:
    """
    获取数据库表结构信息
    :param db_type: 数据库类型 (mysql/oracle/sqlserver/postgresql)
    :param host: 主机地址
    :param port: 端口号
    :param database: 数据库名
    :param username: 用户名
    :param password: 密码
    :param table_names: 要查询的表名，以逗号分隔的字符串，如果为None则查询所有表
    :return: 包含所有表结构信息的字典
    """
    result: dict[str, Any] = {}

    # 构建连接URL
    driver = {
        'mysql': 'pymysql',
        'oracle': 'cx_oracle',
        'sqlserver': 'pymssql',
        'postgresql': 'psycopg2'
    }.get(db_type.lower(), '')

    encoded_username = quote_plus(username)
    encoded_password = quote_plus(password)

    engine = create_engine(f'{db_type.lower()}+{driver}://{encoded_username}:{encoded_password}@{host}:{port}/{database}')
    inspector = inspect(engine)

    # 获取字段注释的SQL语句
    column_comment_sql = {
        'mysql': f"SELECT COLUMN_COMMENT FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = :table_name AND COLUMN_NAME = :column_name",
        'oracle': "SELECT COMMENTS FROM ALL_COL_COMMENTS WHERE TABLE_NAME = :table_name AND COLUMN_NAME = :column_name",
        'sqlserver': "SELECT CAST(ep.value AS NVARCHAR(MAX)) FROM sys.columns c LEFT JOIN sys.extended_properties ep ON ep.major_id = c.object_id AND ep.minor_id = c.column_id WHERE OBJECT_NAME(c.object_id) = :table_name AND c.name = :column_name",
        'postgresql': "SELECT col_description(:table_name::regclass, ordinal_position) FROM information_schema.columns WHERE table_name = :table_name AND column_name = :column_name"
    }.get(db_type.lower(), "")

    try:
        # 获取所有表名
        all_tables = inspector.get_table_names()

        # 如果指定了table_names，则过滤表名
        target_tables = all_tables
        if table_names:
            target_tables = [table.strip() for table in table_names.split(',')]
            # 过滤出实际存在的表
            target_tables = [table for table in target_tables if table in all_tables]

        for table_name in target_tables:
            # 获取表注释
            table_comment = ""
            try:
                table_comment = inspector.get_table_comment(table_name).get("text") or ""
            except SQLAlchemyError as e:
                raise ValueError(f"Failed to retrieve table comments: {str(e)}")

            table_info = {
                'comment': table_comment,
                'columns': []
            }

            for column in inspector.get_columns(table_name):
                # 获取字段注释
                column_comment = ""
                try:
                    with engine.connect() as conn:
                        stmt = text(column_comment_sql)
                        column_comment = conn.execute(stmt, {
                            'table_name': table_name,
                            'column_name': column['name']
                        }).scalar() or ""
                except SQLAlchemyError as e:
                    raise ValueError(f"Failed to retrieve field metadata: {str(e)}")

                table_info['columns'].append({
                    'name': column['name'],
                    'comment': column_comment,
                    'type': str(column['type'])
                })

            result[table_name] = table_info

        return result
    except SQLAlchemyError as e:
        raise ValueError(f"Failed to retrieve database table metadata: {str(e)}")
    finally:
        engine.dispose()