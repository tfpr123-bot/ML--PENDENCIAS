from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from datetime import datetime
import shutil
import uuid

app = FastAPI(title="Melhoria Contínua")

# =========================
# CONFIGURAÇÕES
# =========================

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"

UPLOAD_DIR.mkdir(exist_ok=True)

app.add_middleware(
    SessionMiddleware,
    secret_key="melhoria-continua-chave-secreta"
)

app.mount(
    "/uploads",
    StaticFiles(directory=str(UPLOAD_DIR)),
    name="uploads"
)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# =========================
# DADOS INICIAIS
# =========================

SETORES = [
    "A01",
    "A02",
    "A03",
    "A04",
    "A05",
    "A06",
    "A07",
    "A08",
    "BC"
]

USUARIOS = {
    "marlon": {
        "senha": "1234",
        "nome": "Marlon",
        "perfil": "admin",
        "setor": None
    },

    "lider_a01": {
        "senha": "1234",
        "nome": "Líder A01",
        "perfil": "lider",
        "setor": "A01"
    },

    "lider_a02": {
        "senha": "1234",
        "nome": "Líder A02",
        "perfil": "lider",
        "setor": "A02"
    },

    "lider_a03": {
        "senha": "1234",
        "nome": "Líder A03",
        "perfil": "lider",
        "setor": "A03"
    },

    "lider_a04": {
        "senha": "1234",
        "nome": "Líder A04",
        "perfil": "lider",
        "setor": "A04"
    },

    "lider_a05": {
        "senha": "1234",
        "nome": "Líder A05",
        "perfil": "lider",
        "setor": "A05"
    },

    "lider_a06": {
        "senha": "1234",
        "nome": "Líder A06",
        "perfil": "lider",
        "setor": "A06"
    },

    "lider_a07": {
        "senha": "1234",
        "nome": "Líder A07",
        "perfil": "lider",
        "setor": "A07"
    },

    "lider_a08": {
        "senha": "1234",
        "nome": "Líder A08",
        "perfil": "lider",
        "setor": "A08"
    },

    "lider_bc": {
        "senha": "1234",
        "nome": "Líder BC",
        "perfil": "lider",
        "setor": "BC"
    }
}


# =========================
# BANCO TEMPORÁRIO
# =========================

pendencias = []

contador = 1


# =========================
# FUNÇÕES AUXILIARES
# =========================

def usuario_logado(request: Request):
    username = request.session.get("usuario")

    if not username:
        return None

    return USUARIOS.get(username)


def gerar_id():
    global contador

    numero = f"MC-{contador:05d}"
    contador += 1

    return numero


def salvar_foto(arquivo: UploadFile):
    if not arquivo or not arquivo.filename:
        return None

    extensao = Path(arquivo.filename).suffix.lower()

    nome_arquivo = f"{uuid.uuid4().hex}{extensao}"

    caminho = UPLOAD_DIR / nome_arquivo

    with caminho.open("wb") as buffer:
        shutil.copyfileobj(arquivo.file, buffer)

    return nome_arquivo


# =========================
# LOGIN
# =========================

@app.get("/", response_class=HTMLResponse)
async def inicio(request: Request):

    usuario = usuario_logado(request)

    if usuario:
        return RedirectResponse(
            "/dashboard",
            status_code=303
        )

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request
        }
    )


@app.post("/login")
async def login(
    request: Request,
    usuario: str = Form(...),
    senha: str = Form(...)
):

    dados = USUARIOS.get(usuario)

    if not dados or dados["senha"] != senha:

        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "erro": "Usuário ou senha inválidos."
            },
            status_code=401
        )

    request.session["usuario"] = usuario

    return RedirectResponse(
        "/dashboard",
        status_code=303
    )


@app.get("/logout")
async def logout(request: Request):

    request.session.clear()

    return RedirectResponse(
        "/",
        status_code=303
    )


# =========================
# DASHBOARD
# =========================

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):

    usuario = usuario_logado(request)

    if not usuario:
        return RedirectResponse(
            "/",
            status_code=303
        )

    if usuario["perfil"] == "admin":

        lista = pendencias

    else:

        lista = [
            p for p in pendencias
            if p["setor"] == usuario["setor"]
        ]

    pendentes = len([
        p for p in lista
        if p["status"] == "PENDENTE"
    ])

    aguardando = len([
        p for p in lista
        if p["status"] == "AGUARDANDO VALIDAÇÃO"
    ])

    validadas = len([
        p for p in lista
        if p["status"] == "VALIDADO"
    ])

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "usuario": usuario,
            "pendencias": lista,
            "setores": SETORES,
            "pendentes": pendentes,
            "aguardando": aguardando,
            "validadas": validadas
        }
    )


# =========================
# NOVA PENDÊNCIA
# =========================

