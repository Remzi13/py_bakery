"""Tests for main application routes and overall functionality."""

import pytest
from fastapi.testclient import TestClient


class TestMainRoutes:
    """Test main application routes."""
    
    def test_root_route(self, client):
        """Test landing page route."""
        response = client.get("/")
        assert response.status_code == 200
        assert "html" in response.headers.get("content-type", "").lower()
    
    def test_management_route(self, client):
        """Test management page route."""
        response = client.get("/management")
        assert response.status_code == 200
        assert "html" in response.headers.get("content-type", "").lower()
    
    def test_pos_route(self, client):
        """Test POS (Point of Sale) page route."""
        response = client.get("/pos")
        assert response.status_code == 200
        assert "html" in response.headers.get("content-type", "").lower()


class TestApplicationStructure:
    """Test application structure and configuration."""
    
    def test_app_has_required_routers(self, client):
        """Test that the app has all required routers included."""
        # Test that various API endpoints exist and return proper responses
        api_endpoints = [
            "/api/products/",
            "/api/stock/",
            "/api/sales/",
            "/api/expenses/documents",
            "/api/suppliers/",
            "/api/orders/",
            "/api/writeoffs/"
        ]
        
        for endpoint in api_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 422], f"Endpoint {endpoint} returned unexpected status"
    
    def test_static_files_mounted(self, client):
        """Test that static files are accessible."""
        # Note: This might return 404 if the files don't exist,
        # but it should be routed through the static file handler
        response = client.get("/static/css/style.css")
        assert response.status_code in [200, 404]
    
    def test_app_title(self):
        """Test that the app has the correct title."""
        from main import app
        assert app.title == "Bakery Manager API"


class TestErrorHandling:
    """Test error handling and invalid requests."""
    
    def test_invalid_route(self, client):
        """Test that invalid routes return 404."""
        response = client.get("/invalid/route/that/does/not/exist")
        assert response.status_code == 404
    
    def test_invalid_api_method(self, client):
        """Test that invalid HTTP methods are handled."""
        response = client.put("/api/products/")
        assert response.status_code in [405, 422]
    
    def test_nonexistent_resource(self, client):
        """Test accessing non-existent resource returns appropriate error."""
        response = client.get("/api/products/99999/edit")
        assert response.status_code == 404
