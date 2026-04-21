import csv
import io
from app.utils.etl.base import BaseParser

CINE_TO_CATEGORY = {
    "061": "tech", "062": "tech",
    "031": "comunicacion", "032": "social",
    "041": "negocios", "042": "negocios",
    "051": "ingenieria", "052": "ingenieria",
    "071": "ingenieria", "072": "ingenieria",
    "081": "agro",
    "091": "salud", "092": "salud",
    "021": "arte",
    "011": "educacion", "012": "educacion",
    "015": "deporte",
    "023": "justicia",
}


class SNIESCSVParser(BaseParser):
    def parse(self, data: bytes) -> list[dict]:
        text = data.decode("utf-8-sig", errors="replace")
        reader = csv.DictReader(io.StringIO(text))
        records = []
        for row in reader:
            if not self.validate_record(row):
                continue
            cine = row.get("CODIGO_CINE_CAMPO_DETALLADO", "")[:3]
            records.append({
                "nombre": row.get("NOMBRE_PROGRAMA", "").strip(),
                "slug": row.get("NOMBRE_PROGRAMA", "").strip().lower().replace(" ", "-"),
                "categoria": CINE_TO_CATEGORY.get(cine, "otro"),
                "tipo": self._map_tipo(row.get("NIVEL_FORMACION", "")),
                "sniesCode": row.get("CODIGO_SNIES_PROGRAMA", ""),
                "cineCode": cine,
                "costoSemestre": int(row.get("VALOR_MATRICULA", 0) or 0),
                "descripcion": row.get("DESCRIPCION", ""),
                "fuenteSalario": "SNIES",
            })
        return records

    def validate_record(self, record: dict) -> bool:
        return bool(record.get("NOMBRE_PROGRAMA")) and record.get("ESTADO_PROGRAMA") == "Activo"

    def _map_tipo(self, nivel: str) -> str:
        nivel = nivel.lower()
        if "universitario" in nivel or "profesional" in nivel:
            return "universitaria"
        if "tecnológico" in nivel or "tecnologico" in nivel:
            return "tecnologica"
        if "técnico" in nivel or "tecnico" in nivel:
            return "tecnica"
        return "universitaria"
