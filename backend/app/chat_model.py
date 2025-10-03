from openai import AzureOpenAI
from app.config import settings
import json
from openai.types.chat import ChatCompletion

class ChatModel:
    def __init__(self):
        try:
            # Debug: Print the endpoint being used
            print(f"Using Azure OpenAI endpoint: {settings.AZURE_OPENAI_ENDPOINT}")
            
            # Ensure the endpoint has the correct format
            endpoint = settings.AZURE_OPENAI_ENDPOINT
            if not endpoint.startswith('http'):
                endpoint = f"https://{endpoint}"
            
            # Initialize the client with explicit URL formatting
            self.client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
                azure_endpoint=endpoint.rstrip('/')
            )
            self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME
            
            # Print full configuration for debugging
            print(f"Azure OpenAI Configuration:")
            print(f"- Endpoint: {endpoint}")
            print(f"- API Version: {settings.AZURE_OPENAI_API_VERSION}")
            print(f"- Deployment: {self.deployment_name}")
            
            # Test connection with minimal request
            test_response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": "Test"}],
                max_tokens=5
            )
            
            print(f"ChatModel initialized correctly with deployment: {self.deployment_name}")
        except Exception as e:
            print(f"Error initializing ChatModel: {str(e)}")
            raise

    def generate_response(self, user_input, chat_history=None, travel_config=None):
        try:
            # Initialize history if None
            if chat_history is None:
                chat_history = []
            
            # If there's travel configuration, use the new agent system
            if travel_config:
                return self._generate_response_with_agents(user_input, chat_history, travel_config)
            
            # Prepare chat history
            messages = []
            if chat_history:
                for msg in chat_history:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Add current user message
            messages.append({"role": "user", "content": user_input})

            # Call Azure OpenAI API
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=0.7,
                max_tokens=800,
                top_p=0.95,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None
            )

            # Get response
            assistant_message = response.choices[0].message.content

            # Update history
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": assistant_message})

            # Keep only last 10 messages to avoid excessive tokens
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]

            return assistant_message, chat_history

        except Exception as e:
            print(f"Error in generate_response: {str(e)}")
            error_message = f"Sorry, an error occurred while processing your message: {str(e)}"
            return error_message, chat_history or []

    def _generate_response_with_agents(self, user_input, chat_history, travel_config):
        """
        Generates response using the agent system with travel configuration.
        """
        try:
            # Simple gating: if input is clearly a greeting or generic, don't trigger flow
            lowered = (user_input or "").strip().lower()
            greetings = ["hola", "hola!", "hola :)", "hi", "hello", "buenas", "buenos dias", "buenas tardes", "buenas noches"]
            if lowered in greetings or len(lowered) <= 3:
                assistant_message = (
                    "Hi! Would you like me to create an itinerary or modify an existing one? "
                    "Tell me the country and duration (e.g., 14 days) and the style (beach, history, nature, food)."
                )
                chat_history.append({"role": "user", "content": user_input})
                chat_history.append({"role": "assistant", "content": assistant_message})
                if len(chat_history) > 10:
                    chat_history = chat_history[-10:]
                return assistant_message, chat_history

            from app.agents.smart_itinerary_workflow import SmartItineraryWorkflow
            from datetime import datetime
            import asyncio
            
            # Extract travel configuration
            travel_id = travel_config.get("travel_id", "default")
            user_id = travel_config.get("user_email", "default")
            start_date = travel_config.get("start_date")
            total_days = travel_config.get("total_days", 7)
            country = travel_config.get("country", "thailand")
            
            # Create workflow instance
            workflow = SmartItineraryWorkflow()
            
            # Process with intelligent workflow using asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(workflow.process_smart_request(
                    user_input=user_input,
                    user_id=user_id,
                    travel_id=travel_id,
                    country=country
                ))
            finally:
                loop.close()
            
            # Get response
            assistant_message = result.get("message", "Could not generate response")
            
            # Update history
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": assistant_message})
            
            # Keep only last 10 messages
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]
            
            return assistant_message, chat_history
            
        except Exception as e:
            print(f"Error in _generate_response_with_agents: {str(e)}")
            error_message = f"Sorry, an error occurred while processing your travel request: {str(e)}"
            return error_message, chat_history or []

# Global model instance
chat_model = ChatModel() 