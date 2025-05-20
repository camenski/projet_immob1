from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import json
import smtplib
import random
import os
from email.mime.text import MIMEText
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
import secrets
import bcrypt
import traceback
from fastapi import Form 
from fastapi.responses import RedirectResponse
from typing import Optional
from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print("Chemin du projet :", BASE_DIR)
print("Dossiers :", os.listdir(BASE_DIR))  # 🔹 Affiche tous les fichiers/dossiers
print("Dossiers dans /templates :", os.listdir(os.path.join(BASE_DIR, "templates")))
templates = Jinja2Templates(directory="templates")  # 🔹 Vérifie que c'est bien "templates"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(directory="templates")


# Sauvegarde dans simulations.json
simulations_path = os.path.join(BASE_DIR, "database", "simulations.json")

if os.path.exists(simulations_path):
    with open(simulations_path, "r") as f:
        existing_data = json.load(f)
else:
    existing_data = []

# Ajout de la nouvelle simulation
simulation_data = {}  # Define simulation_data with appropriate structure
existing_data.append(simulation_data)

# Écriture du fichier JSON
with open(simulations_path, "w") as f:
    json.dump(existing_data, f, indent=4)



load_dotenv()  # Charge les variables de l'environnement
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")


# 🔹 Fonction pour envoyer un code de vérification par email
def send_verification_code(email: str):
    verification_code = str(random.randint(1000, 9999))  # Génère un code à 4 chiffres

    print("EMAIL_SENDER :", EMAIL_SENDER)
    print("EMAIL_PASSWORD :", EMAIL_PASSWORD)


    msg = MIMEText(f"Votre code de vérification est : {verification_code}")
    msg["Subject"] = "Réinitialisation de mot de passe"
    if not EMAIL_SENDER:
        raise ValueError("EMAIL_SENDER is not set in the environment variables.")
    msg["From"] = EMAIL_SENDER
    msg["To"] = email

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Sécurisation de la connexion
            if EMAIL_PASSWORD is None:
                raise ValueError("EMAIL_PASSWORD is not set in the environment variables.")
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, email, msg.as_string())
        
        print("Code envoyé avec succès :", verification_code)
        return verification_code  # Retourne le code pour la vérification
    except Exception as e:
        print("Erreur lors de l'envoi de l'email :", e)
        return None

def is_valid_email(email: str) -> bool:
    regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(regex, email) is not None



app = FastAPI()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "database", "data.json")

# Chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    return templates.TemplateResponse("principal.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def show_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)  # 🔹 Assure-toi qu'il est bien présent ici
):

    users_file = os.path.join(BASE_DIR, "database", "users.json")

    try:
        # 🔹 Vérifier que l’email est valide (Ajoute cette ligne ici)
        if not is_valid_email(email):
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Adresse email invalide."
            })

        # 🔹 Vérifier que les mots de passe correspondent
        if password != confirm_password:
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Les mots de passe ne correspondent pas."
            })

        # 🔹 Charger les utilisateurs existants
        if os.path.exists(users_file):
            with open(users_file, "r") as f:
                users = json.load(f)
        else:
            users = []

        # 🔹 Vérifier si l'email ou le username existe déjà
        if any(u["email"] == email or u["username"] == username for u in users):
            return templates.TemplateResponse("register.html", {
                "request": request,
                "error": "Nom d'utilisateur ou email déjà utilisé."
            })

        # 🔹 Hacher le mot de passe
        hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

        # 🔹 Ajouter le nouvel utilisateur
        users.append({
            "username": username,
            "email": email,
            "password": hashed_password
        })

        # 🔹 Enregistrer dans `users.json`
        with open(users_file, "w") as f:
            json.dump(users, f, indent=4)

        # 🔹 Rediriger vers la page de connexion
        return RedirectResponse(url="/login?message=success", status_code=303)

    except Exception as e:
        return {"error": f"Une erreur interne s'est produite : {e}"}


