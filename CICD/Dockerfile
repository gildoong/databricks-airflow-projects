# 에어플로우 이미지를 나타낸다.
FROM apache/airflow:3.0.2-python3.11

COPY ./Dags/ /opt/airflow/dags/

COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt