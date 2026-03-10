# Databricks notebook source
# 가장 많이 사용된 태그가 무엇인지 계산하고자 한다.
stg_posts_df = spark.table("default.stg_posts")

# COMMAND ----------

from pyspark.sql import DataFrame
import pyspark.sql.functions as F

def posts_top_tags(stg_posts_df: DataFrame) -> DataFrame:
    return(
        stg_posts_df
        .withColumn("tag_exploded", F.explode("TagArray"))
        .groupBy("tag_exploded").agg(F.approx_count_distinct("PostId").alias("tags_count"))
        .orderBy(F.col("tags_count").desc())
    )

marts_top_tags_df = posts_top_tags(stg_posts_df)
marts_top_tags_df.write.mode("overwrite").saveAsTable("marts_top_tags")

# COMMAND ----------

display(spark.table("marts_top_tags").limit(5))

# COMMAND ----------