@app.get("/login", response_class=HTMLResponse)
async def show_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# 🔹 Route POST pour traiter la connexion
@app.post("/login")
async def login(request: Request, email: str = Form(...), password: str = Form(...)):
    users_file = os.path.join(BASE_DIR, "database", "users.json")

    try:
        # 🔸 Chargement sécurisé des utilisateurs
        if os.path.exists(users_file):
            with open(users_file, "r") as f:
                users = json.load(f)
        else:
            users = []
        
        # 🔹 Vérifier si l'utilisateur existe
        user = next((u for u in users if u.get("email") == email), None)

        if user is None:
            print("Utilisateur non trouvé :", email)
            return RedirectResponse(url="/login?message=error", status_code=302)

        # 🔹 Vérifier le format du mot de passe
        print("Mot de passe stocké :", user["password"])
        print("Type du mot de passe :", type(user["password"]))

        # 🔹 Assurer que le mot de passe est bien haché
        if not bcrypt.checkpw(password.encode(), user["password"].encode()):
            print("Mot de passe incorrect :", password)
            return RedirectResponse(url="/login?message=error", status_code=302)

        # 🔹 Sauvegarde de session avec cookie
        response = RedirectResponse(url="/index", status_code=302)
        response.set_cookie(key="user", value=email)  # Stocke la session utilisateur
        print("Connexion réussie pour :", email)
        return response

    except Exception as e:
        print("Erreur détectée :", e)
        print(traceback.format_exc())  # Affiche l'erreur complète dans le terminal
        return {"error": f"Une erreur interne s'est produite : {e}"}
    

@app.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@app.post("/reset-password")
async def reset_password(request: Request, email: str = Form(...)):
    users_file = os.path.join(BASE_DIR, "database", "users.json")

    # 🔹 Charger les utilisateurs existants
    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            users = json.load(f)
    else:
        users = []

    user = next((u for u in users if u.get("email") == email), None)

    if user is None:
        return templates.TemplateResponse("forgot_password.html", {
            "request": request,
            "error": "Adresse email introuvable."
        })

    # 🔹 Générer un token unique (dans une vraie app, on enverrait un email)
    reset_token = secrets.token_urlsafe(32)

    # 🔹 Sauvegarde du token pour vérifier plus tard
    reset_file = os.path.join(BASE_DIR, "database", "reset_tokens.json")
    with open(reset_file, "w") as f:
        json.dump({email: reset_token}, f)

    # 🔹 Simuler un email en affichant le lien
    reset_link = f"http://127.0.0.1:8000/new-password?token={reset_token}&email={email}"

    return templates.TemplateResponse("forgot_password.html", {
        "request": request,
        "message": f"Lien de réinitialisation généré : {reset_link}"
    })

# 🔹 Route POST : Envoyer le code par email
@app.post("/send-code")
async def send_code(request: Request, email: str = Form(...)):
    users_file = os.path.join(BASE_DIR, "database", "users.json")

    # 🔹 Vérifier si l'utilisateur existe
    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            users = json.load(f)
    else:
        users = []

    user = next((u for u in users if u.get("email") == email), None)

    if user is None:
        return templates.TemplateResponse("forgot_password.html", {
            "request": request,
            "error": "Adresse email introuvable."
        })

    # 🔹 Envoyer le code par email
    verification_code = send_verification_code(email)

    if not verification_code:
        return templates.TemplateResponse("forgot_password.html", {
            "request": request,
            "error": "Échec d'envoi du code, réessayez plus tard."
        })

    return templates.TemplateResponse("verify_code.html", {"request": request, "email": email})

# 🔹 Route POST : Vérifier le code entré par l’utilisateur
@app.post("/verify-code")
async def verify_code(request: Request, email: str = Form(...), code: str = Form(...)):
    codes_file = os.path.join(BASE_DIR, "database", "verification_codes.json")

    # 🔹 Charger le fichier des codes
    if os.path.exists(codes_file):
        with open(codes_file, "r") as f:
            codes = json.load(f)
    else:
        codes = {}

    if codes.get(email) != code:
        return templates.TemplateResponse("verify_code.html", {
            "request": request,
            "email": email,
            "error": "Code incorrect. Réessayez."
        })

    # 🔹 Rediriger vers la page pour réinitialiser le mot de passe
    return templates.TemplateResponse("new_password.html", {"request": request, "email": email})

