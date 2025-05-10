# Use official Python image
FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y git
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Clone the Zeeguu repo
RUN git clone https://github.com/zeeguu/API.git /app/zeeguu-api

COPY dependency_graph.py /app/dependency_graph.py

WORKDIR /app

CMD ["python", "dependency_graph.py"]
