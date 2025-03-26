import pymysql

timeout = 10
connection = pymysql.connect(
    charset="utf8mb4",
    connect_timeout=timeout,
    cursorclass=pymysql.cursors.DictCursor,
    db="defaultdb",
    host="mysql-151c6473-derilwijdan346-01bf.c.aivencloud.com",  # Replace with your actual host
    password="AVNS_L4xQhcY1pkLgZ4RrbCN",  # Replace with your actual password
    read_timeout=timeout,
    port=13906,  # Replace with your actual port
    user="avnadmin",  # Replace with your actual username
    write_timeout=timeout,
)

try:
    cursor = connection.cursor()
    # Create a table
    cursor.execute("CREATE TABLE mytest (id INTEGER PRIMARY KEY)")
    # Insert some values
    cursor.execute("INSERT INTO mytest (id) VALUES (1), (2)")
    # Fetch the inserted data
    cursor.execute("SELECT * FROM mytest")
    # Print the result
    print(cursor.fetchall())
finally:
    connection.close()
