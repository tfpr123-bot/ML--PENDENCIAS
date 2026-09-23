from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from pathlib import Path
from datetime import datetime
import uuid
import os

from supabase import create_client, Client


app = FastAPI(title="Melhoria Contínua")

BASE_DIR = Path(__file__).resolve().parent


# =========================================================
# SUPABASE
# =========================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL e SUPABASE_KEY precisam estar configurados."
    )

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

BUCKET_FOTOS = "pendencias"


# =========================================================
# CONFIGURAÇÕES DO FASTAPI
# =========================================================

app.add_middleware(
    SessionMiddleware,
    secret_key="melhoria-contínua-chave-secreta"
)

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)


# =========================================================
# SETORES
# =========================================================

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


# =========================================================
# USUÁRIOS
# =========================================================

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


# =========================================================
# USUÁRIO LOGADO
# =========================================================

def usuario_logado(request: Request):

    username = request.session.get("usuario")

    if not username:
        return None

    return USUARIOS.get(username)


# =========================================================
# SALVAR FOTO NO SUPABASE STORAGE
# =========================================================

async def salvar_foto(arquivo: UploadFile):

    if not arquivo or not arquivo.filename:
        return None

    extensao = Path(arquivo.filename).suffix.lower()

    nome_arquivo = f"{uuid.uuid4().hex}{extensao}"

    conteudo = await arquivo.read()

    content_type = arquivo.content_type or "application/octet-stream"

    try:

        supabase.storage \
            .from_(BUCKET_FOTOS) \
            .upload(
                nome_arquivo,
                conteudo,
                {
                    "content-type": content_type,
                    "upsert": "false"
                }
            )

    except Exception as erro:

        print("ERRO AO ENVIAR FOTO PARA O SUPABASE:")
        print(erro)

        return None

    return nome_arquivo


# =========================================================
# ROTA PARA EXIBIR AS FOTOS
# =========================================================
#
# O HTML continua usando:
#
# /uploads/nome-da-foto.jpg
#
# Mas agora essa rota redireciona para o Supabase Storage.
# =========================================================

@app.get("/uploads/{arquivo:path}")
async def visualizar_foto(arquivo: str):

    if not arquivo:
        return HTMLResponse(
            "Arquivo não informado.",
            status_code=400
        )

    try:

        url = (
            supabase
            .storage
            .from_(BUCKET_FOTOS)
            .get_public_url(arquivo)
        )

        return RedirectResponse(
            url,
            status_code=302
        )

    except Exception as erro:

        print("ERRO AO GERAR URL DA FOTO:")
        print(erro)

        return HTMLResponse(
            "Foto não encontrada.",
            status_code=404
        )


# =========================================================
# FORMATAR PENDÊNCIA
# =========================================================

def formatar_pendencia(p):

    if not p:
        return None

    db_id = p.get("id")

    try:

        codigo = f"MC-{int(db_id):05d}"

    except:

        codigo = str(db_id)

    data_criacao = p.get("data_criacao")

    if data_criacao:

        try:

            dt = datetime.fromisoformat(
                data_criacao.replace("Z", "+00:00")
            )

            data_criacao_formatada = dt.strftime(
                "%d/%m/%Y %H:%M"
            )

        except:

            data_criacao_formatada = str(data_criacao)

    else:

        data_criacao_formatada = None

    return {

        "id": codigo,

        "db_id": db_id,

        "setor": p.get("setor"),

        "local": p.get("local"),

        "descricao": p.get("descricao"),

        "categoria": p.get("categoria"),

        "prioridade": p.get("prioridade"),

        "prazo": p.get("prazo"),

        "foto_antes": p.get("foto_antes"),

        "status": p.get("status"),

        "data_criacao": data_criacao_formatada,

        "data_resolucao": p.get("data_resolucao"),

        "observacao_resolucao": p.get(
            "observacao_resolucao"
        ),

        "foto_depois": p.get("foto_depois"),

        "criado_por": p.get("criado_por"),

        "resolvido_por": p.get("resolvido_por")
    }


# =========================================================
# BUSCAR TODAS AS PENDÊNCIAS
# =========================================================

