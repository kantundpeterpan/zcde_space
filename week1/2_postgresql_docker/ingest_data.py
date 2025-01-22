import pandas as pd
import time

import argparse
from sqlalchemy import create_engine

def main(params):
    
    user = params.user
    password = params.password
    host = params.host
    port = params.port
    db = params.db
    table_name = params.table_name
    url = params.url
    
    engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{db}")

    df_iter = pd.read_csv(url,
                    iterator = True, chunksize=100000,
                    parse_dates=['tpep_pickup_datetime', 'tpep_dropoff_datetime'])

    while (tmp_df := next(df_iter, None)) is not None:

        start = time.time()

        tmp_df.to_sql(name = table_name, con=engine, if_exists='append')

        end = time.time()

        print("Check ... took %.3f seconds" % (end - start))


if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description="Ingest CSV data to Postgres")
    
    parser.add_argument('--password', help='password name for Postgres')
    parser.add_argument('--host', help='host for Postgres')
    parser.add_argument('--port', help='port for Postgres')
    parser.add_argument('--db', help='database for Postgres')
    parser.add_argument('--user', help='user name for Postgres')
    parser.add_argument('--table_name', help='name of the db table data will be written to')
    parser.add_argument('--url', help='url of the csv file')

    args = parser.parse_args()
    main(args)