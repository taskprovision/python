"""
Tests for the AIAnalyzer class
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from taskprovision.core.ai_analyzer import (
    AIAnalyzer,
    AnalysisType,
    AnalysisResult
)

@pytest.fixture
def mock_llm_service():
    """Create a mock LLM service"""
    mock = AsyncMock()
    mock.generate.return_value = {
        "suggestions": ["Add error handling", "Improve variable names"],
        "score": 0.9
    }
    return mock

@pytest.fixture
def sample_code():
    """Sample Python code for testing"""
    return """
def add(a, b):
    return a + b
"""

@pytest.mark.asyncio
async def test_analyze_code_quality(mock_llm_service, sample_code):
    """Test analyzing code quality"""
    analyzer = AIAnalyzer(llm_service=mock_llm_service)
    
    # Test with LLM service
    result = await analyzer.analyze_code(sample_code, "python")
    
    assert AnalysisType.CODE_QUALITY in result
    assert isinstance(result[AnalysisType.CODE_QUALITY], AnalysisResult)
    assert 0 <= result[AnalysisType.CODE_QUALITY].score <= 1.0
    assert len(result[AnalysisType.CODE_QUALITY].suggestions) > 0
    
    # Verify LLM service was called
    mock_llm_service.generate.assert_awaited_once()

@pytest.mark.asyncio
async def test_analyze_code_quality_no_llm():
    """Test analyzing code quality without LLM service"""
    analyzer = AIAnalyzer()
    
    result = await analyzer.analyze_code("def test(): pass", "python")
    
    assert AnalysisType.CODE_QUALITY in result
    assert isinstance(result[AnalysisType.CODE_QUALITY], AnalysisResult)
    assert result[AnalysisType.CODE_QUALITY].score == 0.8  # Default score from mock
    assert len(result[AnalysisType.CODE_QUALITY].suggestions) > 0

@pytest.mark.asyncio
async def test_analyze_task_complexity():
    """Test analyzing task complexity"""
    analyzer = AIAnalyzer()
    
    result = await analyzer.analyze_task_complexity("Implement user authentication")
    
    assert result.analysis_type == AnalysisType.TASK_COMPLEXITY
    assert 0 <= result.score <= 1.0
    assert len(result.suggestions) > 0

@pytest.mark.asyncio
async def test_analyze_code_with_multiple_analysis_types(mock_llm_service, sample_code):
    """Test analyzing code with multiple analysis types"""
    analyzer = AIAnalyzer(llm_service=mock_llm_service)
    
    result = await analyzer.analyze_code(
        sample_code,
        "python",
        analysis_types=[AnalysisType.CODE_QUALITY, AnalysisType.SECURITY]
    )
    
    assert len(result) == 2
    assert AnalysisType.CODE_QUALITY in result
    assert AnalysisType.SECURITY in result
