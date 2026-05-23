"""Ollama client removed.

Local Ollama inference is no longer supported in the cloud-first revert.
If tests or code still import this module, they should be updated to use
GroqRouter or MistralReasoner. This placeholder raises on instantiation.
"""

class OllamaClientStub:
    def __init__(self, *args, **kwargs):
        raise RuntimeError("Ollama client removed as part of revert to cloud-based providers.")
