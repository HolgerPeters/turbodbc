import pytest
import six

from turbodbc import connect, InterfaceError, Error

from helpers import for_one_database, get_credentials, open_cursor
from query_fixture import query_fixture


@for_one_database
def test_new_cursor_properties(dsn, configuration):
    connection = connect(dsn, **get_credentials(configuration))
    cursor = connection.cursor()

    # https://www.python.org/dev/peps/pep-0249/#rowcount
    assert cursor.rowcount == -1
    assert None == cursor.description
    assert cursor.arraysize == 1


@for_one_database
def test_closed_cursor_raises_when_used(dsn, configuration):
    connection = connect(dsn, **get_credentials(configuration))
    cursor = connection.cursor()

    cursor.close()

    with pytest.raises(InterfaceError):
        cursor.execute("SELECT 42")

    with pytest.raises(InterfaceError):
        cursor.executemany("SELECT 42")

    with pytest.raises(InterfaceError):
        cursor.executemanycolumns("SELECT 42", [])

    with pytest.raises(InterfaceError):
        cursor.fetchone()

    with pytest.raises(InterfaceError):
        cursor.fetchmany()

    with pytest.raises(InterfaceError):
        cursor.fetchall()

    with pytest.raises(InterfaceError):
        six.next(cursor)


@for_one_database
def test_closing_twice_does_not_raise(dsn, configuration):
    connection = connect(dsn, **get_credentials(configuration))
    cursor = connection.cursor()

    cursor.close()
    cursor.close()


@for_one_database
def test_open_cursor_without_result_set_raises(dsn, configuration):
    connection = connect(dsn, **get_credentials(configuration))
    cursor = connection.cursor()

    with pytest.raises(InterfaceError):
        cursor.fetchone()


@for_one_database
def test_setinputsizes_does_not_raise(dsn, configuration):
    """
    It is legal for setinputsizes() to do nothing, so anything except
    raising an exception is ok
    """
    cursor = connect(dsn, **get_credentials(configuration)).cursor()
    cursor.setinputsizes([10, 20])


@for_one_database
def test_setoutputsize_does_not_raise(dsn, configuration):
    """
    It is legal for setinputsizes() to do nothing, so anything except
    raising an exception is ok
    """
    cursor = connect(dsn, **get_credentials(configuration)).cursor()
    cursor.setoutputsize(1000, 42) # with column
    cursor.setoutputsize(1000, column=42) # with column
    cursor.setoutputsize(1000) # without column


@for_one_database
def test_rowcount_is_reset_after_execute_raises(dsn, configuration):
    with open_cursor(configuration) as cursor:
        with query_fixture(cursor, configuration, 'INSERT INTEGER') as table_name:
            cursor.execute("INSERT INTO {} VALUES (?)".format(table_name), [42])
            assert cursor.rowcount == 1
            with pytest.raises(Error):
                cursor.execute("this is not even a valid SQL statement")
            assert cursor.rowcount == -1


@for_one_database
def test_rowcount_is_reset_after_executemany_raises(dsn, configuration):
    with open_cursor(configuration) as cursor:
        with query_fixture(cursor, configuration, 'INSERT INTEGER') as table_name:
            cursor.execute("INSERT INTO {} VALUES (?)".format(table_name), [42])
            assert cursor.rowcount == 1
            with pytest.raises(Error):
                cursor.executemany("this is not even a valid SQL statement")
            assert cursor.rowcount == -1


@for_one_database
def test_rowcount_is_reset_after_executemanycolumns_raises(dsn, configuration):
    with open_cursor(configuration) as cursor:
        with query_fixture(cursor, configuration, 'INSERT INTEGER') as table_name:
            cursor.execute("INSERT INTO {} VALUES (?)".format(table_name), [42])
            assert cursor.rowcount == 1
            with pytest.raises(Error):
                cursor.executemanycolumns("this is not even a valid SQL statement", [])
            assert cursor.rowcount == -1


@for_one_database
def test_connection_does_not_strongly_reference_cursors(dsn, configuration):
    connection = connect(dsn, **get_credentials(configuration))
    cursor = connection.cursor()
    import sys
    assert sys.getrefcount(cursor) == 2
