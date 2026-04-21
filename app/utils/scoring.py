from dataclasses import dataclass

from app.models.carrera import Carrera


@dataclass
class ScoredCarrera:
    carrera: Carrera
    score: float


def calculate_score(carrera: Carrera, perfil: dict) -> float:
    score = 0.0

    # Employment rate (30 pts max)
    emp_rate = carrera.tasaEmpleabilidad12m or carrera.empleabilidad or 0
    score += min(emp_rate / 100.0, 1.0) * 30

    # Regional demand (25 pts max)
    ciudad = perfil.get("ciudad", "").lower()
    regional_demand = carrera.demandaPorRegion.get(ciudad, 0.0)
    score += min(regional_demand / 100.0, 1.0) * 25

    # Budget fit (15 pts max)
    presupuesto = perfil.get("presupuesto", 0)
    if carrera.costoSemestre > 0:
        if presupuesto >= carrera.costoSemestre:
            score += 15
        elif presupuesto >= carrera.costoSemestre * 0.75:
            score += 7

    # Career type match (20 pts max)
    tipo_pref = perfil.get("tipoCarrera", "cualquiera")
    if tipo_pref in ("cualquiera", carrera.tipo):
        score += 20

    # Interest tag overlap (10 pts max)
    intereses = set(i.lower() for i in perfil.get("intereses", []))
    tags = set(t.lower() for t in carrera.tags)
    if tags:
        score += (len(intereses & tags) / len(tags)) * 10

    return round(score, 2)


def rank_careers(careers: list[Carrera], perfil: dict, limit: int = 10) -> list[ScoredCarrera]:
    scored = [ScoredCarrera(c, calculate_score(c, perfil)) for c in careers]
    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:limit]
