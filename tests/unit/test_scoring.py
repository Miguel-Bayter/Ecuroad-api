import pytest
from unittest.mock import MagicMock

from app.utils.scoring import calculate_score, rank_careers, ScoredCarrera


def make_carrera(**kwargs):
    defaults = {
        "nombre": "Test Career",
        "slug": "test-career",
        "tipo": "universitaria",
        "empleabilidad": 80.0,
        "tasaEmpleabilidad12m": 75.0,
        "demandaPorRegion": {"bogotá": 80.0},
        "costoSemestre": 3000000,
        "tags": ["tech", "software"],
    }
    defaults.update(kwargs)
    obj = MagicMock()
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


def base_perfil(**kwargs):
    defaults = {"ciudad": "otra", "presupuesto": 0, "tipoCarrera": "cualquiera", "intereses": []}
    defaults.update(kwargs)
    return defaults


def test_employment_rate_full_30_pts():
    carrera = make_carrera(tasaEmpleabilidad12m=100.0, demandaPorRegion={}, costoSemestre=0, tags=[])
    score = calculate_score(carrera, base_perfil())
    assert score == 30.0


def test_employment_rate_zero():
    carrera = make_carrera(tasaEmpleabilidad12m=0.0, empleabilidad=0.0, demandaPorRegion={}, costoSemestre=0, tags=[])
    score = calculate_score(carrera, base_perfil())
    assert score == 0.0


def test_regional_demand_full_25_pts():
    carrera = make_carrera(tasaEmpleabilidad12m=0.0, empleabilidad=0.0, demandaPorRegion={"bogotá": 100.0}, costoSemestre=0, tags=[])
    score = calculate_score(carrera, base_perfil(ciudad="Bogotá"))
    assert score == 25.0


def test_regional_demand_case_insensitive():
    carrera = make_carrera(tasaEmpleabilidad12m=0.0, empleabilidad=0.0, demandaPorRegion={"bogotá": 100.0}, costoSemestre=0, tags=[])
    score = calculate_score(carrera, base_perfil(ciudad="BOGOTÁ"))
    assert score == 25.0


def test_budget_fit_full_15_pts():
    carrera = make_carrera(tasaEmpleabilidad12m=0.0, empleabilidad=0.0, demandaPorRegion={}, costoSemestre=3000000, tags=[])
    score = calculate_score(carrera, base_perfil(presupuesto=3000000))
    assert score == 15.0


def test_budget_fit_partial_7_pts():
    carrera = make_carrera(tasaEmpleabilidad12m=0.0, empleabilidad=0.0, demandaPorRegion={}, costoSemestre=3000000, tags=[])
    score = calculate_score(carrera, base_perfil(presupuesto=2500000))
    assert score == 7.0


def test_budget_fit_none_when_too_low():
    carrera = make_carrera(tasaEmpleabilidad12m=0.0, empleabilidad=0.0, demandaPorRegion={}, costoSemestre=3000000, tags=[])
    score = calculate_score(carrera, base_perfil(presupuesto=1000000))
    assert score == 0.0


def test_tipo_match_full_20_pts():
    carrera = make_carrera(tasaEmpleabilidad12m=0.0, empleabilidad=0.0, demandaPorRegion={}, costoSemestre=0, tipo="universitaria", tags=[])
    score = calculate_score(carrera, base_perfil(tipoCarrera="universitaria"))
    assert score == 20.0


def test_tipo_cualquiera_grants_20_pts():
    carrera = make_carrera(tasaEmpleabilidad12m=0.0, empleabilidad=0.0, demandaPorRegion={}, costoSemestre=0, tipo="tecnica", tags=[])
    score = calculate_score(carrera, base_perfil(tipoCarrera="cualquiera"))
    assert score == 20.0


def test_tag_overlap_partial():
    carrera = make_carrera(tasaEmpleabilidad12m=0.0, empleabilidad=0.0, demandaPorRegion={}, costoSemestre=0, tags=["tech", "software", "web"])
    score = calculate_score(carrera, base_perfil(intereses=["tech", "web"]))
    assert score == pytest.approx(6.67, rel=0.01)


def test_tag_overlap_full_10_pts():
    carrera = make_carrera(tasaEmpleabilidad12m=0.0, empleabilidad=0.0, demandaPorRegion={}, costoSemestre=0, tags=["tech"])
    score = calculate_score(carrera, base_perfil(intereses=["tech"]))
    assert score == 10.0


def test_tag_overlap_empty_intereses():
    carrera = make_carrera(tasaEmpleabilidad12m=0.0, empleabilidad=0.0, demandaPorRegion={}, costoSemestre=0, tags=["tech"])
    score = calculate_score(carrera, base_perfil(intereses=[]))
    assert score == 0.0


def test_rank_returns_descending_order():
    careers = [
        make_carrera(slug=f"c{i}", empleabilidad=float(i * 10), tasaEmpleabilidad12m=float(i * 10), demandaPorRegion={}, costoSemestre=0, tags=[])
        for i in range(5)
    ]
    ranked = rank_careers(careers, base_perfil(), limit=5)
    scores = [r.score for r in ranked]
    assert scores == sorted(scores, reverse=True)


def test_rank_respects_limit():
    careers = [make_carrera(slug=f"c{i}", tasaEmpleabilidad12m=50.0, demandaPorRegion={}, costoSemestre=0, tags=[]) for i in range(10)]
    ranked = rank_careers(careers, base_perfil(), limit=3)
    assert len(ranked) == 3


def test_rank_returns_scored_carrera_objects():
    careers = [make_carrera(slug="c1", tasaEmpleabilidad12m=80.0, demandaPorRegion={}, costoSemestre=0, tags=[])]
    ranked = rank_careers(careers, base_perfil())
    assert isinstance(ranked[0], ScoredCarrera)
    assert ranked[0].score >= 0
