# Interpol Red Notices Tracker

**`Interpol-Red-Notices-Tracker`** is composed of three dockerized modules:

- **`Producer:`** Fetches the [Red Notices](https://www.interpol.int/How-we-work/Notices/Red-Notices/View-Red-Notices), extracts metadata, and publishes it to a RabbitMQ queue. It runs continuously at a predefined interval.
- **`Organizer:`** Consumes messages from RabbitMQ and saves notice details to the PostgreSQL database. It is also responsible for storing related images for each notice in MinIO.
- **`Webapp:`** Flask application that serves template webpages and forwards data to the frontend.

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