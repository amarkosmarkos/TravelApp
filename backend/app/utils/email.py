from typing import List, Optional, Dict, Any, Union
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pathlib import Path
import jinja2
import aiofiles
import logging
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

# Configuración de FastMail
email_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_TLS=True,
    MAIL_SSL=False,
    USE_CREDENTIALS=True,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates" / "email"
)

# Configuración de Jinja2
template_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(email_config.TEMPLATE_FOLDER)
)

# Instancia de FastMail
fastmail = FastMail(email_config)

async def send_email(
    email_to: Union[str, List[str]],
    subject: str,
    template_name: str,
    template_data: Dict[str, Any],
    attachments: Optional[List[Dict[str, Any]]] = None
) -> bool:
    """
    Enviar email usando plantilla
    
    Args:
        email_to: Destinatario(s)
        subject: Asunto
        template_name: Nombre de la plantilla
        template_data: Datos para la plantilla
        attachments: Archivos adjuntos
    
    Returns:
        bool: True si se envió correctamente
    """
    try:
        # Cargar plantilla
        template = template_env.get_template(f"{template_name}.html")
        html_content = template.render(**template_data)
        
        # Crear mensaje
        message = MessageSchema(
            subject=subject,
            recipients=[email_to] if isinstance(email_to, str) else email_to,
            body=html_content,
            subtype="html",
            attachments=attachments
        )
        
        # Enviar email
        await fastmail.send_message(message)
        return True
    
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return False

async def send_verification_email(
    email_to: str,
    verification_url: str,
    user_name: Optional[str] = None
) -> bool:
    """
    Enviar email de verificación
    
    Args:
        email_to: Destinatario
        verification_url: URL de verificación
        user_name: Nombre del usuario
    
    Returns:
        bool: True si se envió correctamente
    """
    template_data = {
        "verification_url": verification_url,
        "user_name": user_name
    }
    
    return await send_email(
        email_to=email_to,
        subject="Verifica tu email",
        template_name="verification",
        template_data=template_data
    )

async def send_reset_password_email(
    email_to: str,
    reset_url: str,
    user_name: Optional[str] = None
) -> bool:
    """
    Enviar email de reseteo de contraseña
    
    Args:
        email_to: Destinatario
        reset_url: URL de reseteo
        user_name: Nombre del usuario
    
    Returns:
        bool: True si se envió correctamente
    """
    template_data = {
        "reset_url": reset_url,
        "user_name": user_name
    }
    
    return await send_email(
        email_to=email_to,
        subject="Resetea tu contraseña",
        template_name="reset_password",
        template_data=template_data
    )

async def send_welcome_email(
    email_to: str,
    user_name: str,
    login_url: str
) -> bool:
    """
    Enviar email de bienvenida
    
    Args:
        email_to: Destinatario
        user_name: Nombre del usuario
        login_url: URL de login
    
    Returns:
        bool: True si se envió correctamente
    """
    template_data = {
        "user_name": user_name,
        "login_url": login_url
    }
    
    return await send_email(
        email_to=email_to,
        subject="¡Bienvenido!",
        template_name="welcome",
        template_data=template_data
    )

async def send_travel_invitation_email(
    email_to: str,
    travel_name: str,
    inviter_name: str,
    accept_url: str,
    decline_url: str
) -> bool:
    """
    Enviar email de invitación a viaje
    
    Args:
        email_to: Destinatario
        travel_name: Nombre del viaje
        inviter_name: Nombre del invitador
        accept_url: URL de aceptación
        decline_url: URL de rechazo
    
    Returns:
        bool: True si se envió correctamente
    """
    template_data = {
        "travel_name": travel_name,
        "inviter_name": inviter_name,
        "accept_url": accept_url,
        "decline_url": decline_url
    }
    
    return await send_email(
        email_to=email_to,
        subject=f"Invitación a {travel_name}",
        template_name="travel_invitation",
        template_data=template_data
    )

async def send_travel_update_email(
    email_to: str,
    travel_name: str,
    update_type: str,
    update_details: Dict[str, Any],
    travel_url: str
) -> bool:
    """
    Enviar email de actualización de viaje
    
    Args:
        email_to: Destinatario
        travel_name: Nombre del viaje
        update_type: Tipo de actualización
        update_details: Detalles de la actualización
        travel_url: URL del viaje
    
    Returns:
        bool: True si se envió correctamente
    """
    template_data = {
        "travel_name": travel_name,
        "update_type": update_type,
        "update_details": update_details,
        "travel_url": travel_url
    }
    
    return await send_email(
        email_to=email_to,
        subject=f"Actualización en {travel_name}",
        template_name="travel_update",
        template_data=template_data
    )

async def send_notification_email(
    email_to: str,
    notification_type: str,
    notification_data: Dict[str, Any],
    action_url: Optional[str] = None
) -> bool:
    """
    Enviar email de notificación
    
    Args:
        email_to: Destinatario
        notification_type: Tipo de notificación
        notification_data: Datos de la notificación
        action_url: URL de acción (opcional)
    
    Returns:
        bool: True si se envió correctamente
    """
    template_data = {
        "notification_type": notification_type,
        "notification_data": notification_data,
        "action_url": action_url
    }
    
    return await send_email(
        email_to=email_to,
        subject=f"Nueva notificación: {notification_type}",
        template_name="notification",
        template_data=template_data
    ) 