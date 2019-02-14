# python-microservices
simple microservices

Your task is to build a simple microservice using the Python Flask framework.  This microservice should be responsible for uploading and downloading typical types of files (txt, pdf, png, jpg, etc.).

## Requirements

1. /upload
    - Uploads one file at a time.  Feel free to define what the payload looks like.  You can go ahead and persist the files to the filesystem somewhere.

2. /download
    - Retrieves and downloads a single file, using the filename as the key.

3. We will be looking at understanding of web services fundamentals, including usage of appropriate error response.
    — You should force a failure condition to demonstrate.
    
4. We will also be looking more broadly at Python code structure, layout, and other best practices.

5. Feel free to incorporate whatever else you feel appropriate and feasible.

6. Finally, please provide a way to install dependencies and run/test the app.

## Design

1. `http://localhost:8000/` will redict to `http://localhost:8000/upload`
    - This page will list all uploaded files. And you can upload a file using UI.
    - Or you can use curl to upload a file.
    ```
    curl -i -X POST -H "Content-Type: multipart/form-data" -F "file=@/path/to/file/sample.pdf" http://localhost:8000/upload
    ```
    
2. When file upload fails, the error will show and a link to `upload` will be provided
    - The upload file should have an extension.
    - Only these extension will be allowed. `txt`, `rtf`, `doc`, `docx`, `xls`, `xlsx`, `pdf`
    - The upload file name should be unique in the download folder of server.
    - If upload file has any of the above issue, the server will show the corresponding error.

3. Upload file using API endpoint `http://localhost:8000/upload/your-upload-file-name.ext`
    - You can use curl or your program to upload file
    ```
    curl -i -X POST -H "Content-Type: application/json" --data-binary "@/Users/austinjung/Documents/sample.pdf" http://localhost:8000/upload/my_upload.pdf
    ```
    
4. You can get all file names using API `http://localhost:8000/download`
    - You can use curl or your program to get file names
    ```
    curl -i -X GET -H "Content-Type: application/json" http://localhost:8000/download
    ```
    - And the response will be
    ```json
    [
        {
            "filename": "Austin-Jung_2019_resume.pdf",
            "url": "http://localhost:8000/download/Austin-Jung_2019_resume.pdf"
        },
        {
            "filename": "sample.pdf",
            "url": "http://localhost:8000/download/sample.pdf"
        }
    ]
    ```
    
5. You can download a file using API `http://localhost:8000/download/sample.pdf`
    - You can use curl or your program to get file names
    ```
    curl -i -X GET -H "Content-Type: application/json" http://localhost:8000/download/sample.pdf --output sample.pdf
    ```

## Deployment

1. This project repository is [https://github.com/austinjung/python-microservices](https://github.com/austinjung/python-microservices)

2. The project repository is linked with [Austin's Docker Cloud](https://cloud.docker.com/repository/docker/austinjung/python-microservices/general)

3. Clone this repository
    ```
    git clone git@github.com:austinjung/python-microservices.git
    ```

3. In your docker, run the following line.
    ```
    cd python-microservices
    $ docker-compose down && docker-compose up --build -d
    ```

## Tests

1. At the project folder, run pytest
    ```
    cd python-microservices
    $ pytest
    ```

