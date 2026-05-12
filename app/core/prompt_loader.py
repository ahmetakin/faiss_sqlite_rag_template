"""
Prompt loader.

Bu modül prompt dosyalarını configs/prompts/{domain}/ altından okur.

Amaç:
- Prompt'ları Python kodundan ayırmak
- Domain'e göre prompt yönetmek
- Prompt versiyonlamayı kolaylaştırmak
"""

from pathlib import Path

from app.core.config import ACTIVE_DOMAIN


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROMPTS_DIR = PROJECT_ROOT / "configs" / "prompts"


def load_prompt(prompt_name: str, domain: str | None = None) -> str:
    """
    Prompt dosyasını okur.

    Örnek:
    load_prompt("rag_system")
    -> configs/prompts/automotive/rag_system.txt

    Args:
        prompt_name:
            Dosya adı. Uzantısız verilir.
        domain:
            Opsiyonel domain adı. Verilmezse ACTIVE_DOMAIN kullanılır.
    """
    active_domain = domain or ACTIVE_DOMAIN

    prompt_path = PROMPTS_DIR / active_domain / f"{prompt_name}.txt"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt dosyası bulunamadı: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8")


def render_prompt(template: str, **kwargs) -> str:
    """
    Prompt template içindeki değişkenleri doldurur.

    Örnek:
    template = "Soru: {question}"
    render_prompt(template, question="Akü garantisi kaç yıl?")
    """
    try:
        return template.format(**kwargs)
    except KeyError as exc:
        missing_key = exc.args[0]
        raise KeyError(f"Prompt template içinde eksik değişken: {missing_key}") from exc


def load_and_render_prompt(prompt_name: str, domain: str | None = None, **kwargs) -> str:
    """
    Prompt dosyasını okur ve değişkenlerini doldurur.
    """
    template = load_prompt(prompt_name=prompt_name, domain=domain)
    return render_prompt(template, **kwargs)