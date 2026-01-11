"""Locust load testing configuration"""

from locust import HttpUser, task, between
import json


class B2BAnalyzerUser(HttpUser):
    """Simulated user for load testing"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a user starts"""
        # Could authenticate here if needed
        pass
    
    @task(3)
    def health_check(self):
        """Health check endpoint"""
        self.client.get("/health")
    
    @task(2)
    def list_tools(self):
        """List available tools"""
        self.client.get("/api/v1/tools")
    
    @task(1)
    def analyze_tool(self):
        """Run analysis (most resource-intensive)"""
        payload = {
            "tools": ["Salesforce"],
            "use_semantic": True
        }
        self.client.post(
            "/api/v1/analyze",
            json=payload,
            headers={"Content-Type": "application/json"}
        )


# For running with: locust -f locustfile.py --host=http://localhost:8501
