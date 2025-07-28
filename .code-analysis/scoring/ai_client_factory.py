import os

try:
    from azure.ai.inference import ChatCompletionsClient
    from azure.identity import DefaultAzureCredential
    from azure.core.credentials import AzureKeyCredential
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    # Define placeholder classes for when Azure isn't available
    class ChatCompletionsClient:
        pass
    class DefaultAzureCredential:
        pass
    class AzureKeyCredential:
        pass


class AIClientFactory:
    """Factory for creating AI Foundry clients only."""
    
    @staticmethod
    def create_client():
        """Create AI Foundry ChatCompletionsClient.
        
        Returns:
            ChatCompletionsClient instance
        """
        endpoint = os.getenv("AI_FOUNDRY_ENDPOINT")
        if not endpoint:
            raise ValueError("AI_FOUNDRY_ENDPOINT environment variable is required")
        
        # For Azure OpenAI endpoints, construct the deployment-specific endpoint
        model_name = os.getenv("AI_FOUNDRY_MODEL", "gpt-4o")
        if not endpoint.endswith('/'):
            endpoint += '/'
        
        # Construct the deployment-specific endpoint
        deployment_endpoint = f"{endpoint}openai/deployments/{model_name}"
        
        # Check if we have an API key or should use DefaultAzureCredential
        token = os.getenv("AI_FOUNDRY_TOKEN")
        if token:
            credential = AzureKeyCredential(token)
        else:
            credential = DefaultAzureCredential()
        
        return ChatCompletionsClient(
            endpoint=deployment_endpoint,
            credential=credential,
            api_version="2024-12-01-preview"
        )
    
    @staticmethod
    def get_model_name() -> str:
        """Get the model deployment name."""
        return os.getenv("AI_FOUNDRY_MODEL", "gpt-4o")
    
    @staticmethod
    def validate_config() -> bool:
        """Validate that required environment variables are set.
        
        Returns:
            True if configuration is valid
        """
        if not AZURE_AVAILABLE:
            raise ValueError("Azure AI dependencies not available. Install: pip install azure-ai-inference azure-identity")
        
        endpoint = os.getenv("AI_FOUNDRY_ENDPOINT")
        if not endpoint:
            raise ValueError("Missing required environment variable: AI_FOUNDRY_ENDPOINT")
        
        token = os.getenv("AI_FOUNDRY_TOKEN")
        if not token:
            import warnings
            warnings.warn(
                "AI_FOUNDRY_TOKEN not set. Will attempt to use DefaultAzureCredential. "
                "Ensure you're authenticated via Azure CLI, managed identity, or environment variables.",
                UserWarning
            )
        
        return True