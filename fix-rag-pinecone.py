# In vectorstore.py, replace _get_api_key method with:

def _get_api_key(self) -> str:
    """Get Pinecone API key from environment or Secret Manager"""
    
    # Try environment variable first (for local dev)
    api_key = os.getenv('PINECONE_API_KEY')
    if api_key:
        return api_key
    
    # Fall back to GCP Secret Manager (for production)
    try:
        from google.cloud import secretmanager
        client = secretmanager.SecretManagerServiceClient()
        name = f"projects/{self.project_id}/secrets/pinecone-api-key/versions/latest"
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode('UTF-8')
    except Exception as e:
        raise ValueError(f"Could not get Pinecone API key from env or Secret Manager: {e}")
