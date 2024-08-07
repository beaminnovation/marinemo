# MARINEMO
Network slicing plugin for maritime IoT applications

## Project Overview

MARINEMO is a comprehensive solution designed to enhance maritime operations through the integration of Internet of Things (IoT) technologies. This project aims to improve safety, efficiency, and operational effectiveness in maritime environments by leveraging advanced data processing, AI/ML algorithms, and decision-making engines.

## Features

- **Network Slice Manager Plugin**: Efficient resource allocation and management across different maritime IoT applications.
- **Monitoring Engine**: Real-time monitoring and alerting for network parameters.
- **Decision-Making Engine**: Automated decision-making based on predefined thresholds and templates.
- **API Integration**: Seamless communication with various 5G testbeds and systems.

## Project Structure

```
project-root/
├── config/
│ └── config.yaml
├── data/
│ ├── raw/
│ ├── processed/
│ └── models/
├── docs/
│ ├── architecture.md
│ ├── user_guide.md
│ └── api_documentation.md
├── src/
│ ├── main.py
│ ├── api/
│ │ ├── flask_app.py
│ │ └── endpoints/
│ │ ├── alerts.py
│ │ └── decisions.py
│ ├── data_processing/
│ │ ├── data_processor.py
│ │ ├── ml_model.py
│ │ └── kafka_consumer.py
│ ├── decision_engine/
│ │ ├── decision_engine.py
│ │ └── templates/
│ │ ├── high_latency_template.py
│ │ ├── high_signal_template.py
│ │ └── others.py
│ ├── monitoring/
│ │ ├── monitoring_engine.py
│ │ └── db_handler.py
│ └── utils/
│ ├── logger.py
│ └── helpers.py
├── tests/
│ ├── test_api/
│ │ ├── test_alerts.py
│ │ └── test_decisions.py
│ ├── test_data_processing/
│ │ ├── test_data_processor.py
│ │ └── test_ml_model.py
│ ├── test_decision_engine/
│ │ ├── test_decision_engine.py
│ │ └── test_templates.py
│ ├── test_monitoring/
│ │ ├── test_monitoring_engine.py
│ │ └── test_db_handler.py
│ └── test_utils/
│ ├── test_logger.py
│ └── test_helpers.py
├── .gitignore
├── README.md
└── requirements.txt
```

- **config/**: Configuration files for the project.
- **data/**: Storage for raw and processed data, and machine learning models.
- **docs/**: Documentation files for architecture, user guide, and API documentation.
- **src/**: Source code for the main components of the project.
- **tests/**: Unit and integration tests for the project.
- **requirements.txt**: Python dependencies for the project.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Docker (optional, for containerized deployment)
- Kafka
- PostgreSQL or any other supported SQL database

### Installation

1. Clone the repository:

   ```
   git clone https://github.com/beaminnovation/marinemo.git
   cd marinemo
   ```

2. Create a virtual environment and activate it:

   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the dependencies

   ```
   pip install -r requirements.txt
   ```

4. Configure the project settings in `config/config.yaml`.

5. Run the application:

   ```
   python src/main.py
   ```

# Usage

## Data Processing

The data_processing module processes incoming data from IoT sensors, trains machine learning models, and generates alerts.

## Decision Engine

The decision_engine module consumes alerts, evaluates them against predefined thresholds, and makes decisions based on templates.

## Monitoring

The monitoring module continuously monitors network parameters and provides real-time alerts.

## API Endpoints

Use the API endpoints to fetch alerts and make decisions. Refer to the API Documentation for details on available endpoints and their usage.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes and push to your fork.
4. Submit a pull request with a detailed description of your changes.

## Issues

If you encounter any issues, please report them in the issue tracker.

## License

This project is licensed under the GNU License. See the see the [LICENSE](LICENSE) file for details.

## Contact

For questions or inquiries, please contact [the developer](office@beaminnovation.ro).