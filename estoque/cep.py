"""Consulta de CEP no serviço público ViaCEP (https://viacep.com.br)."""
import json
import re
from urllib.error import URLError
from urllib.request import urlopen

VIACEP_URL = "https://viacep.com.br/ws/{cep}/json/"
TIMEOUT_SEGUNDOS = 5


class CepInvalidoError(ValueError):
    """O CEP não tem 8 dígitos."""


class CepNaoEncontradoError(LookupError):
    """O ViaCEP não conhece o CEP informado."""


class ServicoCepIndisponivelError(ConnectionError):
    """Falha de rede ou resposta inválida do ViaCEP."""


def normalizar_cep(cep):
    """Remove pontuação e confere se restaram exatamente 8 dígitos."""
    digitos = re.sub(r"\D", "", cep or "")
    if len(digitos) != 8:
        raise CepInvalidoError("O CEP deve ter 8 dígitos.")
    return digitos


def buscar_cep(cep):
    """Retorna o endereço correspondente ao CEP como dicionário."""
    digitos = normalizar_cep(cep)
    try:
        with urlopen(VIACEP_URL.format(cep=digitos), timeout=TIMEOUT_SEGUNDOS) as resposta:
            dados = json.load(resposta)
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ServicoCepIndisponivelError("Não foi possível consultar o CEP agora.") from exc

    if dados.get("erro"):
        raise CepNaoEncontradoError("CEP não encontrado.")

    return {
        "cep": digitos,
        "logradouro": dados.get("logradouro", ""),
        "bairro": dados.get("bairro", ""),
        "cidade": dados.get("localidade", ""),
        "uf": dados.get("uf", ""),
    }
