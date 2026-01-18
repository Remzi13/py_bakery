"""Simple and focused tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestAPIEndpoints:
    """Test all main API endpoints."""
    
    def test_products_endpoint(self, client):
        """Test products API endpoint."""
        response = client.get("/api/products/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_products_new_form(self, client):
        """Test new product form endpoint."""
        response = client.get("/api/products/new")
        assert response.status_code == 200
    
    def test_suppliers_endpoint(self, client):
        """Test suppliers API endpoint."""
        response = client.get("/api/suppliers/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_suppliers_new_form(self, client):
        """Test new supplier form endpoint."""
        response = client.get("/api/suppliers/new")
        assert response.status_code == 200
    
    def test_main_pages(self, client):
        """Test main page routes."""
        endpoints = ["/", "/management", "/pos"]
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200
            assert "html" in response.headers.get("content-type", "").lower()
    
    def test_invalid_route_returns_404(self, client):
        """Test that invalid routes return 404."""
        response = client.get("/invalid/route")
        assert response.status_code == 404
    
    def test_nonexistent_resource_returns_404(self, client):
        """Test accessing non-existent resource."""
        response = client.get("/api/products/99999/edit")
        assert response.status_code == 404
