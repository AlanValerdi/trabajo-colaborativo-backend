"""Pruebas de HU-15 (bloqueo), HU-16 (colaboración), HU-18 (historial) y HU-21 (feed)."""
from datetime import datetime, timedelta, timezone

from app.models.collaboration import ReportCollaboration
from app.models.comment import Comment

FOLIO = "INC-TEST-0001"


def _status(api, user, status, comment=None):
    body = {"status": status}
    if comment is not None:
        body["comment"] = comment
    return api.post(f"/reports/{FOLIO}/status", json=body, headers=api.as_user(user))


def _collab(api, user, reason="Se necesita apoyo eléctrico"):
    return api.post(
        f"/reports/{FOLIO}/collaborations",
        json={"category": "electricidad", "reason": reason},
        headers=api.as_user(user),
    )


# ---------------------------------------------------------------- HU-15
def test_bloqueo_exige_comentario(api, world):
    r = _status(api, world["users"]["tecnico"], "bloqueada")
    assert r.status_code == 422


def test_bloquear_y_volver_a_en_progreso(api, world):
    tec = world["users"]["tecnico"]
    assert _status(api, tec, "en_progreso").status_code == 200
    assert _status(api, tec, "bloqueada", "Falta refacción").status_code == 200
    r = _status(api, tec, "en_progreso")
    assert r.status_code == 200 and r.json()["status"] == "en_progreso"


def test_desbloquear_regresa_a_asignada(api, world):
    """Bug: una incidencia bloqueada desde Asignada no podía volver a Asignada."""
    tec = world["users"]["tecnico"]
    assert _status(api, tec, "bloqueada", "Sin acceso al aula").status_code == 200
    r = _status(api, tec, "asignada")
    assert r.status_code == 200, r.json()
    assert r.json()["status"] == "asignada"


def test_bloqueada_solo_vuelve_al_estado_previo(api, world):
    tec = world["users"]["tecnico"]
    _status(api, tec, "en_progreso")
    _status(api, tec, "bloqueada", "Falta refacción")
    assert _status(api, tec, "resuelta").status_code == 409


def test_reportante_no_puede_bloquear(api, world):
    r = _status(api, world["users"]["reportante"], "bloqueada", "x")
    assert r.status_code == 403


# ---------------------------------------------------------------- HU-16
def test_colaboracion_se_crea_y_lista(api, world):
    tec = world["users"]["tecnico"]
    r = _collab(api, tec)
    assert r.status_code == 201
    assert r.json()["status"] == "solicitada"
    lst = api.get(f"/reports/{FOLIO}/collaborations", headers=api.as_user(tec))
    assert len(lst.json()) == 1


def test_colaboracion_misma_especialidad_rechazada(api, world):
    tec = world["users"]["tecnico"]
    r = api.post(f"/reports/{FOLIO}/collaborations", json={"category": "ti", "reason": "x"}, headers=api.as_user(tec))
    assert r.status_code == 409


def test_solicitante_no_puede_aceptar_su_propia_solicitud(api, world):
    """Bug: el técnico que solicita la colaboración también podía aceptarla."""
    tec = world["users"]["tecnico"]
    cid = _collab(api, tec).json()["id"]
    r = api.patch(f"/collaborations/{cid}", json={"status": "aceptada"}, headers=api.as_user(tec))
    assert r.status_code == 403


def test_responsable_acepta_y_queda_registrado_quien_respondio(api, world):
    tec, resp = world["users"]["tecnico"], world["users"]["responsable"]
    cid = _collab(api, tec).json()["id"]
    r = api.patch(f"/collaborations/{cid}", json={"status": "aceptada"}, headers=api.as_user(resp))
    assert r.status_code == 200
    assert r.json()["respondedById"] == resp.id
    hist = api.get(f"/reports/{FOLIO}/history", headers=api.as_user(tec)).json()
    resp_entries = [h for h in hist if h["type"] == "colaboracion" and "aceptada" in h["summary"]]
    assert resp_entries and resp_entries[0]["actorName"] == resp.name


def test_solicitante_puede_retirar_su_solicitud_pendiente(api, world):
    tec = world["users"]["tecnico"]
    cid = _collab(api, tec).json()["id"]
    r = api.patch(f"/collaborations/{cid}", json={"status": "rechazada"}, headers=api.as_user(tec))
    assert r.status_code == 200


def test_solicitante_marca_completada(api, world):
    tec, resp = world["users"]["tecnico"], world["users"]["responsable"]
    cid = _collab(api, tec).json()["id"]
    api.patch(f"/collaborations/{cid}", json={"status": "aceptada"}, headers=api.as_user(resp))
    r = api.patch(f"/collaborations/{cid}", json={"status": "completada"}, headers=api.as_user(tec))
    assert r.status_code == 200 and r.json()["status"] == "completada"


def test_transicion_invalida_de_colaboracion(api, world):
    tec, resp = world["users"]["tecnico"], world["users"]["responsable"]
    cid = _collab(api, tec).json()["id"]
    r = api.patch(f"/collaborations/{cid}", json={"status": "completada"}, headers=api.as_user(resp))
    assert r.status_code == 409


# ---------------------------------------------------------------- HU-18
def test_historial_cronologico_y_estable(api, world, db):
    tec, resp = world["users"]["tecnico"], world["users"]["responsable"]
    _status(api, tec, "en_progreso")
    _status(api, tec, "bloqueada", "Falta refacción")
    _collab(api, resp)
    hist = api.get(f"/reports/{FOLIO}/history", headers=api.as_user(tec)).json()
    stamps = [h["timestamp"] for h in hist]
    assert stamps == sorted(stamps)
    types = [h["type"] for h in hist]
    assert types[0] == "creacion" and "estado" in types and "colaboracion" in types
    bloqueo = [h for h in hist if "bloqueó" in h["summary"]]
    assert bloqueo and "Falta refacción" in bloqueo[0]["summary"]


def test_historial_folio_inexistente(api, world):
    r = api.get("/reports/NOEXISTE/history", headers=api.as_user(world["users"]["tecnico"]))
    assert r.status_code == 404


# ---------------------------------------------------------------- HU-21
def test_feed_ordenado_y_respeta_limite(api, world, db):
    rep, tec = world["report"], world["users"]["tecnico"]
    base = datetime.now(timezone.utc) + timedelta(minutes=1)
    for i in range(30):
        db.add(Comment(report_id=rep.id, user_id=tec.id, content=f"comentario {i}", created_at=base + timedelta(minutes=i)))
    db.commit()
    feed = api.get("/activity/recent?limit=5", headers=api.as_user(tec)).json()
    assert len(feed) == 5
    stamps = [f["timestamp"] for f in feed]
    assert stamps == sorted(stamps, reverse=True)
    assert "comentario 29" in feed[0]["summary"]
    assert feed[0]["reportFolio"] == FOLIO


def test_feed_incluye_eventos_de_varias_fuentes(api, world):
    tec, resp = world["users"]["tecnico"], world["users"]["responsable"]
    _status(api, tec, "en_progreso")
    _collab(api, resp)
    feed = api.get("/activity/recent?limit=20", headers=api.as_user(tec)).json()
    assert {"estado", "colaboracion", "creacion"} <= {f["type"] for f in feed}


def test_feed_limite_invalido(api, world):
    r = api.get("/activity/recent?limit=0", headers=api.as_user(world["users"]["tecnico"]))
    assert r.status_code == 422
