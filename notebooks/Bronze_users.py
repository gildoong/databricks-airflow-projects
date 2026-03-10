# Databricks notebook source
# df = (
#     spark.read.format("xml")
#     .option("rootTag","users")
#     .option("rowTag","row")
#     .schema(schema)
#     .load("/Volumes/my_workspace/default/my_volume/Users.xml")
# )

# COMMAND ----------

#df.printSchema()

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, StringType, LongType, TimestampType

schema = StructType([
    StructField("_AboutMe", StringType(), True),
    StructField("_AccountId", LongType(), True),
    StructField("_CreationDate", TimestampType(), True),
    StructField("_DisplayName", StringType(), True),
    StructField("_DownVotes", LongType(), True),
    StructField("_Id", LongType(), True),
    StructField("_LastAccessDate", TimestampType(), True),
    StructField("_Location", StringType(), True),
    StructField("_Reputation", LongType(), True),
    StructField("_UpVotes", LongType(), True),
    StructField("_Views", LongType(), True),
    StructField("_WebsiteUrl", StringType(), True)
])

# COMMAND ----------


df = (
    spark.read.format("xml")
    .option("rootTag","users")
    .option("rowTag","row")
    .option("inferSchema","true")
    .load("/Volumes/my_workspace/default/my_external_volume/raw/Users.xml")
)

# COMMAND ----------

new_column_names = [col[1:] for col in df.columns]
df = df.toDF(*new_column_names)

# COMMAND ----------

display(df.limit(10))

# COMMAND ----------

df.write.mode("overwrite").option("overwriteSchema","true").saveAsTable("raw_users")