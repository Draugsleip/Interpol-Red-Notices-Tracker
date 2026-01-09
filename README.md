# Interpol Red Notices Tracker

**`Interpol-Red-Notices-Tracker`** is composed of three dockerized modules:

- **`Producer:`** Fetches the [Red Notices](https://www.interpol.int/How-we-work/Notices/Red-Notices/View-Red-Notices), extracts metadata, and publishes it to a RabbitMQ queue. It runs continuously at a predefined interval.
  
- **`Organizer:`** Consumes messages from RabbitMQ and saves notice details to the PostgreSQL database. It is also responsible for storing related images for each notice in MinIO.

- **`Webapp:`** Flask application that serves template webpages and forwards data to the frontend.

## System Structure

<p align="center">
  <br>
  <img width=70% alt="interpol_system_architecture_diagram" src="https://github.com/user-attachments/assets/6a16c124-309a-44ee-b04d-c498de4d4a7e" />
  <br>
  <em>System Architecture Diagram</em>
</p>

### **Producer**

- `fetch_details.py`: Handles the process of fetching data and publishing it to RabbitMQ.

	- make_session(): Creates a requests session with headers from 'config/headers.json'
	
	- fetch_all_data(): The main method. Firstly, it classifies notices by nationality as either light (total notices < 160) or heavy (total notices > 160). For heavy categories, additional queries are used to ensure no notices are missed. Query urls are built using a bruteforce approach. Once all notice details are retrieved they are published to the RabbitMQ queue.

- `query_options.py`: Contains the options required for bruteforce querying. Builds urls and generates query parameters.
  
	- bruteforce_params(): Generates parameter combinations for comprehensive data fetching. For light countries, only nationality is used. For heavy countries, more specific parameters (age, gender, name, and freetext) are combined in different ways to cover all possible cases.

- `rabbitmq_client.py`: Client that publishes notice details to the queue.
	
	- _connect(): Establishes connection with retry and heartbeat logic in case of a disconnection.
	
	- publish_meta(): Function that accept metadata as parameter and sends it to the queue.
<p align="center">
  <br>
  <img width=30% alt="Interpol Producer Flowchart" src="https://github.com/user-attachments/assets/f27c6aa5-40be-49b0-a638-48aaacf0eaf0" />
  <br>
  <em>Producer Flowchart</em>
</p>

### **Organizer**

- `message_receiver.py`: Processes incoming messages from the queue and saves them to the database also handles the transfer of notice images to MinIO.

	- save_to_db(): When a message is received, it checks the database if that notice is already exists in database or its new.
   
	- process_rabbit_messages(): Receives messages, transfers notice images to MinIO and notice details to database.

- `database_config.py`: Establishes the database connection and creates the necessary table structures.

- `minio_client.py`: Sets the connection and creates a bucket. Handles the images that need to be sent to or retreived from MinIO.
	
   - send_to_minio_img(): Uploads images into MinIO bucket using the entity ID as filename.
   
	- list_from_minio(): Lists images of a notice using entity ID as a prefix.

<p align="center">
  <br>
  <img width=30% alt="interpol_organizer_flowchart" src="https://github.com/user-attachments/assets/24c654de-4efc-41e6-9c48-636844d0c451" />
  <br>
  <em>Organizer Flowchart</em>
</p>

### **Webapp**

- `webapp.py`: Flask application with routes and template filters, serves data to frontend.

<p align="center">
  <br>
  <img width=100% alt="interpol_system_flowchart" src="https://github.com/user-attachments/assets/349a0af6-60d1-4f95-89de-c7b07bc3e6ac" />
  <br>
  <em>System Flowchart</em>
</p>

https://github.com/user-attachments/assets/84f21e8d-900b-4c31-aa5c-a80c158107b1

## How to use

### Prerequisites
- Docker Engine
- Docker Compose

### Setup
1. Clone the repository
   
   ```bash
   git clone https://github.com/Draugsleip/Interpol-Red-Notices-Tracker.git

2. Navigate to the project directory
   ```bash
   cd Interpol-Red-Notices-Tracker
   
3. Create your own configuration file using the `.env` template
   ```bash
   copy .env.example .env

4. Start the services
   ```bash
   docker-compose up --build

5. After the initial run, access the web interface at
   ```
   http://localhost:5000
