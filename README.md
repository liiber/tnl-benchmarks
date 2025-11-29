# How to run? 
1. Go to the project folder: `cd tnl-benchmarks`
2. Run the docker compose file: `docker-compose up --build`
3. Access the **Adminer** dashboard by visiting the [link](http://0.0.0.0:8080/)

### Environment setup
Here is the example of .env file you should have:
```text
# ----------------------------
# Database credentials
# ----------------------------

# Postgres username
DB_USER=admin

# Postgres password
DB_PASSWORD=admin

# Database name
DB_NAME=tnl_benchmarks

# Database host
DB_HOST=tnl_benchmarks_db

# Database port (default 5432)
DB_PORT=5432

# ----------------------------
# Application settings
# ----------------------------

# Port for the app to run on
APP_PORT=8000
```