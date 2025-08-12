"""
Colombian Labor Law knowledge base and legal information.
"""

# Colombian Labor Law Topics
LEGAL_TOPICS = {
    "contratos": {
        "keywords": ["contrato", "contratos", "trabajo", "empleo", "vinculación", "nombramiento"],
        "description": "Contratos de trabajo y vinculación laboral"
    },
    "salarios": {
        "keywords": ["salario", "sueldo", "pago", "remuneración", "salarios", "pagos"],
        "description": "Salarios, pagos y remuneración"
    },
    "prestaciones": {
        "keywords": ["prestaciones", "cesantías", "prima", "vacaciones", "bonificaciones"],
        "description": "Prestaciones sociales y beneficios"
    },
    "terminacion": {
        "keywords": ["despido", "terminación", "renuncia", "liquidación", "finiquito"],
        "description": "Terminación de contratos y despidos"
    },
    "derechos": {
        "keywords": ["derechos", "obligaciones", "deberes", "protección"],
        "description": "Derechos y obligaciones laborales"
    },
    "licencias": {
        "keywords": ["licencia", "permiso", "incapacidad", "maternidad", "paternidad"],
        "description": "Licencias y permisos laborales"
    },
    "seguridad_social": {
        "keywords": ["eps", "pensión", "arl", "seguridad social", "salud"],
        "description": "Seguridad social y afiliaciones"
    }
}

# Key Colombian Labor Law Information
LABOR_LAW_BASICS = """
INFORMACIÓN BÁSICA DEL DERECHO LABORAL COLOMBIANO:

1. VACACIONES:
- 15 días hábiles por año de servicio
- Se pueden acumular hasta por 2 años
- Compensación en dinero solo en casos excepcionales

2. SALARIO MÍNIMO (2024):
- Salario mínimo legal vigente: $1.300.000
- Auxilio de transporte: $162.000

3. PRESTACIONES SOCIALES:
- Prima de servicios: 15 días de salario por semestre
- Cesantías: 1 mes de salario por año
- Intereses sobre cesantías: 12% anual

4. JORNADA LABORAL:
- Máximo 8 horas diarias, 48 horas semanales
- Horas extras: 25% recargo diurno, 75% nocturno

5. TERMINACIÓN DE CONTRATO:
- Con justa causa: sin indemnización
- Sin justa causa: indemnización según tiempo de servicio

6. LICENCIAS:
- Maternidad: 18 semanas
- Paternidad: 2 semanas
- Luto: 5 días hábiles

IMPORTANTE: Esta información es general. Para casos específicos, consulte con un abogado laboralista.
"""

def identify_legal_topic(message: str) -> str:
    """
    Identify the legal topic based on keywords in the message.
    
    Args:
        message: User's message text
        
    Returns:
        Identified legal topic or 'general' if no specific topic found
    """
    message_lower = message.lower()
    
    for topic, info in LEGAL_TOPICS.items():
        for keyword in info["keywords"]:
            if keyword in message_lower:
                return topic
    
    return "general"


def get_topic_context(topic: str) -> str:
    """
    Get relevant legal context for a specific topic.
    
    Args:
        topic: Legal topic identifier
        
    Returns:
        Relevant legal information for the topic
    """
    if topic == "general":
        return LABOR_LAW_BASICS
    
    topic_info = LEGAL_TOPICS.get(topic, {})
    description = topic_info.get("description", "Consulta laboral general")
    
    # Return basic info plus topic-specific context
    return f"{LABOR_LAW_BASICS}\n\nTEMA ESPECÍFICO: {description}"
