from typing import Optional, List, Dict
from pyspark.sql import SparkSession
from config.database_config import get_database_config

class SparkConnect():
    def __init__(
            self,
            app_name: str,
            master_url: str = "local[*]",
            executor_cores: Optional[int] = 2,
            executor_memory: Optional[str] = "2g",
            driver_memory: Optional[str] = "2g",
            num_executors: Optional[int] = 2,
            jar_packages: Optional[List[str]] = None,
            spark_conf: Optional[Dict[str, str]] = None,
            log_level: str = "WARN"
    ):
        self.app_name = app_name
        self.spark = self.create_spark_session(
            master_url,
            executor_cores,
            executor_memory,
            driver_memory,
            num_executors,
            jar_packages,
            spark_conf,
            log_level
        )

    def create_spark_session(
            self,
            master_url: str = "local[*]",
            executor_cores: Optional[int] = 2,
            executor_memory: Optional[str] = "2g",
            driver_memory: Optional[str] = "2g",
            num_executors: Optional[int] = 2,
            jar_packages: Optional[List[str]] = None,
            spark_conf: Optional[Dict[str, str]] = None,
            log_level: str = "WARN"
    ) -> SparkSession:
        builder = SparkSession.builder \
            .appName(self.app_name) \
            .master(master_url) \

        if executor_memory:
            builder.config("spark.executor.memory", executor_memory)
        if executor_cores:
            builder.config("spark.executor.cores", executor_cores)
        if driver_memory:
            builder.config("spark.driver.memory", driver_memory)
        if num_executors:
            builder.config("spark.executor.instances", num_executors)

        if jar_packages:
            jar_packages_url = ",".join([jar_package for jar_package in jar_packages])
            builder.config("spark.jars.packages", jar_packages_url)

        if spark_conf:
            for key, value in spark_conf.items():
                builder.config(key, value)

        spark = builder.getOrCreate()

        spark.sparkContext.setLogLevel(log_level)
        return spark

    def stop(self):
        if self.spark:
            self.spark.stop()
            print("-------------Stop SparkSession-------------")

def get_spark_config() -> Dict:
    db_config = get_database_config()
    return {
        "clickhouse": {
            "table": db_config["clickhouse"].table,
            "jdbc_url": "jdbc:clickhouse://{}:{}/{}".format(db_config["clickhouse"].host, db_config["clickhouse"].port, db_config["clickhouse"].database),
            "config": {
                "host": db_config["clickhouse"].host,
                "port": db_config["clickhouse"].port,
                "user": db_config["clickhouse"].user,
                "password": db_config["clickhouse"].password,
                "database": db_config["clickhouse"].database
            }
        }
    }
