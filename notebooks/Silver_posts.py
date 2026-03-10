# Databricks notebook source
raw_posts_df = spark.table("default.raw_posts")

# COMMAND ----------

display(raw_posts_df.limit(10))

# COMMAND ----------

# DBTITLE 1,Declarative transmissions
import pyspark.sql.functions as F
from pyspark.sql.types import StructType, StructField, MapType, IntegerType, StringType
from pyspark.sql import DataFrame

def split_tag_into_array(df: DataFrame) -> DataFrame:
    return(
        df
        .withColumn("TagArray", F.filter(F.split(F.col("Tags"), r'\|'), lambda x: x != ""))
        .drop("Tags")
    )

def rename_columns(df: DataFrame) -> DataFrame:
    return(
        df.withColumnRenamed("Id","PostId")
    )

def map_post_type(df: DataFrame) -> DataFrame:
    map_data = [
        (1, "Question"),
        (2, "Answer"),
        (3, "Orphaned tag wiki"),
        (4, "Tag wiki excerpt"),
        (5, "Tag wiki"),
        (6, "Moderator nomination"),
        (7, "Wiki placeholder"),
        (8, "Privilege wiki"),
        (9, "Article"),
        (10, "HelpArticle"),
        (12, "Collection"),
        (13, "ModeratorQuestionnaireResponse"),
        (14, "Announcement"),
        (15, "CollectiveDiscussion"),
        (17, "CollectiveCollection")
    ]

    map_schema = StructType([
        StructField("PostTypeId", IntegerType(), False),
        StructField("PostTypeName", StringType(), False)
    ])

    map_df = spark.createDataFrame(map_data, schema=map_schema)
    return df.join(
        F.broadcast(map_df),
        df["PostTypeId"] == map_df["PostTypeId"],
        "left"
    ).drop(map_df["PostTypeId"])

stg_posts_df = (
    raw_posts_df
    .transform(split_tag_into_array)
    .transform(rename_columns)
    .transform(map_post_type)
)


# COMMAND ----------

stg_posts_df.explain()

# COMMAND ----------

display(stg_posts_df.limit(3))

# COMMAND ----------

# DBTITLE 1,Incremental Upsert
from delta.tables import DeltaTable
import pyspark.sql.functions as F
from pyspark.sql import DataFrame

def incremental_upsert(dest_table: str, df: DataFrame, unique_key: str, updated_at: str, full_refresh=False):
    """
    Performs incremental upsert using updated_at as the cursor value with unique_key 
    """

    if not spark.catalog.tableExists(dest_table) or full_refresh:
        (
            df
            .write
            .format("delta")
            .mode("overwrite")
            .option("overwriteSchema","true")
            .saveAsTable(dest_table)
        )
    else:
        last_max = (
            spark.table(dest_table)
                .agg(F.max(updated_at).alias("max_ts"))
                .collect()[0]["max_ts"]
        )

        incr_df = df.filter(F.col(updated_at) > last_max)

        # Shared cluster compatible empty check
        if incr_df.limit(1).count() > 0:
            delta_table = DeltaTable.forName(spark, dest_table)

            (
                delta_table.alias("t")
                .merge(
                    source=incr_df.alias("s"),
                    condition=f"s.{unique_key} = t.{unique_key}"
                )
                .whenMatchedUpdateAll()
                .whenNotMatchedInsertAll()
                .execute()
            )

dest_table = "default.stg_posts"

incremental_upsert(dest_table, stg_posts_df, "PostId", "CreationDate")

# COMMAND ----------

# DBTITLE 1,Optimize Spark Writes
spark.table(dest_table).selectExpr("spark_partition_id()").distinct().count()
# spark.table(dest_table).rdd.getNumPartitions()  
# Not supported in shared access mode, consider alternative methods.
# 한 스파크의 파티션 당 이상적인 크기는 약 128MB
## 스파크 작업 최적화 및 셔플링 감소 방법에 대한 자료는 많지만, 핵심은 클러스터에 있는 실행기 수 의 배수로 파티션 수를 설정하는 것이 좋다는 것이다.

# COMMAND ----------

incremental_upsert(dest_table, stg_posts_df.repartition(4), "PostId", "CreationDate", full_refresh=True)

# COMMAND ----------

spark.conf.set("spark.sql.shuffle.partitions", "4")