import bcrypt
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import os
import traceback
from fastapi import Form
from fastapi.responses import RedirectResponse
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
app = FastAPI()

# Chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Définir l'application FastAPI
app = FastAPI()

# Monter les fichiers statiques
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    with open(os.path.join(BASE_DIR, "database", "data.json"), "r") as f:
        properties = json.load(f)
    return templates.TemplateResponse("principal.html", {"request": request, "properties": properties})

# 🔹 Route GET pour afficher la page de connexion
@app.get("/login", response_class=HTMLResponse)
async def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 🔹 Route POST pour traiter la connexion
@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    users_file = os.path.join(BASE_DIR, "database", "users.json")

    # 🔸 Chargement sécurisé des utilisateurs
    try:
        users_file = os.path.join(BASE_DIR, "database", "users.json")

        if os.path.exists(users_file):
            with open(users_file, "r") as f:
                users = json.load(f)
        else:
            users = []

        user = next((u for u in users if u.get("email") == email), None)

        if user is None or not bcrypt.checkpw(password.encode(), user["password"].encode()):
            return RedirectResponse(url="/login?message=error", status_code=302)

        session_data = {"user": user["email"]}
        session_file = os.path.join(BASE_DIR, "database", "session.json")
        with open(session_file, "w") as f:
            json.dump(session_data, f)

        return RedirectResponse(url="/index", status_code=302)

    except Exception as e:
        print("Erreur :", e)
        print(traceback.format_exc())  # Affiche l'erreur complète dans le terminal
        return {"error": "Une erreur interne s'est produite."}

    # 🔸 Sauvegarde de session sécurisée
    session_data = {"user": user["email"]}
    session_file = os.path.join(BASE_DIR, "database", "session.json")
    with open(session_file, "w") as f:
        json.dump(session_data, f)

    return RedirectResponse(url="/index", status_code=302)



@app.get("/register", response_class=HTMLResponse)
async def show_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirme_password: str = Form(...)
):
    users_file = os.path.join(BASE_DIR, "database", "users.json")

    # Vérification si les mots de passe correspondent
    if password != confirme_password:
        return templates.TemplateResponse("register.html", {
            "request": request,
            "error": "Les mots de passe ne sont pas identiques"
        })

    # Charger les utilisateurs existants
    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            users = json.load(f)
    else:
        users = []

    # Vérifier si l'utilisateur existe déjà
    for user in users:
        if user["username"] == username or user.get("email") == email:
            print("lolololo")
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Nom d'utilisateur ou email déjà utilisé"
            })

    # Ajouter le nouvel utilisateur
    users.append({
        "username": username,
        "email": email,
        "password": password  # À sécuriser avec un hachage
    })

    with open(users_file, "w") as f:
        json.dump(users, f, indent=4)

    print("uygfygfrdftrd")

    # Rediriger vers la page de connexion
    return RedirectResponse(url="/index", status_code=302)

@app.get("/index", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/proprietes", response_class=HTMLResponse) 
async def all_properties(request: Request):
    with open(os.path.join(BASE_DIR, "database", "data.json"), "r") as f:
        properties = json.load(f)
    return templates.TemplateResponse("all_properties.html", {"request": request, "properties": properties})

@app.get("/a-vendre", response_class=HTMLResponse)
async def biens_a_vendre(request: Request):
    with open(os.path.join(BASE_DIR, "database", "data.json"), "r") as f:
        all_properties = json.load(f)

    properties = [p for p in all_properties if p.get("statut") == "vente"]

    return templates.TemplateResponse("a_vendre.html", {"request": request, "properties": properties})

@app.get("/a-louer", response_class=HTMLResponse)
async def biens_a_louer(request: Request):
    with open(os.path.join(BASE_DIR, "database", "data.json"), "r") as f:
        all_properties = json.load(f)

    properties = [p for p in all_properties if p.get("statut") == "location"]

    return templates.TemplateResponse("a_louer.html", {"request": request, "properties": properties})


@app.get("/personnalisation-achat", response_class=HTMLResponse)
async def personnalisation_achat_get(request: Request):
    return templates.TemplateResponse("personnalisation_achat.html", {"request": request})

@app.post("/personnalisation-achat", response_class=HTMLResponse)
async def personnalisation_achat_post(
    request: Request,
    type: str = Form(...),
    budget: int = Form(...),
    localisation: str = Form(...),
    surface: int = Form(...),
    pieces: int = Form(...)
):
    # Tu peux ici sauvegarder dans un fichier JSON ou faire des traitements
    data = {
        "type": type,
        "budget": budget,
        "localisation": localisation,
        "surface": surface,
        "pieces": pieces
    }
    # Enregistre dans un fichier temporaire par exemple
    with open(os.path.join(BASE_DIR, "database", "personnalisation_achat.json"), "w") as f:
        json.dump(data, f, indent=4)
    
    return templates.TemplateResponse("personnalisation_achat.html", {
        "request": request,
        "message": "Préférences enregistrées avec succès !"
    })

@app.get("/personnalisation-location", response_class=HTMLResponse)
async def personnalisation_location_get(request: Request):
    return templates.TemplateResponse("personnalisation_location.html", {"request": request})

@app.post("/personnalisation-location", response_class=HTMLResponse)
async def personnalisation_location_post(
    request: Request,
    type: str = Form(...),
    budget: int = Form(...),
    localisation: str = Form(...),
    surface: int = Form(...),
    pieces: int = Form(...)
):
    data = {
        "type": type,
        "budget": budget,
        "localisation": localisation,
        "surface": surface,
        "pieces": pieces
    }

    with open(os.path.join(BASE_DIR, "database", "personnalisation_location.json"), "w") as f:
        json.dump(data, f, indent=4)

    return templates.TemplateResponse("personnalisation_location.html", {
        "request": request,
        "message": "Préférences de location enregistrées avec succès !"
    })

@app.get("/contact", response_class=HTMLResponse)
async def contact_get(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.post("/contact", response_class=HTMLResponse)
async def contact_post(
    request: Request,
    nom: str = Form(...),
    email: str = Form(...),
    message: str = Form(...)
):
    contact_data = {
        "nom": nom,
        "email": email,
        "message": message
    }

    contact_file = os.path.join(BASE_DIR, "database", "messages.json")

    # Si le fichier existe, on récupère les anciens messages
    if os.path.exists(contact_file):
        with open(contact_file, "r") as f:
            messages = json.load(f)
    else:
        messages = []

    messages.append(contact_data)

    with open(contact_file, "w") as f:
        json.dump(messages, f, indent=4)

    return templates.TemplateResponse("contact.html", {
        "request": request,
        "message": "Votre message a été envoyé avec succès !"
    })

@app.get("/profil", response_class=HTMLResponse)
async def profil(request: Request):
    session_file = os.path.join(BASE_DIR, "database", "session.json")

    if os.path.exists(session_file):
        with open(session_file, "r") as f:
            user = json.load(f)
    else:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Veuillez vous connecter pour accéder à votre profil."
        })

    return templates.TemplateResponse("profil.html", {"request": request, "user": user})

