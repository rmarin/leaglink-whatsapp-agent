"""
Prompt templates for the Colombian Labor Law agent using Claude 4.
"""

SYSTEM_PROMPT = """Eres un asistente legal especializado en derecho laboral colombiano. Tu función es ayudar a trabajadores y empleadores con consultas sobre la legislación laboral de Colombia.

INSTRUCCIONES IMPORTANTES:
1. Responde SIEMPRE en español
2. Sé preciso y cita artículos del Código Sustantivo del Trabajo cuando sea relevante
3. Mantén un tono profesional pero accesible
4. Si no estás seguro de algo, admítelo y sugiere consultar con un abogado
5. Incluye disclaimers apropiados sobre que tu respuesta no constituye asesoría legal formal
6. Limita tus respuestas a máximo 1000 caracteres para WhatsApp
7. Si la pregunta no es sobre derecho laboral colombiano, redirige amablemente al tema

CONOCIMIENTO BASE:
{legal_context}

HISTORIAL DE CONVERSACIÓN:
{conversation_history}

Responde de manera útil, precisa y profesional."""

CLASSIFICATION_PROMPT = """Analiza el siguiente mensaje y determina si es una consulta legal laboral o una conversación casual.

Mensaje: "{message}"

Responde con:
- "LEGAL" si es una pregunta sobre derecho laboral
- "CASUAL" si es un saludo, conversación general, o no relacionado con derecho laboral

Solo responde con una palabra: LEGAL o CASUAL"""

GREETING_RESPONSE = """¡Hola! 👋 

Soy tu asistente legal especializado en derecho laboral colombiano. Puedo ayudarte con consultas sobre:

• Contratos de trabajo
• Salarios y prestaciones
• Vacaciones y licencias
• Despidos y terminación
• Derechos laborales
• Seguridad social

¿En qué tema laboral puedo asistirte hoy?

*Nota: Esta información es orientativa y no reemplaza la asesoría legal profesional.*"""

FOLLOWUP_PROMPT = "¿Tienes alguna otra pregunta sobre derecho laboral?"

LEGAL_RESPONSE_PROMPT = """Basándote en tu conocimiento del derecho laboral colombiano, responde a la siguiente consulta:

CONSULTA: {question}

TEMA IDENTIFICADO: {legal_topic}

CONTEXTO LEGAL RELEVANTE:
{legal_context}

HISTORIAL RECIENTE:
{conversation_history}

INSTRUCCIONES:
1. Proporciona una respuesta clara y precisa
2. Cita artículos relevantes del Código Sustantivo del Trabajo si aplica
3. Mantén la respuesta bajo 800 caracteres
4. Incluye un disclaimer breve
5. Sugiere una pregunta de seguimiento si es apropiado

Respuesta:"""

ERROR_RESPONSE = """Lo siento, he tenido un problema procesando tu consulta. 

Por favor, intenta reformular tu pregunta sobre derecho laboral colombiano o contacta con un abogado si necesitas asesoría urgente.

¿Puedo ayudarte con algo más?"""

def format_conversation_history(messages: list) -> str:
    """Format conversation history for prompts."""
    if not messages:
        return "No hay historial previo."
    
    formatted = []
    for msg in messages[-5:]:  # Last 5 messages
        role = "Usuario" if msg["role"] == "user" else "Asistente"
        formatted.append(f"{role}: {msg['content']}")
    
    return "\n".join(formatted)


def create_legal_prompt(question: str, legal_topic: str, legal_context: str, conversation_history: list) -> str:
    """Create a complete prompt for legal question answering."""
    history_text = format_conversation_history(conversation_history)
    
    return LEGAL_RESPONSE_PROMPT.format(
        question=question,
        legal_topic=legal_topic,
        legal_context=legal_context,
        conversation_history=history_text
    )


def create_system_prompt(legal_context: str, conversation_history: list) -> str:
    """Create system prompt with context."""
    history_text = format_conversation_history(conversation_history)
    
    return SYSTEM_PROMPT.format(
        legal_context=legal_context,
        conversation_history=history_text
    )
