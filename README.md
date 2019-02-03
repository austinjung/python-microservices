# python-microservices
simple microservices
# AsyncProxy - Python Programming Task

Your task is to build a simple microservice using the Python Flask framework.  This microservice should be responsible for uploading and downloading typical types of files (txt, pdf, png, jpg, etc.).

## Requirements

1. /upload
  * Uploads one file at a time.  Feel free to define what the payload looks like.  You can go ahead and persist the files to the filesystem somewhere.

2. /download
  * Retrieves and downloads a single file, using the filename as the key.

3. We will be looking at understanding of web services fundamentals, including usage of appropriate error response — you should force a failure condition to demonstrate.  We will also be looking more broadly at Python code structure, layout, and other best practices.  Feel free to incorporate whatever else you feel appropriate and feasible.  Finally, please provide a way to install dependencies and run/test the app.

## Design

1. I built a simple AsyncProxy server based on [aiohttp](http://aiohttp.readthedocs.io/en/stable/). The reasons are:
    - aiohttp is based on [asyncio — Asynchronous I/O, event loop, coroutines and tasks module og python 3.4+](https://docs.python.org/3.6/library/asyncio.html#module-asyncio)
    - aiohttp supports both Client and HTTP Server. 
    - aiohttp supports both Server WebSockets and Client WebSockets out-of-the-box.
    - aiohttp Web-server has Middlewares, Signals and pluggable routing.
    
2. The default proxy target server is set to http://youtube.com
    - Browsing **http://localhost:8080** will response with the content of **http://youtube.com**
    - Browsing **http://localhost:8080/stats** will give **the current stats of the AsyncProxy server**.
    - Browsing **http://localhost:8080/?target_url=http://python.org** will **change proxy target to python.org** and response with the content of http://python.org 


## Deployment

1. This project repository is [https://bitbucket.org/austinjung/asyncproxyinpython](https://bitbucket.org/austinjung/asyncproxyinpython)
2. The project repository is linked with [Austin's Docker Cloud](https://cloud.docker.com/swarm/austinjung/repository/registry-1.docker.io/austinjung/async-http-proxy-python/general)
3. In your docker, run the following line.
    ```
    $ docker run -p 8080:8080 austinjung/async-http-proxy-python:latest
    ```
    or 
    ```
    clone the project repository
    cd /to/the_top_folder_of_the_project
    $ docker-compose up
    ```

## Things do-to

1. Some images or contents are blocked by 'Referrer Policy: no-referrer-when-downgrade', 'Access-Control-Allow_Origin', or 'cross-origin frame' etc.
2. Do proper post method.
and more
