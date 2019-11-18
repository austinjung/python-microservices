# Use an official Python runtime as a base image
FROM python:3.6.9

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD ./microservices /app
ADD requirements.txt /app
ADD pip.conf /app
ADD tkn.yaml /app
RUN mkdir -p /etc/app/cfg
COPY tkn.yaml /etc/app/cfg

# Expose the port uWSGI will listen on
EXPOSE 3000

# Define environment variable
ENV FLASK_ENV=development
ENV FLASK_DEBUG=1
ENV API_TOKEN=python-microservices-key
ENV PIP_CONFIG_FILE /app/pip.conf
ENV PYTHONPATH "${PYTHONPATH}:/app"

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

CMD python app.py