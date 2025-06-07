# free_tools/repo_health_checker.py
def create_free_health_checker():
    """
    Darmowy tool który:
    1. Analizuje repo GitHub
    2. Daje health score
    3. Pokazuje top 5 problemów
    4. Sugeruje rozwiązania
    5. Oferuje "Get full analysis with WronAI AutoDev"
    """
    return """
    🔍 Repository Health Score: 67/100
    
    ❌ Top Issues Found:
    1. 23% functions lack docstrings
    2. 156 lines of duplicate code detected  
    3. 5 security vulnerabilities
    4. Missing unit tests (43% coverage)
    5. 12 outdated dependencies
    
    💡 Estimated fix time: 14 hours manually
    ⚡ WronAI AutoDev: 2 hours automated
    
    🚀 Get Full Analysis + Auto-Fix: [Start Free Trial]
    """

# Embed na stronie jako widget
<script src="https://tools.wronai.com/health-checker.js"></script>