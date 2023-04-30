# Python and Node.js image
FROM nikolaik/python-nodejs:python3.10-nodejs20

# Set the working directory to /app
WORKDIR /app

# Create a virtual environment in /venv directory and add it to PATH
RUN python -m venv /venv
ENV PATH /venv/bin:$PATH

# Install Python and Node.js dependencies
COPY log_parsing /app/log_parsing
COPY ./requirements.txt /app
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY ./setup.cfg /app
COPY ./pyproject.toml /app
RUN pip install -e /app/
COPY dashboard/package*.json ./dashboard/
RUN cd dashboard && npm ci


# Copy the rest of the project files into the container
COPY . .

# Run npm build
RUN cd dashboard && npm run build

CMD ["/venv/bin/python", "dashboard/app.py"]
