"""
Domain loader.

Bu dosya aktif domain'e ait modülleri dinamik olarak yükler.

Amaç:
Core katmanı doğrudan app.domains.automotive import etmesin.
Böylece ileride automotive yerine başka domain kullanılabilir.
"""

from importlib import import_module

from app.core.config import ACTIVE_DOMAIN


def load_domain_module(module_name: str):
    """
    Aktif domain içindeki bir modülü yükler.

    Örnek:
    ACTIVE_DOMAIN = "automotive"

    load_domain_module("prompts")
    -> app.domains.automotive.prompts
    """
    full_module_path = f"app.domains.{ACTIVE_DOMAIN}.{module_name}"
    return import_module(full_module_path)


def get_domain_prompts():
    """
    Aktif domain prompt modülünü döndürür.
    """
    return load_domain_module("prompts")


def get_domain_context():
    """
    Aktif domain context formatter modülünü döndürür.
    """
    return load_domain_module("context")


def get_domain_tools():
    """
    Aktif domain tools modülünü döndürür.
    """
    return load_domain_module("tools")


def get_domain_router_rules():
    """
    Aktif domain router_rules modülünü döndürür.
    """
    return load_domain_module("router_rules")


def get_domain_retrieval_rules():
    """
    Aktif domain retrieval_rules modülünü döndürür.
    """
    return load_domain_module("retrieval_rules")

def get_domain_tool_rules():
    """
    Aktif domain tool routing rules modülünü döndürür.
    """
    return load_domain_module("tool_rules")