# Databricks notebook source
stg_posts_df = spark.table("default.stg_posts")
raw_users_df = spark.table("default.raw_users")

# COMMAND ----------

# DBTITLE 1,Create a One Big Table
from pyspark.sql import DataFrame
import pyspark.sql.functions as F

def posts_users_OBT(stg_posts_df: DataFrame, raw_users_df: DataFrame) -> DataFrame:
    """
    This function joins the stg_posts and raw_users tables on the OwnerUserId column.
    """
    return (stg_posts_df
        .alias("posts")
        .withColumnRenamed("CreationDate", "PostCreationDate")
        .join(
            other = raw_users_df
                .withColumnRenamed("CreationDate", "UserCreationDate")
                .alias("users"),
            on=F.col("posts.OwnerUserId") == F.col("users.Id"),
            how = "left"
        )
    )

marts_posts_user_df = posts_users_OBT(stg_posts_df, raw_users_df)


# COMMAND ----------

marts_posts_user_df.write.mode("overwrite").saveAsTable("marts_posts_users")

# COMMAND ----------

display(spark.table("default.marts_posts_users").limit(3))

# COMMAND ----------

