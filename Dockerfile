FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl gnupg \
 && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
 && apt-get install -y nodejs \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 6274

CMD ["npx", "@modelcontextprotocol/inspector", "python", "main.py"]
