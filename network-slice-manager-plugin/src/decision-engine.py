# decision_engine.py

import requests
import json
import time

class DecisionEngine:
    def __init__(self, config):
        """
        Initialize the decision engine with the given configuration.

        Args:
            config (dict): Configuration dictionary containing API endpoints, thresholds, etc.
        """
        self.config = config

    def fetch_alerts(self):
        """
        Fetch alerts from the data processing API.

        Returns:
            list: List of alerts.
        """
        response = requests.get(self.config.get('alerts_endpoint'))
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def evaluate_alert(self, alert):
        """
        Evaluate an alert against predefined thresholds.

        Args:
            alert (dict): Alert data.

        Returns:
            dict: Decision based on the alert.
        """
        decision = {'alert': alert, 'action': None}

        # Compare alert values with predefined thresholds
        for key, value in alert.items():
            threshold = self.config.get('thresholds', {}).get(key)
            if threshold and value > threshold:
                decision['action'] = self.make_decision(alert)
                break

        return decision

    def make_decision(self, alert):
        """
        Make a decision based on the alert using predefined templates.

        Args:
            alert (dict): Alert data.

        Returns:
            dict: Action to be taken.
        """
        template = self.select_template(alert)
        if template:
            response = self.call_api(template, alert)
            return response
        return None

    def select_template(self, alert):
        """
        Select the appropriate template for the given alert.

        Args:
            alert (dict): Alert data.

        Returns:
            dict: Template with API calls.
        """
        # Example: Selecting a template based on alert type
        alert_type = alert.get('type')
        return self.config.get('templates', {}).get(alert_type)

    def call_api(self, template, alert):
        """
        Call the API as per the template instructions.

        Args:
            template (dict): Template data containing API call instructions.
            alert (dict): Alert data.

        Returns:
            dict: API response.
        """
        url = template.get('url')
        method = template.get('method', 'GET').upper()
        headers = template.get('headers', {})
        data = template.get('data', {})
        data.update(alert)  # Include alert data in the API call

        if method == 'POST':
            response = requests.post(url, headers=headers, json=data)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=data)
        else:
            response = requests.get(url, headers=headers, params=data)

        if response.status_code in [200, 201]:
            return response.json()
        else:
            response.raise_for_status()

    def run(self):
        """
        Run the decision engine to continuously fetch and process alerts.
        """
        while True:
            alerts = self.fetch_alerts()
            for alert in alerts:
                decision = self.evaluate_alert(alert)
                if decision.get('action'):
                    print(f"Decision made: {decision}")
            time.sleep(self.config.get('poll_interval', 60))

# Example usage
if __name__ == "__main__":
    config = {
        'alerts_endpoint': 'http://localhost:5000/alerts',
        'thresholds': {
            'signal_strength': -85,
            'latency': 50,
            'packet_loss': 2,
            'throughput': 100,
            # Add other thresholds as needed
        },
        'templates': {
            'high_signal_strength': {
                'url': 'http://example.com/api/high-signal-action',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'data': {'action': 'adjust_antenna'}
            },
            'high_latency': {
                'url': 'http://example.com/api/high-latency-action',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'data': {'action': 'increase_bandwidth'}
            },
            'high_packet_loss': {
                'url': 'http://example.com/api/high-packet-loss-action',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'data': {'action': 'optimize_routing'}
            },
            'low_throughput': {
                'url': 'http://example.com/api/low-throughput-action',
                'method': 'POST',
                'headers': {'Content-Type': 'application/json'},
                'data': {'action': 'allocate_resources'}
            },
            # Add other templates as needed
        },
        'poll_interval': 60  # Poll every 60 seconds
    }

    engine = DecisionEngine(config)
    engine.run()