def buscar_todas_pendencias():

    resposta = (
        supabase
        .table("pendencias")
        .select("*")
        .order("id", desc=True)
        .execute()
    )

    dados = resposta.data or []

    return [
        formatar_pendencia(p)
        for p in dados
    ]


# =========================================================
# BUSCAR UMA PENDÊNCIA
# =========================================================

def buscar_pendencia(codigo):

    try:

        if codigo.startswith("MC-"):

            db_id = int(
                codigo.replace("MC-", "")
            )

        else:

            db_id = int(codigo)

    except:

        return None

    resposta = (
        supabase
        .table("pendencias")
        .select("*")
        .eq("id", db_id)
        .limit(1)
        .execute()
    )

    if not resposta.data:
        return None

    return formatar_pendencia(
        resposta.data[0]
    )


# =========================================================
# LOGIN
# =========================================================

@app.get(
    "/",
    response_class=HTMLResponse
)
async def inicio(request: Request):

    usuario = usuario_logado(request)

    if usuario:

        return RedirectResponse(
            "/dashboard",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={}
    )


# =========================================================
# PROCESSAR LOGIN
# =========================================================

@app.post("/login")
async def login(
    request: Request,
    usuario: str = Form(...),
    senha: str = Form(...)
):

    dados = USUARIOS.get(usuario)

    if not dados or dados["senha"] != senha:

        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "erro": "Usuário ou senha inválidos."
            },
            status_code=401
        )

    request.session["usuario"] = usuario

    return RedirectResponse(
        "/dashboard",
        status_code=303
    )


# =========================================================
# LOGOUT
# =========================================================

@app.get("/logout")
async def logout(request: Request):

    request.session.clear()

    return RedirectResponse(
        "/",
        status_code=303
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.get(
    "/dashboard",
    response_class=HTMLResponse
)
async def dashboard(request: Request):

    usuario = usuario_logado(request)

    if not usuario:

        return RedirectResponse(
            "/",
            status_code=303
        )

    lista = buscar_todas_pendencias()

    # Líder só enxerga seu setor

    if usuario["perfil"] == "lider":

        lista = [
            p
            for p in lista
            if p["setor"] == usuario["setor"]
        ]

    pendentes = len([
        p
        for p in lista
        if p["status"] == "PENDENTE"
    ])

    aguardando = len([
        p
        for p in lista
        if p["status"] == "AGUARDANDO VALIDAÇÃO"
    ])

    validadas = len([
        p
        for p in lista
        if p["status"] == "VALIDADO"
    ])

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={

            "usuario": usuario,

            "pendencias": lista,

            "setores": SETORES,

            "pendentes": pendentes,

            "aguardando": aguardando,

            "validadas": validadas
        }
    )


# =========================================================
# FORMULÁRIO NOVA PENDÊNCIA
# =========================================================

@app.get(
    "/pendencia/nova",
    response_class=HTMLResponse
)
async def nova_pendencia_form(
    request: Request
):

    usuario = usuario_logado(request)

    if (
        not usuario
        or usuario["perfil"] != "admin"
    ):

        return RedirectResponse(
            "/dashboard",
            status_code=303
        )

    return templates.TemplateResponse(
        request=request,
        name="nova_pendencia.html",
        context={
            "setores": SETORES
        }
    )


# =========================================================
# CRIAR PENDÊNCIA
# =========================================================

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

    if (
        not usuario
        or usuario["perfil"] != "admin"
    ):

        return RedirectResponse(
            "/dashboard",
            status_code=303
        )

    # Salva foto no Supabase Storage

    foto_nome = await salvar_foto(foto)

    nova = {

        "setor": setor,

        "local": local,

        "descricao": descricao,

        "categoria": categoria,

        "prioridade": prioridade,

        "prazo": prazo,

        "foto_antes": foto_nome,

        "status": "PENDENTE",

        "criado_por": usuario["nome"]
    }

    supabase \
        .table("pendencias") \
        .insert(nova) \
        .execute()

    return RedirectResponse(
        "/dashboard",
        status_code=303
    )


# =========================================================
# VISUALIZAR PENDÊNCIA
# =========================================================

