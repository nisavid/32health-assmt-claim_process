# 📄 claim_process

**Author**: Ivan D Vasin

**Context**: This project is a technical assessment for 32Health.

<!--toc:start-->

- [☑️ High-Level Features and Design](#readme-features)
- [🏗️ Tech Stack](#readme-tech)
- [🌀 Cloning the Repository](#readme-clone)
- [📦 Setting Up the Project with `pipenv`](#readme-pipenv)
- [🐋 Running the Services with `docker-compose`](#readme-docker)
- [✅ Running the Automated Tests with `pytest`](#readme-pytest)
- [⌨️ Manually Testing the Endpoints with `httpx`](#readme-httpx)
- [📚 Viewing the API Docs](#readme-apidocs)
- [🔄 Service Communication: claim_process and payments](#readme-interop)

<!--toc:end-->

<a id="readme-features"></a>

## ☑️ High-Level Features and Design

This project implements a FastAPI-based web service to process and manage
insurance claims. It includes the following features:

- Create and read operations for insurance claims.
- Endpoint to retrieve the top 10 provider NPIs by total net fees generated,
  with rate limiting.
- Data validation and normalization.
- Automated tests covering various scenarios.

<a id="readme-tech"></a>

## 🏗️ Tech Stack

- **FastAPI**: For building the web service.
- **SQLAlchemy**: For ORM and database interactions.
- **Pydantic**: For data validation.
- **Redis**: For rate limiting.
- **Pytest**: For automated testing.
- **Docker**: For containerization.
- **Docker Compose**: For orchestrating multi-container Docker applications.
- **HTTPX**: For making HTTP requests in tests.

<a id="readme-clone"></a>

## 🌀 Cloning the Repository

To clone the repository, run:

```sh
git clone https://github.com/nisavid/32health-assmt-claim_process claim_process
cd claim_process
```

<a id="readme-pipenv"></a>

## 📦 Setting Up the Project with `pipenv`

To set up the project, ensure you have `pipenv` installed. Then run:

```sh
pipenv install --dev
pipenv shell
```

<a id="readme-docker"></a>

## 🐋 Running the Services with `docker-compose`

To start the services using Docker Compose, ensure Docker is installed
and running. Then execute:

```sh
docker-compose up --build
```

This will start the web service, PostgreSQL, and Redis containers.

<a id="readme-pytest"></a>

## ✅ Running the Automated Tests with `pytest`

Before running the tests, ensure that `docker-compose` is up and running.
Then, in another terminal, execute:

```sh
PYTHONPATH=. pytest
```

This command will run all the tests defined in the project.

<a id="readme-httpx"></a>

## ⌨️ Manually Testing the Endpoints with `httpx`

You can use `httpx` to manually test the endpoints. Below are some
example commands:

- **Create a claim with normalized field names:**

  ```sh
  httpx http://localhost/claims -j '{
      "service_date": "2024-06-24",
      "submitted_procedure": "D1234",
      "quadrant": "UR",
      "plan_group_number": "ABC123",
      "subscriber_number": "SUB123456",
      "provider_npi": "1234567890",
      "provider_fees": 100.0,
      "member_coinsurance": 20.0,
      "member_copay": 10.0,
      "allowed_fees": 50.0
  }'
  ```

- **Create a claim with non-normalized field names:**

  ```sh
  httpx http://localhost/claims -j '{
      " Service Date ": "2024-06-24",
      "Submitted Procedure": "D1234",
      "Quadrant": "UR",
      "Plan/Group #": "ABC123",
      "Subscriber#": "SUB123456",
      "Provider NPI": "2345678901",
      "provider fees": 100.0,
      "member CoInsurance": 20.0,
      "member coPay": 10.0,
      "Allowed Fees": 50.0
  }'
  ```

- **Create multiple claims at once:**

  ```sh
  httpx http://localhost:80/claims -j '[
    {
        "service_date": "2024-06-25",
        "submitted_procedure": "D1235",
        "quadrant": "UL",
        "plan_group_number": "DEF456",
        "subscriber_number": "SUB789012",
        "provider_npi": "2345678901",
        "provider_fees": 200.0,
        "member_coinsurance": 40.0,
        "member_copay": 20.0,
        "allowed_fees": 100.0
    },
    {
        "service_date": "2024-06-26",
        "submitted_procedure": "D1236",
        "quadrant": "LL",
        "plan_group_number": "GHI789",
        "subscriber_number": "SUB345678",
        "provider_npi": "3456789012",
        "provider_fees": 300.0,
        "member_coinsurance": 60.0,
        "member_copay": 30.0,
        "allowed_fees": 150.0
    }
  ]'
  ```

- **Attempt to create a claim with invalid values:**

  ```sh
  httpx http://localhost/claims -j '{
      "service_date": "invalid-date",
      "submitted_procedure": "1234",
      "quadrant": "UR",
      "plan_group_number": "ABC123",
      "subscriber_number": "SUB123456",
      "provider_npi": "4567890123",
      "provider_fees": -100.0,
      "member_coinsurance": 20.0,
      "member_copay": 10.0,
      "allowed_fees": 50.0
  }'
  ```

- **Retrieve all claims:**

  ```sh
  httpx http://localhost/claims
  ```

- **Retrieve a particular claim:**

  ```sh
  httpx http://localhost/claims/1
  ```

- **Retrieve the top provider NPIs:**
  ```sh
  httpx http://localhost/top-provider-npis
  ```

<a id="readme-apidocs"></a>

## 📚 Viewing the API Docs

FastAPI automatically generates interactive API documentation. Once the service
is running, you can view the documentation at:

- **Swagger UI**: [http://localhost/docs](http://localhost/docs)
- **ReDoc**: [http://localhost/redoc](http://localhost/redoc)

<a id="readme-interop"></a>

## 🔄 Service Communication: claim_process and payments

To facilitate communication between `claim_process` and `payments` services,
consider the following approach:

### High-Level Design

- **Communication Mechanism**: Use a message broker like RabbitMQ or Kafka
  for asynchronous communication between services. This ensures reliability
  and scalability.
- **Transactional Integrity**: Use a two-phase commit or a saga pattern
  to ensure consistency across services. This helps in gracefully handling
  failures and unwinding steps if needed.
- **Concurrency Handling**: Utilize distributed locks or idempotency keys
  to manage concurrent requests and prevent race conditions.

### Pseudo Code

Here's some high-level pseudo code outline for integrating the `claim_process`
with `payments`:

1. **Send Claim Data to Payments Service**:

   ```python
   def send_claim_to_payments(claim_data):
       try:
           # Publish claim data to the payments topic
           publish_to_message_broker(topic="payments", message=claim_data)
       except Exception as e:
           logger.error(f"Failed to send claim data to payments: {str(e)}")
           raise
   ```

2. **Handle Payments Service Response**:

   ```python
   def handle_payment_response(response):
       try:
           if response.status == "success":
               # Update claim status to processed
               update_claim_status(claim_id=response.claim_id, status="processed")
           else:
               # Handle payment failure and update claim status
               update_claim_status(claim_id=response.claim_id, status="failed")
       except Exception as e:
           logger.error(f"Failed to handle payment response: {str(e)}")
           raise
   ```

3. **Saga Pattern for Distributed Transactions**:

   ```python
   def process_claim(claim_data):
       try:
           # Create claim in claim_process service
           claim_id = create_claim(claim_data)

           # Send claim data to payments service
           send_claim_to_payments(claim_data)

           # Await response from payments service
           response = await get_payment_response(claim_id)

           # Handle payment response
           handle_payment_response(response)
       except Exception as e:
           logger.error(f"Error processing claim: {str(e)}")
           # Rollback if any step fails
           rollback_claim(claim_id)
           raise
   ```

### Handling Failures and Unwinding Steps

- **Retry Mechanism**: Implement retry logic for transient failures,
  such as network issues.
- **Compensation Actions**: Define compensation actions for each step to undo
  the changes if a failure occurs.
- **Monitoring and Alerts**: Set up monitoring and alerts to detect and respond
  to failures promptly.

### Running Multiple Instances

- **Load Balancing**: Use a load balancer to distribute incoming requests
  across multiple instances of each service.
- **Horizontal Scaling**: Deploy multiple instances of each service to handle
  increased load. Ensure that the message broker is also scalable to handle
  the increased message traffic.
- **Stateless Services**: Design services to be stateless to facilitate
  horizontal scaling. Store session data in a distributed cache if needed.
- **Idempotency**: Ensure that service endpoints are idempotent, meaning that
  repeated requests with the same data will not result in duplicate operations.
