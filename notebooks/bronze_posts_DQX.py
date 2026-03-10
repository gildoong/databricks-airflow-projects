# Databricks notebook source
# MAGIC %pip install databricks-labs-dqx

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

raw_posts_df = spark.read.table("default.raw_posts")

# COMMAND ----------

from databricks.labs.dqx import check_funcs
from databricks.labs.dqx.engine import DQEngine
from databricks.labs.dqx.rule import DQRowRule, DQForEachColRule
from databricks.sdk import WorkspaceClient

dq_engine = DQEngine(WorkspaceClient())

checks = [
    *DQForEachColRule(
        columns=["Id","CreationDate"],
        criticality="error",
        check_func = check_funcs.is_not_null
    ).get_rules(),
    DQRowRule(
        name="creation_date_not_in_future",
        criticality="error",
        check_func = check_funcs.is_not_in_future,
        column="CreationDate"
    ),
    DQRowRule(
        name ="post_type_id_allowed_values",
        criticality="error",
        check_func = check_funcs.is_in_list,
        column="PostTypeId",
        check_func_kwargs={"allowed" : ["1","2","3","4"]}
    )
]

valid_df, quarantined_df = dq_engine.apply_checks_and_split(raw_posts_df, checks)


# COMMAND ----------

display(quarantined_df.limit(3))

# COMMAND ----------

