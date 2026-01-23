"""
RFC-10 Test Support - Bypass Detection Target
Operation that can be executed with or without guardian.
Used to test bypass detection.
"""


class BypassDetectionTarget:
    """
    Operation that tracks whether it was executed with guardian protection.
    """
    
    def __init__(self):
        self.execution_count = 0
        self.guarded_executions = 0
        self.unguarded_executions = 0
    
    def execute_guarded(self) -> str:
        """
        Execute with guardian (proper path).
        """
        self.execution_count += 1
        self.guarded_executions += 1
        return f"guarded_execution_{self.execution_count}"
    
    def execute_unguarded(self) -> str:
        """
        Execute without guardian (bypass - should be blocked).
        """
        self.execution_count += 1
        self.unguarded_executions += 1
        return f"BYPASS_DETECTED_{self.execution_count}"
    
    def was_bypassed(self) -> bool:
        """
        Check if any unguarded executions occurred.
        """
        return self.unguarded_executions > 0
    
    def reset(self):
        """Reset counters."""
        self.execution_count = 0
        self.guarded_executions = 0
        self.unguarded_executions = 0
