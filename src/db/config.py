import os
from urllib.parse import urlparse

def get_db_url(use_connection_pooling: bool = True) -> str:
    """
    Get database URL with optional connection pooling using Supavisor
    
    Args:
        use_connection_pooling: Whether to enable connection pooling
        
    Returns:
        Database URL string with appropriate configuration
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set")
        
    if use_connection_pooling:
        # Parse the original URL to get components
        parsed = urlparse(db_url)
        
        # Extract project reference from hostname (assuming format: db.[project-ref].supabase.co)
        project_ref = parsed.hostname.split('.')[1]
        
        # Construct pooled username (format: postgres.[project-ref])
        pooled_username = f"postgres.{project_ref}"
        
        # Construct Supavisor URL
        # Format: postgresql://postgres.[project-ref]:[password]@aws-0-us-west-1.pooler.supabase.com:6543/postgres
        return f"{parsed.scheme}://{pooled_username}:{parsed.password}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"
    
    return db_url 