@app.get(
    "/pendencia/{pendencia_id}",
    response_class=HTMLResponse
)
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

    pendencia = buscar_pendencia(
        pendencia_id
    )

    if not pendencia:

        return HTMLResponse(
            "Pendência não encontrada.",
            status_code=404
        )

    # Líder só pode acessar seu setor

    if usuario["perfil"] == "lider":

        if (
            pendencia["setor"]
            != usuario["setor"]
        ):

            return HTMLResponse(
                "Acesso não permitido.",
                status_code=403
            )

    return templates.TemplateResponse(
        request=request,
        name="pendencia.html",
        context={

            "usuario": usuario,

            "pendencia": pendencia
        }
    )


# =========================================================
# RESOLVER PENDÊNCIA
# =========================================================

@app.post(
    "/pendencia/{pendencia_id}/resolver"
)
async def resolver_pendencia(

    request: Request,

    pendencia_id: str,

    data_resolucao: str = Form(...),

    observacao: str = Form(...),

    foto: UploadFile = File(None)
):

    usuario = usuario_logado(request)

    if (
        not usuario
        or usuario["perfil"] != "lider"
    ):

        return RedirectResponse(
            "/dashboard",
            status_code=303
        )

    pendencia = buscar_pendencia(
        pendencia_id
    )

    if not pendencia:

        return HTMLResponse(
            "Pendência não encontrada.",
            status_code=404
        )

    if (
        pendencia["setor"]
        != usuario["setor"]
    ):

        return HTMLResponse(
            "Acesso não permitido.",
            status_code=403
        )

    # Salva foto da resolução
    # no Supabase Storage

    foto_nome = await salvar_foto(foto)

    try:

        db_id = int(
            pendencia["db_id"]
        )

    except:

        return HTMLResponse(
            "ID da pendência inválido.",
            status_code=400
        )

    atualizacao = {

        "data_resolucao":
            data_resolucao,

        "observacao_resolucao":
            observacao,

        "foto_depois":
            foto_nome,

        "status":
            "AGUARDANDO VALIDAÇÃO",

        "resolvido_por":
            usuario["nome"]
    }

    supabase \
        .table("pendencias") \
        .update(atualizacao) \
        .eq("id", db_id) \
        .execute()

    return RedirectResponse(
        "/dashboard",
        status_code=303
    )


# =========================================================
# VALIDAR PENDÊNCIA
# =========================================================

@app.post(
    "/pendencia/{pendencia_id}/validar"
)
async def validar_pendencia(

    request: Request,

    pendencia_id: str
):

    usuario = usuario_logado(request)

    if (
        not usuario
        or usuario["perfil"] != "admin"
    ):

        return RedirectResponse(
            "/dashboard",
            status_code=303
        )

    pendencia = buscar_pendencia(
        pendencia_id
    )

    if pendencia:

        try:

            db_id = int(
                pendencia["db_id"]
            )

            supabase \
                .table("pendencias") \
                .update({
                    "status": "VALIDADO"
                }) \
                .eq("id", db_id) \
                .execute()

        except Exception as erro:

            print(
                "Erro ao validar pendência:"
            )

            print(erro)

    return RedirectResponse(
        "/dashboard",
        status_code=303
    )


# =========================================================
# REABRIR PENDÊNCIA
# =========================================================

@app.post(
    "/pendencia/{pendencia_id}/reabrir"
)
async def reabrir_pendencia(

    request: Request,

    pendencia_id: str
):

    usuario = usuario_logado(request)

    if (
        not usuario
        or usuario["perfil"] != "admin"
    ):

        return RedirectResponse(
            "/dashboard",
            status_code=303
        )

    pendencia = buscar_pendencia(
        pendencia_id
    )

    if pendencia:

        try:

            db_id = int(
                pendencia["db_id"]
            )

            supabase \
                .table("pendencias") \
                .update({

                    "status": "PENDENTE",

                    "data_resolucao": None,

                    "observacao_resolucao": None,

                    "foto_depois": None,

                    "resolvido_por": None

                }) \
                .eq("id", db_id) \
                .execute()

        except Exception as erro:

            print(
                "Erro ao reabrir pendência:"
            )

            print(erro)

    return RedirectResponse(
        "/dashboard",
        status_code=303
    )