# 🔹 Route POST : Réinitialiser le mot de passe après confirmation
@app.post("/new-password")
async def update_password(request: Request, email: str = Form(...), new_password: str = Form(...)):
    users_file = os.path.join(BASE_DIR, "database", "users.json")

    # 🔹 Charger les utilisateurs
    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            users = json.load(f)
    else:
        users = []

    user = next((u for u in users if u.get("email") == email), None)

    if user is None:
        return {"error": "Utilisateur introuvable."}

    # 🔹 Hacher le nouveau mot de passe
    import bcrypt
    user["password"] = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

    # 🔹 Sauvegarder le nouveau mot de passe
    with open(users_file, "w") as f:
        json.dump(users, f, indent=4)

    return RedirectResponse(url="/login?message=password_updated", status_code=303)


@app.get("/index", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/proprietes", response_class=HTMLResponse)
async def all_properties(request: Request):
    try:
        with open(os.path.join(BASE_DIR, "database", "data.json"), "r") as f:
            properties = json.load(f)
        return templates.TemplateResponse("all_properties.html", {"request": request, "properties": properties})
    except Exception as e:
        return {"error": f"Une erreur est survenue : {e}"}
    
@app.get("/acheter/{property_id}", response_class=HTMLResponse)
async def acheter_propriete_details(request: Request, property_id: int):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        all_properties = json.load(f)

     # Trouver la propriété sélectionnée
    property_info = next((p for p in all_properties if p["id"] == property_id), None)

    if not property_info:
        return templates.TemplateResponse("erreur.html", {"request": request, "message": "Propriété introuvable."})

    return templates.TemplateResponse("achat.html", {"request": request, "property": property_info})

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


@app.get("/dossier/{property_id}", response_class=HTMLResponse)
async def dossier(request: Request, property_id: int):
    with open(os.path.join(BASE_DIR, "database", "dossiers.json"), "r") as f:
        dossiers = json.load(f)

    property = next((p for p in dossiers if p.get("id") == property_id), None)

    if not property:
        return templates.TemplateResponse("404.html", {"request": request})

    return templates.TemplateResponse("dossier.html", {"request": request, "property": property})


@app.get("/profil", response_class=HTMLResponse)
async def profil(request: Request):
    user_email = request.cookies.get("user")  # 🔹 Lire l'email stocké dans le cookie

    if not user_email:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Veuillez vous connecter."})

    users_file = os.path.join(BASE_DIR, "database", "users.json")

    if os.path.exists(users_file):
        with open(users_file, "r", encoding="utf-8") as f:
            users = json.load(f)
        
        user = next((u for u in users if u.get("email") == user_email), None)

        if not user:
            return templates.TemplateResponse("login.html", {"request": request, "error": "Compte introuvable."})

    else:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Erreur de session."})

    return templates.TemplateResponse("profil.html", {"request": request, "user": user})


@app.get("/annonces", response_class=HTMLResponse)
async def annonces(request: Request):
    annonces_file = os.path.join(BASE_DIR, "database", "data.json")

    if os.path.exists(annonces_file):
        with open(annonces_file, "r") as f:
            all_properties = json.load(f)
    else:
        all_properties = []

    # Filtrer uniquement les annonces validées
    properties = [p for p in all_properties if p["statut"] == "publié"]

    return templates.TemplateResponse("annonces.html", {"request": request, "properties": properties})

@app.post("/confirmer-annonce/{property_id}")
async def confirmer_publication(property_id: int):  # Nouveau nom pour éviter le conflit
    annonces_file = os.path.join(BASE_DIR, "database", "data.json")

    if os.path.exists(annonces_file):
        with open(annonces_file, "r") as f:
            properties = json.load(f)
    else:
        return {"error": "Aucune annonce trouvée"}

    # Modifier le statut de l'annonce ciblée
    for annonce in properties:
        if annonce["id"] == property_id:
            annonce["statut"] = "publié"
            break

    # Sauvegarder les modifications
    with open(annonces_file, "w") as f:
        json.dump(properties, f, indent=4)

    return RedirectResponse(url="/annonces", status_code=303)

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    annonces_file = os.path.join(BASE_DIR, "database", "data.json")

    if os.path.exists(annonces_file):
        with open(annonces_file, "r") as f:
            all_properties = json.load(f)
    else:
        all_properties = []

    # Sélectionner uniquement les annonces en attente
    pending_annonces = [p for p in all_properties if p["statut"] == "en attente"]

    return templates.TemplateResponse("admin.html", {"request": request, "annonces": pending_annonces})


@app.post("/confirmer-annonce/{property_id}")
async def confirmer_annonce(property_id: int):
    annonces_file = os.path.join(BASE_DIR, "database", "data.json")

    if os.path.exists(annonces_file):
        with open(annonces_file, "r") as f:
            properties = json.load(f)
    else:
        return {"error": "Aucune annonce trouvée"}

    # Modifier le statut de l'annonce ciblée
    for annonce in properties:
        if annonce["id"] == property_id:
            annonce["statut"] = "publié"
            break

    # Sauvegarder les modifications
    with open(annonces_file, "w") as f:
        json.dump(properties, f, indent=4)

    return RedirectResponse(url="/admin", status_code=303)



@app.post("/verifier_fraude")
async def verifier_fraude(property_id: int):
    with open("database/dossiers.json", "r") as f:
        dossiers = json.load(f)

    # Vérifie si la propriété a été vendue plusieurs fois en peu de temps
    property_data = next((p for p in dossiers if p["id"] == property_id), None)

    if not property_data:
        return {"erreur": "Propriété introuvable"}

    historique = property_data.get("historique", [])

    if len(historique) > 1:  # Si plusieurs transactions existent
        return {"alerte": "Vérifier les transactions, vente multiple détectée !", "historique": historique}
    
    return {"message": "Aucune fraude détectée"}

@app.get("/historique/{property_id}")
async def get_historique(property_id: int):
    historique_file = os.path.join(BASE_DIR, "database", "historique.json")

    if os.path.exists(historique_file):
        with open(historique_file, "r") as f:
            historiques = json.load(f)
    else:
        return {"error": "Fichier historique introuvable"}

    property_historique = next((h for h in historiques if h["property_id"] == property_id), None)

    if not property_historique:
        return {"error": "Aucun historique trouvé pour cette propriété"}

    return property_historique

@app.post("/publier-annonce", response_class=HTMLResponse)
async def publier_annonce(
    request: Request,
    titre: str = Form(...),
    prix: int = Form(...),
    localisation: str = Form(...),
    description: str = Form(...),
    image: str = Form(...)
):
    annonces_file = os.path.join(BASE_DIR, "database", "data.json")

    # Charger les annonces existantes
    if os.path.exists(annonces_file):
        with open(annonces_file, "r") as f:
            properties = json.load(f)
    else:
        properties = []

    # Ajouter une nouvelle annonce avec un statut "en attente"
    nouvelle_annonce = {
        "id": len(properties) + 1,
        "titre": titre,
        "prix": prix,
        "localisation": localisation,
        "description": description,
        "image": image,
        "statut": "en attente"
    }

    properties.append(nouvelle_annonce)

    # Enregistrer dans le fichier `data.json`
    with open(annonces_file, "w") as f:
        json.dump(properties, f, indent=4)

    # Rediriger vers une page de confirmation
    return RedirectResponse(url="/annonces", status_code=303)

@app.get("/recherche-achat", response_class=HTMLResponse)
async def show_recherche_achat(request: Request):
    return templates.TemplateResponse("recherche_achat.html", {"request": request})

@app.get("/api/recherche-achat")
async def rechercher_proprietes(
    request: Request,
    type: str = Query(None, description="Type de bien"),
    budget: int = Query(0, description="Budget maximum"),
    localisation: str = Query(None, description="Localisation"),
    surface: int = Query(0, description="Surface minimum"),
    pieces: int = Query(0, description="Nombre de pièces minimum")
):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        all_properties = json.load(f)

    matching_properties = [
        p for p in all_properties
        if p.get("statut") == "vente"
        and p.get("price") <= budget
        and p.get("surface") >= surface
        and p.get("pieces") >= pieces
        and (type is None or p.get("type") == type)
        and (localisation is None or localisation.lower() in p.get("location").lower())
    ]

    return JSONResponse(content={"resultats": matching_properties})

@app.get("/acheter/{property_id}", response_class=HTMLResponse)
async def acheter_propriete(request: Request, property_id: int):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        all_properties = json.load(f)

    # Trouver la propriété sélectionnée
    property_info = next((p for p in all_properties if p["id"] == property_id), None)

    if not property_info:
        return templates.TemplateResponse("erreur.html", {"request": request, "message": "Propriété introuvable."})

    return templates.TemplateResponse("achat.html", {"request": request, "property": property_info})

@app.post("/finaliser-achat/{property_id}")
async def finaliser_achat(request: Request, property_id: int):
    form_data = await request.form()

    # Enregistrer l'achat
    achat_info = {
        "property_id": property_id,
        "nom": form_data.get("nom"),
        "email": form_data.get("email"),
        "telephone": form_data.get("telephone")
    }

    achat_file = os.path.join(BASE_DIR, "database", "achats.json")

    if os.path.exists(achat_file):
        with open(achat_file, "r", encoding="utf-8") as f:
            achats = json.load(f)
    else:
        achats = []

    achats.append(achat_info)

    with open(achat_file, "w", encoding="utf-8") as f:
        json.dump(achats, f)

    return templates.TemplateResponse("confirmation_achat.html", {"request": request, "property_id": property_id})

app.mount("/static", StaticFiles(directory="static"), name="static")

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
async def profil_session(request: Request):
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

@app.get("/annonces-filtrees", response_class=HTMLResponse)
async def annonces_filtrees(request: Request, type: Optional[str] = None, prix_min: int = 0, prix_max: int = 1000000):
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
async def dossier_details(request: Request, property_id: int):
    # Charger les données des dossiers immobiliers
    with open(os.path.join(BASE_DIR, "database", "dossiers.json"), "r") as f:
        dossiers = json.load(f)
    
    # Chercher la propriété correspondant à l'ID
    property = next((p for p in dossiers if p.get("id") == property_id), None)
    
    if not property:
        return templates.TemplateResponse("404.html", {"request": request})
    
    return templates.TemplateResponse("dossier.html", {"request": request, "property": property})

@app.get("/estimation", response_class=HTMLResponse)
async def estimation(request: Request):
    return templates.TemplateResponse("estimation.html", {"request": request})


@app.post("/estimation", response_class=HTMLResponse)
async def estimation_result(request: Request,
                            type: str = Form(...),
                            surface: int = Form(...),
                            localisation: str = Form(...),
                            pieces: int = Form(...)):
    
    # 🔹 Prix moyen du terrain par localisation en Côte d'Ivoire
    prix_terrain = {
        "plateau": 1000000,
        "marcory": 892000,
        "cocody": 241569,
        "bingerville": 62358,
        "assinie": 90445,
        "yamoussoukro": 45537
    }

    # 🔹 Prix moyen de construction par m² (maison ou appartement)
    prix_construction_m2 = {
        "maison": 350000,   # Prix moyen de construction d'une maison par m²
        "appartement": 400000  # Prix moyen au m² pour un appartement
    }

    # 📌 Détermination du prix du bien immobilier
    localisation_factor = prix_terrain.get(localisation.lower(), 45000)  # Valeur par défaut si localisation inconnue
    prix_construction = prix_construction_m2.get(type.lower(), 250000)   # Valeur par défaut si type inconnu

    if type.lower() == "terrain":
        # 🏞 Estimation uniquement du prix du terrain
        estimation = localisation_factor * surface
    else:
        # 🏡 Estimation du coût total (terrain + construction)
        prix_terrain_total = localisation_factor * (surface * 0.5)  # Supposons que le terrain est 50% plus grand que la maison
        prix_construction_total = prix_construction * surface
        estimation = prix_terrain_total + prix_construction_total

    # 📌 Calcul de l'impôt foncier (0.5% de la base imposable)
    base_imposable = estimation * 0.5
    impot_foncier = base_imposable * 0.005

    return templates.TemplateResponse("estimation.html", {
        "request": request,
        "estimation": "{:,.0f}".format(estimation) + " FCFA",
        "impot_foncier": "{:,.0f}".format(impot_foncier) + " FCFA"
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

@app.post("/api/simulation")
async def calculer_rentabilite(request: Request,
    prix: float = Form(...),
    loyer: float = Form(...),
    charges: float = Form(...),
    surface: float = Form(...)
):
    print(f"Reçu: prix={prix}, loyer={loyer}, charges={charges}, surface={surface}")  # 🔍 Ajoute ceci


@app.get("/agents", response_class=HTMLResponse)
async def agents(request: Request):
    with open(os.path.join(BASE_DIR, "database", "agents.json"), "r") as f:
        agents_data = json.load(f)
    return templates.TemplateResponse("agents.html", {"request": request, "agents": agents_data})
@app.get("/", response_class=HTMLResponse)
async def accueil_page(request: Request):
    return templates.TemplateResponse("accueil.html", {"request": request})


@app.post("/favoris/{property_id}")
async def add_favorite(request: Request, property_id: int):
    session_file = os.path.join(BASE_DIR, "database", "session.json")
    favorites_file = os.path.join(BASE_DIR, "database", "favorites.json")

    # Vérifier si l'utilisateur est connecté
    if not os.path.exists(session_file):
        return {"error": "Veuillez vous connecter pour ajouter des favoris."}

    with open(session_file, "r") as f:
        user = json.load(f)

    user_email = user.get("email")  # Identifiant unique

    # Charger les favoris existants
    if os.path.exists(favorites_file):
        with open(favorites_file, "r") as f:
            all_favorites = json.load(f)
    else:
        all_favorites = {}

    # Ajouter la propriété aux favoris de l'utilisateur
    user_favorites = all_favorites.get(user_email, [])
    if property_id not in user_favorites:
        user_favorites.append(property_id)

    # Sauvegarder les favoris mis à jour
    all_favorites[user_email] = user_favorites
    with open(favorites_file, "w") as f:
        json.dump(all_favorites, f)

    return {"message": f"Propriété {property_id} ajoutée aux favoris !"}

@app.get("/mes-favoris", response_class=HTMLResponse)
async def show_favorites(request: Request):
    session_file = os.path.join(BASE_DIR, "database", "session.json")
    favorites_file = os.path.join(BASE_DIR, "database", "favorites.json")
    properties_file = os.path.join(BASE_DIR, "database", "data.json")

    # Vérifier si l'utilisateur est connecté
    if not os.path.exists(session_file):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Veuillez vous connecter."})

    with open(session_file, "r") as f:
        user = json.load(f)

    user_email = user.get("email")

    # Charger les favoris existants
    if os.path.exists(favorites_file):
        with open(favorites_file, "r") as f:
            all_favorites = json.load(f)
    else:
        all_favorites = {}

    user_favorites = all_favorites.get(user_email, [])

    # Charger les propriétés complètes depuis `data.json`
    with open(properties_file, "r") as f:
        all_properties = json.load(f)

    favorite_properties = [p for p in all_properties if p.get("id") in user_favorites]

    return templates.TemplateResponse("favorites.html", {"request": request, "favorites": favorite_properties})
# Cette route récupère les favoris de l'utilisateur et affiche les propriétés
