# Databricks notebook source
# df = (
#     spark.read.format("xml")
#     .option("rootTag","posts")
#     .option("rowTag","row")
#     .option("inferSchema","True")
#     .load("/Volumes/my_workspace/default/my_volume/Posts.xml")    
# )

# COMMAND ----------

# display(df.limit(10))

# COMMAND ----------

#df.printSchema()

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, LongType, StringType, TimestampType

schema = StructType([
    StructField("_AcceptedAnswerId", LongType(), True),
    StructField("_AnswerCount", LongType(), True),
    StructField("_Body", StringType(), True),
    StructField("_ClosedDate", TimestampType(), True),
    StructField("_CommentCount", LongType(), True),
    StructField("_CommunityOwnedDate", TimestampType(), True),
    StructField("_ContentLicense", StringType(), True),
    StructField("_CreationDate", TimestampType(), True),
    StructField("_FavoriteCount", LongType(), True),
    StructField("_Id", LongType(), True),
    StructField("_LastActivityDate", TimestampType(), True),
    StructField("_LastEditDate", TimestampType(), True),
    StructField("_LastEditorDisplayName", StringType(), True),
    StructField("_LastEditorUserId", LongType(), True),
    StructField("_OwnerDisplayName", StringType(), True),
    StructField("_OwnerUserId", LongType(), True),
    StructField("_ParentId", LongType(), True),
    StructField("_PostTypeId", LongType(), True),
    StructField("_Score", LongType(), True),
    StructField("_Tags", StringType(), True),
    StructField("_Title", StringType(), True),
    StructField("_ViewCount", LongType(), True)
])

# COMMAND ----------

df = (
    spark.read.format("xml")
    .option("rootTag","posts")
    .option("rowTag","row")
    .schema(schema) # 속도가 더 빨라진다.
    .load("/Volumes/my_workspace/default/my_external_volume/raw/Posts.xml")    
)

# COMMAND ----------

#칼럼 이름 앞 "_" 제거
new_column_names = [col[1:] for col in df.columns]
df = df.toDF(*new_column_names)

# COMMAND ----------

df.write.mode("overwrite").option("overwriteSchema","true").saveAsTable("raw_posts")