from openai import AzureOpenAI
from ..config import settings
import logging

logger = logging.getLogger(__name__)

class ChatGPTService:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
        )
        self.deployment_name = settings.AZURE_OPENAI_DEPLOYMENT_NAME

    async def get_travel_recommendation(self, user_message: str) -> str:
        try:
            system_message = """Eres un asistente de viajes experto. Tu objetivo es ayudar a los usuarios a planificar sus viajes 
            de manera efectiva y personalizada. Proporciona recomendaciones detalladas sobre destinos, itinerarios, 
            alojamientos y actividades. Sé específico y considera el presupuesto, preferencias y necesidades del usuario."""

            response = await self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=800
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error en ChatGPT service: {str(e)}")
            raise Exception("Error al procesar la solicitud con ChatGPT")

chatgpt_service = ChatGPTService()
