# Déploiement sur Railway

## Prérequis
- Compte GitHub avec ton repo poussé
- Compte [Railway.app](https://railway.app)
- CLI Railway (optionnel, mais recommandé)

## Étape 1 : Préparer ton repo (✅ DÉJÀ FAIT)

### Vérifications complétées
- ✅ `.env` retiré du Git (`git rm --cached .env`)
- ✅ `.gitignore` créé avec `.env` et `venv/`
- ✅ `.env.example` créé avec des valeurs fictives
- ✅ `docker-entrypoint.sh` créé pour exécuter Alembic au démarrage
- ✅ `Dockerfile` mis à jour pour utiliser l'entrypoint
- ✅ `alembic.ini` et `alembic/env.py` configurés pour lire `DATABASE_URL` depuis l'environnement

### Pousser les changements
```bash
git add .
git commit -m "Deployment ready: .env secured, Docker optimized, Alembic configured"
git push origin yaya  # remplace 'yaya' par ta branche principale (main/master)
```

---

## Étape 2 : Créer un projet Railway

1. **Aller sur [railway.app](https://railway.app)** et se connecter avec GitHub
2. **Cliquer sur "New Project"**
3. **Sélectionner "Deploy from GitHub repo"**
4. **Authoriser Railway à accéder à tes repos**
5. **Sélectionner le repo `pharmacy-system`** (ou le nom de ton repo)
6. **Railway détectera automatiquement le Dockerfile** et créera le service

---

## Étape 3 : Ajouter PostgreSQL

Dans le dashboard Railway du projet :

1. **Cliquer sur "+ New"** (en haut)
2. **Sélectionner "Database"** → **"PostgreSQL"**
3. Railway génère automatiquement `DATABASE_URL`
4. **Copier `DATABASE_URL` depuis les variables d'environnement** (tu vas en avoir besoin)

---

## Étape 4 : Configurer les variables d'environnement

Dans le dashboard Railway, aller dans **"Variables"** du service Web :

### Variables requises à ajouter

```
DATABASE_URL=postgresql://user:pass@host:5432/db
SECRET_KEY=<nouvelle_clé_générée_ci-dessous>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
BASE_URL=https://<nom-du-service>.railway.app
SMTP_USER=yayatraore115@gmail.com
SMTP_PASSWORD=<ton_app_password_Gmail>
DEBUG=False
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

### Générer une nouvelle SECRET_KEY

Sur ta machine locale, exécute :
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copie la valeur et colle-la dans Railway comme `SECRET_KEY`.

### Récupérer ton `BASE_URL` Railway

Après le premier déploiement, Railway t'attribuera une URL comme :
```
https://pharmacy-app-production.railway.app
```

Configure `BASE_URL` avec cette valeur exacte.

### Récupérer un app password Gmail

Si tu utilises Gmail pour SMTP :

1. **Aller sur [myaccount.google.com](https://myaccount.google.com)**
2. **Naviguer vers "Security"** (à gauche)
3. **Activer "2-Step Verification"** si ce n'est pas fait
4. **Retourner à "Security"** et chercher **"App passwords"**
5. Générer un mot de passe pour "Mail" + "Windows"
6. Copier et coller ce mot de passe dans Railway comme `SMTP_PASSWORD`

---

## Étape 5 : Déployer

Railway redéploiera automatiquement à chaque push vers la branche :

```bash
git push origin yaya
```

**Lors du premier déploiement** :
1. Railway télécharge l'image Docker
2. Lance le conteneur
3. **`docker-entrypoint.sh` exécute `alembic upgrade head`** — crée les tables
4. **`uvicorn` démarre** et l'app est live

---

## Étape 6 : Vérifier les logs

Dans le dashboard Railway :
- **Cliquer sur le service Web**
- **Aller dans "Deployments"**
- **Voir les logs** en live pour déboguer les erreurs

Exemple de logs réussis :
```
Starting container entrypoint
alembic.ini found — running migrations: alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl
INFO  [alembic.runtime.migration] Will assume transactional DDL is supported
...
INFO:     Started server process [1]
INFO:     Uvicorn running on http://0.0.0.0:10000
```

---

## Étape 7 : (Optionnel) Configurer un domaine personnalisé

1. **Dans Railway → "Settings" du projet**
2. **Ajouter un domaine personnalisé** (ex: `pharmacie.example.com`)
3. **Ajouter les DNS records** fournis par Railway à ton registrar
4. Mettre à jour `BASE_URL` dans les variables d'environnement

---

## Dépannage courant

### ❌ "alembic upgrade head" échoue
- Vérifie que `DATABASE_URL` est correctement configurée dans Railway
- Vérifie que PostgreSQL a démarré (attendre ~30 secondes)
- Consulter les logs dans Railway

### ❌ Erreur SMTP dans les emails
- Vérifier `SMTP_USER` et `SMTP_PASSWORD`
- Si Gmail, générer une [app password](https://support.google.com/accounts/answer/185833) au lieu du mot de passe principal
- Vérifier que `BASE_URL` ne contient pas de typo

### ❌ "Remote database is not accessible"
- Attendre que PostgreSQL soit complètement démarré (~1-2 min)
- Redéployer le service Web après que PostgreSQL soit prêt

---

## Commandes utiles (CLI Railway)

Si tu as installé [Railway CLI](https://docs.railway.app/cli/install) :

```bash
# Se connecter à ton compte Railway
railway login

# Lier le projet local
railway link

# Voir les logs en direct
railway logs

# Configurer les variables d'environnement
railway env push

# Déployer manuellement
railway deploy
```

---

## URLs utiles

- 📊 Dashboard Railway: https://railway.app/dashboard
- 📖 Docs Deployment: https://docs.railway.app/deploy/dockerfiles
- 🗂️ Ton repo: https://github.com/yayaTraore1/pharmacy-system

---

**Besoin d'aide ? Je peux te guider pas à pas pour chaque étape.**