@app.get("/pendencia/nova", response_class=HTMLResponse)
async def nova_pendencia_form(request: Request):

    usuario = usuario_logado(request)

    if not usuario or usuario["perfil"] != "admin":
        return RedirectResponse(
            "/dashboard",
            status_code=303
        )

    return templates.TemplateResponse(
        "nova_pendencia.html",
        {
            "request": request,
            "setores": SETORES
        }
    )


@app.post("/pendencia/nova")
async def criar_pendencia(
    request: Request,
    setor: str = Form(...),
    local: str = Form(...),
    descricao: str = Form(...),
    categoria: str = Form(...),
    prioridade: str = Form(...),
    prazo: str = Form(...),
    foto: UploadFile = File(None)
):

    usuario = usuario_logado(request)

    if not usuario or usuario["perfil"] != "admin":
        return RedirectResponse(
            "/dashboard",
            status_code=303
        )

    foto_nome = salvar_foto(foto)

    nova = {
        "id": gerar_id(),
        "setor": setor,
        "local": local,
        "descricao": descricao,
        "categoria": categoria,
        "prioridade": prioridade,
        "prazo": prazo,
        "foto_antes": foto_nome,
        "status": "PENDENTE",
        "data_criacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "data_resolucao": None,
        "observacao_resolucao": None,
        "foto_depois": None
    }

    pendencias.append(nova)

    return RedirectResponse(
        "/dashboard",
        status_code=303
    )


# =========================
# VISUALIZAR PENDÊNCIA
# =========================

@app.get("/pendencia/{pendencia_id}", response_class=HTMLResponse)
async def visualizar_pendencia(
    request: Request,
    pendencia_id: str
):

    usuario = usuario_logado(request)

    if not usuario:
        return RedirectResponse(
            "/",
            status_code=303
        )

    pendencia = next(
        (
            p for p in pendencias
            if p["id"] == pendencia_id
        ),
        None
    )

    if not pendencia:
        return HTMLResponse(
            "Pendência não encontrada.",
            status_code=404
        )

    if usuario["perfil"] == "lider":
        if pendencia["setor"] != usuario["setor"]:
            return HTMLResponse(
                "Acesso não permitido.",
                status_code=403
            )

    return templates.TemplateResponse(
        "pendencia.html",
        {
            "request": request,
            "usuario": usuario,
            "pendencia": pendencia
        }
    )


# =========================
# RESOLVER PENDÊNCIA
# =========================

@app.post("/pendencia/{pendencia_id}/resolver")
async def resolver_pendencia(
    request: Request,
    pendencia_id: str,
    data_resolucao: str = Form(...),
    observacao: str = Form(...),
    foto: UploadFile = File(None)
):

    usuario = usuario_logado(request)

    if not usuario or usuario["perfil"] != "lider":
        return RedirectResponse(
            "/dashboard",
            status_code=303
        )

    pendencia = next(
        (
            p for p in pendencias
            if p["id"] == pendencia_id
        ),
        None
    )

    if not pendencia:
        return HTMLResponse(
            "Pendência não encontrada.",
            status_code=404
        )

    if pendencia["setor"] != usuario["setor"]:
        return HTMLResponse(
            "Acesso não permitido.",
            status_code=403
        )

    foto_nome = salvar_foto(foto)

    pendencia["data_resolucao"] = data_resolucao
    pendencia["observacao_resolucao"] = observacao
    pendencia["foto_depois"] = foto_nome
    pendencia["status"] = "AGUARDANDO VALIDAÇÃO"

    return RedirectResponse(
        "/dashboard",
        status_code=303
    )


# =========================
# VALIDAR
# =========================

@app.post("/pendencia/{pendencia_id}/validar")
async def validar_pendencia(
    request: Request,
    pendencia_id: str
):

    usuario = usuario_logado(request)

    if not usuario or usuario["perfil"] != "admin":
        return RedirectResponse(
            "/dashboard",
            status_code=303
        )

    pendencia = next(
        (
            p for p in pendencias
            if p["id"] == pendencia_id
        ),
        None
    )

    if pendencia:
        pendencia["status"] = "VALIDADO"

    return RedirectResponse(
        "/dashboard",
        status_code=303
    )


# =========================
# REABRIR
# =========================

@app.post("/pendencia/{pendencia_id}/reabrir")
async def reabrir_pendencia(
    request: Request,
    pendencia_id: str
):

    usuario = usuario_logado(request)

    if not usuario or usuario["perfil"] != "admin":
        return RedirectResponse(
            "/dashboard",
            status_code=303
        )

    pendencia = next(
        (
            p for p in pendencias
            if p["id"] == pendencia_id
        ),
        None
    )

    if pendencia:
        pendencia["status"] = "PENDENTE"
        pendencia["data_resolucao"] = None
        pendencia["observacao_resolucao"] = None
        pendencia["foto_depois"] = None

    return RedirectResponse(
        "/dashboard",
        status_code=303
    )
