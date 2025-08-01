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
            
            print(f"ChatModel inicializado correctamente con deployment: {self.deployment_name}")
        except Exception as e:
            print(f"Error al inicializar ChatModel: {str(e)}")
            raise

    def generate_response(self, user_input, chat_history=None, travel_config=None):
        try:
            # Inicializar el historial si es None
            if chat_history is None:
                chat_history = []
            
            # Si hay configuración de viaje, usar el nuevo sistema de agentes
            if travel_config:
                return self._generate_response_with_agents(user_input, chat_history, travel_config)
            
            # Preparar el historial de chat
            messages = []
            if chat_history:
                for msg in chat_history:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Añadir el mensaje actual del usuario
            messages.append({"role": "user", "content": user_input})

            # Llamar a la API de Azure OpenAI
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

            # Obtener la respuesta
            assistant_message = response.choices[0].message.content

            # Actualizar el historial
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": assistant_message})

            # Mantener solo los últimos 10 mensajes para evitar tokens excesivos
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]

            return assistant_message, chat_history

        except Exception as e:
            print(f"Error en generate_response: {str(e)}")
            error_message = f"Lo siento, ha ocurrido un error al procesar tu mensaje: {str(e)}"
            return error_message, chat_history or []

    def _generate_response_with_agents(self, user_input, chat_history, travel_config):
        """
        Genera respuesta usando el sistema de agentes con configuración de viaje.
        """
        try:
            from app.agents.smart_itinerary_workflow import SmartItineraryWorkflow
            from datetime import datetime
            import asyncio
            
            # Extraer configuración del viaje
            travel_id = travel_config.get("travel_id", "default")
            user_id = travel_config.get("user_email", "default")
            start_date = travel_config.get("start_date")
            total_days = travel_config.get("total_days", 7)
            country = travel_config.get("country", "thailand")
            
            # Crear instancia del workflow
            workflow = SmartItineraryWorkflow()
            
            # Procesar con el workflow inteligente usando asyncio
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
            
            # Obtener respuesta
            assistant_message = result.get("message", "No se pudo generar respuesta")
            
            # Actualizar historial
            chat_history.append({"role": "user", "content": user_input})
            chat_history.append({"role": "assistant", "content": assistant_message})
            
            # Mantener solo los últimos 10 mensajes
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]
            
            return assistant_message, chat_history
            
        except Exception as e:
            print(f"Error en _generate_response_with_agents: {str(e)}")
            error_message = f"Lo siento, ha ocurrido un error al procesar tu solicitud de viaje: {str(e)}"
            return error_message, chat_history or []

# Instancia global del modelo
chat_model = ChatModel() 