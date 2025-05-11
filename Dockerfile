# Use official Python image
FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y git
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Clone the Zeeguu repo
RUN git clone https://github.com/zeeguu/API.git /app/zeeguu-api

COPY dependency_graph.py /app/dependency_graph.py
COPY abstract_graph.py /app/abstract_graph.py

WORKDIR /app

# If the first call succeds run the second one
CMD python dependency_graph.py && python abstract_graph.py 