@app.get("/logout")
async def logout():
    session_file = os.path.join(BASE_DIR, "database", "session.json")

    if os.path.exists(session_file):
        os.remove(session_file)

    # Redirection vers la page de login avec un message
    return RedirectResponse(url="/login?message=deconnected", status_code=302)

@app.get("/annonces", response_class=HTMLResponse)
async def annonces(request: Request, type: Optional[str] = None, prix_min: int = 0, prix_max: int = 1000000):
    # Charger les données des propriétés
    with open(os.path.join(BASE_DIR, "database", "data.json"), "r") as f:
        properties = json.load(f)

    # Filtrer les propriétés en fonction des critères (type, prix_min, prix_max)
    if type:
        properties = [p for p in properties if p["type"] == type]
    if prix_min:
        properties = [p for p in properties if p["prix"] >= prix_min]
    if prix_max:
        properties = [p for p in properties if p["prix"] <= prix_max]

    return templates.TemplateResponse("annonces.html", {"request": request, "properties": properties})

@app.get("/dossier/{property_id}", response_class=HTMLResponse)
async def dossier(request: Request, property_id: int):
    # Charger les données des dossiers immobiliers
    with open(os.path.join(BASE_DIR, "database", "dossiers.json"), "r") as f:
        dossiers = json.load(f)
    
    # Chercher la propriété correspondant à l'ID
    property = next((p for p in dossiers if p.get("id") == property_id), None)
    
    if not property:
        return templates.TemplateResponse("404.html", {"request": request})
    
    return templates.TemplateResponse("dossier.html", {"request": request, "property": property})

@app.get("/estimation", response_class=HTMLResponse)
async def estimation_form(request: Request):
    return templates.TemplateResponse("estimation.html", {"request": request})

@app.post("/estimation", response_class=HTMLResponse)
async def estimation_result(request: Request,
                            type: str = Form(...),
                            surface: int = Form(...),
                            localisation: str = Form(...),
                            pieces: int = Form(...)):
    # Estimation simplifiée : base + surface * coefficient
    base_price = 1000
    coefficient = 30 if type == "maison" else 25
    localisation_factor = 1.2 if "paris" in localisation.lower() else 1.0

    estimation = int((base_price + surface * coefficient + pieces * 500) * localisation_factor)

    return templates.TemplateResponse("estimation.html", {
        "request": request,
        "estimation": estimation
    })

@app.get("/apropos", response_class=HTMLResponse)
async def apropos(request: Request):
    return templates.TemplateResponse("apropos.html", {"request": request})

@app.get("/investissements", response_class=HTMLResponse)
async def investissements(request: Request):
    return templates.TemplateResponse("investissements.html", {"request": request})

@app.post("/simulation", response_class=HTMLResponse)
async def simulation(request: Request, prix: float = Form(...), loyer: float = Form(...), charges: float = Form(...)):
    loyer_annuel = loyer * 12
    rentabilite_brute = (loyer_annuel / prix) * 100
    rentabilite_nette = ((loyer_annuel - charges) / prix) * 100

        # Sauvegarde dans simulations.json
    simulation_data = {
        "prix": prix,
        "loyer": loyer,
        "charges": charges,
        "brute": round(rentabilite_brute, 2),
        "nette": round(rentabilite_nette, 2)
    }

    simulations_path = os.path.join(BASE_DIR, "database", "simulations.json")
    if os.path.exists(simulations_path):
        with open(simulations_path, "r") as f:
            existing_data = json.load(f)
    else:
        existing_data = []

    existing_data.append(simulation_data)

    with open(simulations_path, "w") as f:
        json.dump(existing_data, f, indent=4)

    return templates.TemplateResponse("resultats_simulation.html", {
        "request": request,
        "prix": prix,
        "loyer": loyer,
        "charges": charges,
        "brute": round(rentabilite_brute, 2),
        "nette": round(rentabilite_nette, 2)
    })

@app.get("/agents", response_class=HTMLResponse)
async def agents(request: Request):
    with open(os.path.join(BASE_DIR, "database", "agents.json"), "r") as f:
        agents_data = json.load(f)
    return templates.TemplateResponse("agents.html", {"request": request, "agents": agents_data})

print("Routes disponibles :", [route.path for route in app.routes]) # type: ignore