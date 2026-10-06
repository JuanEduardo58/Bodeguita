from tests.conftest import auth_header, login


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_login_y_me(client, crear_usuario):
    crear_usuario("ana@colmado.do")
    # El correo no distingue mayúsculas.
    r = client.get("/api/auth/me", headers=auth_header(client, "ANA@colmado.do"))
    assert r.status_code == 200
    assert r.json()["email"] == "ana@colmado.do"
    assert r.json()["rol"] == "dueno"


def test_login_clave_incorrecta(client, crear_usuario):
    crear_usuario("ana@colmado.do")
    assert login(client, "ana@colmado.do", "otra-clave").status_code == 401
    assert login(client, "nadie@colmado.do").status_code == 401


def test_usuario_inactivo_no_entra(client, db, crear_usuario):
    assert login(client, crear_usuario("off@colmado.do", activo=False).email).status_code == 401

    # Si lo desactivan después del login, su token deja de servir.
    usuario = crear_usuario("luego@colmado.do")
    headers = auth_header(client, usuario.email)
    usuario.activo = False
    db.flush()
    assert client.get("/api/auth/me", headers=headers).status_code == 401


def test_token_invalido(client):
    assert client.get("/api/auth/me").status_code == 401
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer basura"})
    assert r.status_code == 401


def test_dueno_crea_cajero_en_su_negocio(client, crear_usuario):
    dueno = crear_usuario("dueno@colmado.do")
    headers = auth_header(client, dueno.email)
    nuevo = {"nombre": "Pedro", "email": "Pedro@Colmado.do", "password": "12345678"}

    r = client.post("/api/auth/usuarios", json=nuevo, headers=headers)
    assert r.status_code == 201
    assert r.json()["id_negocio"] == dueno.id_negocio
    assert r.json()["rol"] == "cajero"
    assert r.json()["email"] == "pedro@colmado.do"

    assert client.post("/api/auth/usuarios", json=nuevo, headers=headers).status_code == 409


def test_cajero_no_crea_usuarios(client, crear_usuario):
    crear_usuario("caja@colmado.do", rol="cajero")
    nuevo = {"nombre": "X", "email": "x@colmado.do", "password": "12345678"}
    r = client.post(
        "/api/auth/usuarios", json=nuevo, headers=auth_header(client, "caja@colmado.do")
    )
    assert r.status_code == 403


def test_clave_corta_rechazada(client, crear_usuario):
    crear_usuario("dueno@colmado.do")
    nuevo = {"nombre": "X", "email": "x@colmado.do", "password": "corta"}
    r = client.post(
        "/api/auth/usuarios", json=nuevo, headers=auth_header(client, "dueno@colmado.do")
    )
    assert r.status_code == 422
