# python-microservices
simple microservices

Your task is to build a simple microservice using the Python Flask framework.  This microservice should be responsible for uploading and downloading typical types of files (txt, pdf, png, jpg, etc.).

## Requirements

1. /upload
    Uploads one file at a time.  Feel free to define what the payload looks like.  You can go ahead and persist the files to the filesystem somewhere.

2. /download
    Retrieves and downloads a single file, using the filename as the key.

3. We will be looking at understanding of web services fundamentals, including usage of appropriate error response — you should force a failure condition to demonstrate.  We will also be looking more broadly at Python code structure, layout, and other best practices.  Feel free to incorporate whatever else you feel appropriate and feasible.  Finally, please provide a way to install dependencies and run/test the app.

## Design

1. `/` will redict to `/upload`.
    - This page will list all uploaded files. And you can upload a file using UI.
    - Or you can use curl to upload a file.
    ```
    curl -i -X POST -H "Content-Type: multipart/form-data" -F "file=@/path/to/file/sample.pdf" http://localhost:5000/upload
    ```
    
2. When file upload fails, the error will show and a link to `upload` will be provided

3. Upload file 


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
