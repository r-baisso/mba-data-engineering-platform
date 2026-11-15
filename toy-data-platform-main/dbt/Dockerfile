FROM python:3.11.11-slim
RUN pip install dbt-core==1.12.6 dbt-trino==1.10.6
WORKDIR /usr/app/movies_transform
COPY movies_transform /usr/app/movies_transform
