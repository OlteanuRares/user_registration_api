# user registration api

### System requirements

    docker
    docker-compose

### Basic project setup

* `git clone git@github.com:OlteanuRares/user_registration_api.git`

* `cd user_registration_api`

* run the initial project setup :
    `docker-compose build`

* startup:
    `docker-compose up`
    
* for using django admin you'll have to manually do a :
    `docker-compose exec web django-admin.py createsuperuser`

* for accessing the admin app in browser go to 
     `http://localhost:8000/admin/`
  and use the credentials generated on creating the supersuser

* bash in web container
   `docker-compose exec web  bash`

* to run the tests on local environment run:
    `docker-compose run --rm web pytest tests/`

### Usage
The application has two endpoints:
1) localhost:8000/api/v1/sign_up/

  `curl --location --request POST 'localhost:8000/api/v1/sign_up/' \
   --header 'Content-Type: application/json' \
   --data-raw '{
        "email": "<your_email>",
        "password": "<your password>"
       }`

2) localhost:8000/api/v1/activate/

`curl --location --request PATCH 'localhost:8000/api/v1/activate/' \
-u '<your_email>:<your_password>' \
--header 'Content-Type: application/json' \
--data-raw '{
    "token": "<received token>"
}`

A rest client such as insomnia or postman can be used to send these requests
