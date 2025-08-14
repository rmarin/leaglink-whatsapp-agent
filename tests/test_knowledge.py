import pytest
from app.agent.knowledge import (
    identify_legal_topic,
    get_topic_context,
    LEGAL_TOPICS,
    LABOR_LAW_BASICS
)


@pytest.mark.unit
class TestKnowledge:
    """Test cases for the Colombian Labor Law knowledge base."""

    def test_identify_legal_topic_contracts(self):
        """Test identifying contract-related topics."""
        messages = [
            "¿Cómo firmo un contrato de trabajo?",
            "Mi empleo tiene problemas",
            "Vinculación laboral nueva"
        ]
        
        for message in messages:
            topic = identify_legal_topic(message)
            assert topic == "contratos"

    def test_identify_legal_topic_salaries(self):
        """Test identifying salary-related topics."""
        messages = [
            "¿Cuánto es el salario mínimo?",
            "No me han pagado mi sueldo",
            "Remuneración por horas extras"
        ]
        
        for message in messages:
            topic = identify_legal_topic(message)
            assert topic == "salarios"

    def test_identify_legal_topic_benefits(self):
        """Test identifying benefits-related topics."""
        messages = [
            "¿Cuánto es la prima de servicios?",
            "Prestaciones sociales que me deben",
            "Cesantías no pagadas",
            "Vacaciones acumuladas"
        ]
        
        for message in messages:
            topic = identify_legal_topic(message)
            assert topic == "prestaciones"

    def test_identify_legal_topic_termination(self):
        """Test identifying termination-related topics."""
        messages = [
            "Me despidieron sin justa causa",
            "Terminación de contrato laboral",
            "Quiero renunciar a mi trabajo",
            "Liquidación final"
        ]
        
        for message in messages:
            topic = identify_legal_topic(message)
            assert topic == "terminacion"

    def test_identify_legal_topic_rights(self):
        """Test identifying rights-related topics."""
        messages = [
            "¿Cuáles son mis derechos laborales?",
            "Obligaciones del empleador",
            "Protección laboral"
        ]
        
        for message in messages:
            topic = identify_legal_topic(message)
            assert topic == "derechos"

    def test_identify_legal_topic_leaves(self):
        """Test identifying leave-related topics."""
        messages = [
            "Licencia de maternidad",
            "Permiso por luto",
            "Incapacidad médica",
            "Licencia de paternidad"
        ]
        
        for message in messages:
            topic = identify_legal_topic(message)
            assert topic == "licencias"

    def test_identify_legal_topic_social_security(self):
        """Test identifying social security topics."""
        messages = [
            "Afiliación a EPS",
            "Pensión de vejez",
            "ARL riesgos laborales",
            "Seguridad social independientes"
        ]
        
        for message in messages:
            topic = identify_legal_topic(message)
            assert topic == "seguridad_social"

    def test_identify_legal_topic_general(self):
        """Test general topic identification for unspecific messages."""
        messages = [
            "Hola, ¿cómo estás?",
            "Necesito ayuda legal",
            "Pregunta sobre trabajo",
            "¿Qué tal el día?"
        ]
        
        for message in messages:
            topic = identify_legal_topic(message)
            assert topic == "general"

    def test_identify_legal_topic_case_insensitive(self):
        """Test that topic identification is case insensitive."""
        messages = [
            "CONTRATO DE TRABAJO",
            "Salario Mínimo",
            "PRESTACIONES SOCIALES",
            "despido"
        ]
        
        expected_topics = ["contratos", "salarios", "prestaciones", "terminacion"]
        
        for message, expected in zip(messages, expected_topics):
            topic = identify_legal_topic(message)
            assert topic == expected

    def test_identify_legal_topic_multiple_keywords(self):
        """Test topic identification when multiple keywords are present."""
        message = "Mi contrato incluye salario y prestaciones"
        topic = identify_legal_topic(message)
        
        # Should return the first matching topic found
        assert topic in ["contratos", "salarios", "prestaciones"]

    def test_get_topic_context_general(self):
        """Test getting context for general topic."""
        context = get_topic_context("general")
        
        assert context == LABOR_LAW_BASICS
        assert "VACACIONES" in context
        assert "SALARIO MÍNIMO" in context
        assert "PRESTACIONES SOCIALES" in context

    def test_get_topic_context_specific_topic(self):
        """Test getting context for specific topics."""
        topic = "contratos"
        context = get_topic_context(topic)
        
        assert LABOR_LAW_BASICS in context
        assert LEGAL_TOPICS[topic]["description"] in context
        assert "TEMA ESPECÍFICO" in context

    def test_get_topic_context_all_topics(self):
        """Test getting context for all defined topics."""
        for topic in LEGAL_TOPICS.keys():
            context = get_topic_context(topic)
            
            assert LABOR_LAW_BASICS in context
            assert LEGAL_TOPICS[topic]["description"] in context
            assert "TEMA ESPECÍFICO" in context

    def test_get_topic_context_nonexistent_topic(self):
        """Test getting context for non-existent topic."""
        context = get_topic_context("nonexistent_topic")
        
        assert LABOR_LAW_BASICS in context
        assert "Consulta laboral general" in context

    def test_legal_topics_structure(self):
        """Test that LEGAL_TOPICS has proper structure."""
        for topic, info in LEGAL_TOPICS.items():
            assert isinstance(topic, str)
            assert isinstance(info, dict)
            assert "keywords" in info
            assert "description" in info
            assert isinstance(info["keywords"], list)
            assert isinstance(info["description"], str)
            assert len(info["keywords"]) > 0
            assert len(info["description"]) > 0

    def test_labor_law_basics_content(self):
        """Test that LABOR_LAW_BASICS contains essential information."""
        essential_topics = [
            "VACACIONES",
            "SALARIO MÍNIMO",
            "PRESTACIONES SOCIALES",
            "JORNADA LABORAL",
            "TERMINACIÓN DE CONTRATO",
            "LICENCIAS"
        ]
        
        for topic in essential_topics:
            assert topic in LABOR_LAW_BASICS

    def test_keywords_coverage(self):
        """Test that keywords cover essential Spanish labor law terms."""
        all_keywords = []
        for topic_info in LEGAL_TOPICS.values():
            all_keywords.extend(topic_info["keywords"])
        
        essential_keywords = [
            "contrato", "trabajo", "salario", "prestaciones", 
            "despido", "derechos", "licencia", "eps"
        ]
        
        for keyword in essential_keywords:
            assert keyword in all_keywords

    def test_topic_descriptions_in_spanish(self):
        """Test that all topic descriptions are in Spanish."""
        spanish_indicators = ["de", "y", "del", "las", "los", "la", "el"]
        
        for topic_info in LEGAL_TOPICS.values():
            description = topic_info["description"].lower()
            # At least one Spanish indicator should be present
            assert any(indicator in description for indicator in spanish_indicators)