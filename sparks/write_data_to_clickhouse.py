from pyspark.sql.functions import *
from pyspark.sql.types import *
from config.spark_config import SparkConnect
from spark_write_database import SparkWriteDatabase
import os
from config.spark_config import get_spark_config

def main():
    jar_packages = [
        "com.clickhouse:clickhouse-jdbc:0.6.4",
        "org.apache.httpcomponents.client5:httpclient5:5.3.1",
        "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0",
        # "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.1"  # ← thêm dòng này

    ]
    
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

    spark_config = get_spark_config()       

    # Config params for spark_connect
    spark_connect = SparkConnect(
        app_name="thanhdz",
        master_url="spark://spark-master:7077",
        executor_cores=2,
        executor_memory="1g",
        driver_memory="2g",
        num_executors=1,
        jar_packages=jar_packages,
        # spark_conf=spark_config,
        log_level="WARN"
    )

    # Initial spark
    spark = spark_connect.spark

    # =========================================PROCESSING FOR ORDER_ITEMS=========================================
    # Scheme of cdc debezium
    schema_order_items = StructType([
        StructField("id", IntegerType()),
        StructField("order_id", IntegerType()),
        StructField("name", StringType()),
        StructField("brand", StringType()),
        StructField("price", IntegerType()),
        StructField("quantity", IntegerType()),
    ])

    # Overview schema of message CDC
    schema_payload_order_items = StructType([
        StructField("before", schema_order_items),
        StructField("after", schema_order_items),
        StructField("op", StringType()),     # operation: c, u, d
        StructField("ts_ms", LongType()) # <-- ts_ms nên là LongType (milliseconds)
        # StructField("ts_ms", StringType())   # timestamp in milliseconds
    ])
    
    kafka_df_order_items = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", bootstrap_servers) \
        .option("subscribe", "order_cdc.order_streaming.order_items") \
        .option("startingOffsets", "earliest") \
        .load()
    
    df_parsed_order_items = kafka_df_order_items.select(
        from_json(col("value").cast(StringType()), StructType([
            StructField("payload", schema_payload_order_items)
        ])).alias("data")
    ).select("data.payload.*") # Lấy trực tiếp các trường trong payload

    df_final_order_items_ch = df_parsed_order_items.select(
        # cloalesce => Return first value != null
        coalesce(col("after.id"), col("before.id")).alias("id"),
        
        # Orther column: Get infor from 'before' if op='d', 'after' if op='c/u'
        when(col("op") == "d", col("before.order_id")).otherwise(col("after.order_id")).alias("order_id"),
        when(col("op") == "d", col("before.name")).otherwise(col("after.name")).alias("name"),
        when(col("op") == "d", col("before.brand")).otherwise(col("after.brand")).alias("brand"),
        when(col("op") == "d", col("before.price")).otherwise(col("after.price")).alias("price"),
        when(col("op") == "d", col("before.quantity")).otherwise(col("after.quantity")).alias("quantity"),
        
        col("op"),
        (col("ts_ms") / 1000).cast(TimestampType()).alias("ts_ms"), # Chuyển ts_ms sang DateTime64(3)
        when(col("op") == "d", lit(1)).otherwise(lit(0)).alias("_is_deleted")
    ).filter(col("id").isNotNull()) # <-- RẤT QUAN TRỌNG: Lọc bỏ bất kỳ hàng nào có ID là NULL

    df_write_to_order_items = SparkWriteDatabase(spark, spark_config)

    query_order_items = df_final_order_items_ch.writeStream \
        .foreachBatch(lambda df, epoch_id: df_write_to_order_items.spark_write_clickhouse(
            df=df,
            table_name="order_items_cdc",
            jdbc_url=spark_config["clickhouse"]["jdbc_url"],
            mode="append" # Luôn dùng "append" cho CDC với ReplacingMergeTree
        )) \
        .option("checkpointLocation", "/opt/checkpoints/order_items_cdc") \
        .start()

    # =========================================PROCESSING FOR ORDERS=========================================
    # Scheme of cdc debezium
    schema_orders = StructType([
        StructField("id", IntegerType()),
        StructField("created_at", LongType())
    ])

    # Overview schema of message CDC
    schema_payload_orders = StructType([
        StructField("before", schema_orders),
        StructField("after", schema_orders),
        StructField("op", StringType()),     # operation: c, u, d
        StructField("ts_ms", LongType()) # <-- ts_ms nên là LongType (milliseconds)
    ])


    kafka_df_orders = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", bootstrap_servers) \
        .option("subscribe", "order_cdc.order_streaming.orders") \
        .option("startingOffsets", "earliest") \
        .load()
    
    df_parsed_orders = kafka_df_orders.select(
        from_json(col("value").cast(StringType()), StructType([
            StructField("payload", schema_payload_orders)
        ])).alias("data")
    ).select("data.payload.*") # Lấy trực tiếp các trường trong payload

    df_final_orders_ch = df_parsed_orders.select(
        # cloalesce => Return first value != null
        coalesce(col("after.id"), col("before.id")).alias("id"),
        when(col("op") == 'd', col("before.created_at")).otherwise(col("after.created_at")).alias("created_at"), 
        col("op"),
        (col("ts_ms") / 1000).cast(TimestampType()).alias("ts_ms"), # Chuyển ts_ms sang DateTime64(3)
        when(col("op") == "d", lit(1)).otherwise(lit(0)).alias("_is_deleted")
    ).filter(col("id").isNotNull()) # <-- RẤT QUAN TRỌNG: Lọc bỏ bất kỳ hàng nào có ID là NULL

    df_write_to_orders = SparkWriteDatabase(spark, spark_config)

    query_orders = df_final_orders_ch.writeStream \
        .foreachBatch(lambda df, epoch_id: df_write_to_orders.spark_write_clickhouse(
            df=df,
            table_name="orders_cdc",
            jdbc_url=spark_config["clickhouse"]["jdbc_url"],
            mode="append" # Luôn dùng "append" cho CDC với ReplacingMergeTree
        )) \
        .option("checkpointLocation", "/opt/checkpoints/orders_cdc") \
        .start()

    query_orders.awaitTermination()

    # Stop spark_session
    spark_connect.stop()

if __name__ == "__main__":
    main()
