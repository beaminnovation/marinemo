# MARINEMO
Network slicing manager plugin for maritime IoT applications

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
├── network-slice-manager-plugin/
│ ├── src/
│ │ ├── decision-engine-1.py
│ │ ├── plugin-api-engine.py
│ │ ├── train.py
│ │ ├── web-app.py
│ │ └── datasets/
│ │ ├── CPE_high.csv
│ │ ├── CPE_medium.csv
│ │ ├── CPE_normal.csv
│ │ └── CPE_normal_medium.py
│ │ └── examples/
│ │ ├── monitoring-1.csv
│ │ ├── traffic_change_alerts_1.csv
│ │ └── testbed-1.json
│ │ └── models/
│ │ ├── scaler.joblib
│ │ └── traffic_model.joblib
│ │ └── templates/
│ │ └── index.html
├── testbed-plugin/
│ ├── src/
│ │ ├── acs-server.py
│ │ ├── Open5GS.py
│ │ ├── slices.py
│ │ ├── subscribers.py
│ │ ├── testbed-api-engine.py
│ │ └── testbed-monitoring-engine.py
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

- **src/**: Source code for the main components of the project.
- **datasets/**: Datasets used for training the AI/ML model used by the Slice Manager Plugin.
- **examples/**: Example files for testbed-specific slice manager behaviour, alerting and monitoring data.
- **models/**: A/ML model computed by the Slice Manager Plugin based on the given datasets.
- **templates/**: Slice Manager Plugin dashboard HTML web interface files.
- **requirements.txt**: Python dependencies for the project.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Kafka (optional)
- InfluxDB (optional)

### Installation

1. Clone the repository:

   ```
   git clone https://github.com/beaminnovation/marinemo.git
   cd marinemo
   ```

2. Create a virtual environment and activate it:

   ```
   python -m venv venv
   source venv/bin/activate
   ```

3. Install the dependencies

   ```
   pip install -r requirements.txt
   ```

5. Run the Slice Manager Plugin:

   ```
   python network-slice-manager-plugin/src/web-app.py
   python network-slice-manager-plugin/src/plugin-api-engine.py
   python network-slice-manager-plugin/src/decision-making-engine.py
   ```

# Slice Manager Plugin components

## Data Ingestion Pipeline

This module continuously gathers network traffic information by interrogating the testbed-specific Performance Monitoring Agents.

## Data Processing

This module saves the monitoring data coming from the Data Ingestion Pipeline and the predictions coming from the AI/ML block to persistent CSV files.

## Decision Making Engine

This module consumes live monitoring data, evaluates them using the trained AI/ML model, and makes decisions based on testbed-specific templates and scenarios.

## Plugin API Engine

This module exposes several endpoints to configure the behaviour of the Slice Manager Plugin, fetch testbed-specific alerts and performance analytics. 
Refer to the API Documentation for details on available endpoints and their usage:
https://app.swaggerhub.com/apis/RazvanMihai/slice-manager-plugin/1.0

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