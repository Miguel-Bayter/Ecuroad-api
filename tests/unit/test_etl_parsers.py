import csv
import hashlib
import io
import pytest

from app.core.exceptions import IntegrityCheckError, SSRFBlockedError
from app.utils.etl.factory import ParserFactory
from app.utils.etl.integrity import ETLIntegrity
from app.utils.etl.snies import SNIESCSVParser


def make_snies_csv(rows: list[dict]) -> bytes:
    fields = [
        "NOMBRE_PROGRAMA", "ESTADO_PROGRAMA", "CODIGO_CINE_CAMPO_DETALLADO",
        "NIVEL_FORMACION", "CODIGO_SNIES_PROGRAMA", "VALOR_MATRICULA", "DESCRIPCION",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


# --- SNIESCSVParser ---

def test_snies_parses_active_record():
    data = make_snies_csv([{
        "NOMBRE_PROGRAMA": "Ingeniería de Sistemas",
        "ESTADO_PROGRAMA": "Activo",
        "CODIGO_CINE_CAMPO_DETALLADO": "061",
        "NIVEL_FORMACION": "Universitario",
        "CODIGO_SNIES_PROGRAMA": "12345",
        "VALOR_MATRICULA": "4000000",
        "DESCRIPCION": "Carrera de sistemas",
    }])
    parser = SNIESCSVParser()
    records = parser.parse(data)
    assert len(records) == 1
    assert records[0]["nombre"] == "Ingeniería de Sistemas"
    assert records[0]["categoria"] == "tech"
    assert records[0]["tipo"] == "universitaria"
    assert records[0]["costoSemestre"] == 4000000


def test_snies_maps_cine_code_to_salud():
    data = make_snies_csv([{
        "NOMBRE_PROGRAMA": "Medicina",
        "ESTADO_PROGRAMA": "Activo",
        "CODIGO_CINE_CAMPO_DETALLADO": "091",
        "NIVEL_FORMACION": "Universitario",
        "CODIGO_SNIES_PROGRAMA": "99",
        "VALOR_MATRICULA": "8000000",
        "DESCRIPCION": "",
    }])
    parser = SNIESCSVParser()
    records = parser.parse(data)
    assert records[0]["categoria"] == "salud"


def test_snies_filters_inactive_records():
    data = make_snies_csv([{
        "NOMBRE_PROGRAMA": "Programa Inactivo",
        "ESTADO_PROGRAMA": "Inactivo",
        "CODIGO_CINE_CAMPO_DETALLADO": "061",
        "NIVEL_FORMACION": "Universitario",
        "CODIGO_SNIES_PROGRAMA": "0",
        "VALOR_MATRICULA": "0",
        "DESCRIPCION": "",
    }])
    parser = SNIESCSVParser()
    records = parser.parse(data)
    assert len(records) == 0


def test_snies_filters_empty_name():
    data = make_snies_csv([{
        "NOMBRE_PROGRAMA": "",
        "ESTADO_PROGRAMA": "Activo",
        "CODIGO_CINE_CAMPO_DETALLADO": "061",
        "NIVEL_FORMACION": "Universitario",
        "CODIGO_SNIES_PROGRAMA": "1",
        "VALOR_MATRICULA": "0",
        "DESCRIPCION": "",
    }])
    parser = SNIESCSVParser()
    records = parser.parse(data)
    assert len(records) == 0


def test_snies_maps_tecnologica_tipo():
    data = make_snies_csv([{
        "NOMBRE_PROGRAMA": "Tecnología en Redes",
        "ESTADO_PROGRAMA": "Activo",
        "CODIGO_CINE_CAMPO_DETALLADO": "061",
        "NIVEL_FORMACION": "Tecnológico",
        "CODIGO_SNIES_PROGRAMA": "5",
        "VALOR_MATRICULA": "2000000",
        "DESCRIPCION": "",
    }])
    parser = SNIESCSVParser()
    records = parser.parse(data)
    assert records[0]["tipo"] == "tecnologica"


# --- ETLIntegrity ---

def test_validate_url_allows_snies_domain():
    url = ETLIntegrity.validate_url("https://snies.mineducacion.gov.co/data.csv")
    assert "snies.mineducacion.gov.co" in url


def test_validate_url_blocks_private_192():
    with pytest.raises(SSRFBlockedError):
        ETLIntegrity.validate_url("http://192.168.1.1/data")


def test_validate_url_blocks_private_10():
    with pytest.raises(SSRFBlockedError):
        ETLIntegrity.validate_url("http://10.0.0.1/data")


def test_validate_url_blocks_localhost():
    with pytest.raises(SSRFBlockedError):
        ETLIntegrity.validate_url("http://localhost/data")


def test_validate_url_blocks_127():
    with pytest.raises(SSRFBlockedError):
        ETLIntegrity.validate_url("http://127.0.0.1/data")


def test_validate_url_blocks_unknown_domain():
    with pytest.raises(SSRFBlockedError):
        ETLIntegrity.validate_url("https://evil.com/data.csv")


def test_check_hash_match():
    data = b"test payload"
    expected = hashlib.sha256(data).hexdigest()
    result = ETLIntegrity.check_hash(data, expected)
    assert result == expected


def test_check_hash_no_expected_returns_actual():
    data = b"test payload"
    result = ETLIntegrity.check_hash(data)
    assert result == hashlib.sha256(data).hexdigest()


def test_check_hash_mismatch_raises():
    with pytest.raises(IntegrityCheckError):
        ETLIntegrity.check_hash(b"data", "wrong_hash_value")


# --- ParserFactory ---

def test_factory_returns_snies_parser():
    parser = ParserFactory.get_parser("snies")
    assert isinstance(parser, SNIESCSVParser)


def test_factory_case_insensitive():
    parser = ParserFactory.get_parser("SNIES")
    assert isinstance(parser, SNIESCSVParser)


def test_factory_raises_on_unknown_source():
    with pytest.raises(ValueError, match="Unknown ETL source"):
        ParserFactory.get_parser("linkedin")


def test_factory_available_sources_contains_snies_ole():
    sources = ParserFactory.available_sources()
    assert "snies" in sources
    assert "ole" in sources
