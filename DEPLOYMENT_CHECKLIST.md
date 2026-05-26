# 🚀 Checklist de Déploiement Railway

**PRÊT POUR LE DÉPLOIEMENT : ✅ OUI**

Tous les fichiers et configurations nécessaires ont été préparés. Voici ce qui a été fait :

---

## ✅ Étapes complétées (LOCAL)

- ✅ **Sécurité `.env`** — `.env` retiré de Git, `.env.example` créé
- ✅ **SECRET_KEY et SMTP_PASSWORD** — Nouvelles valeurs générées
- ✅ **Git History Purged** — Suppression des anciennes traces `.env` via `git filter-repo`
- ✅ **Mailer amélioré** — Try/except ajoutés, BASE_URL depuis env
- ✅ **Docker optimisé** — Entrypoint pour Alembic + uvicorn
- ✅ **Alembic configuré** — env.py lit DATABASE_URL depuis l'env
- ✅ **Railway config** — `railway.json` et `Procfile` créés
- ✅ **Guide complet** — `RAILWAY_DEPLOYMENT.md`

---

## ⏭️  Étapes à faire MAINTENANT (GITHUB + RAILWAY)

### 1️⃣ Pousser ton code à GitHub

```bash
git push origin yaya
```

> Remplace `yaya` par ta branche principale (main/master) si c'est différent.

### 2️⃣ Créer un compte Railway (si pas déjà fait)

- Aller sur https://railway.app
- Connecter avec GitHub
- Cliquer "New Project" → "Deploy from GitHub repo"
- Sélectionner ton repo `pharmacy-system`

### 3️⃣ Ajouter PostgreSQL à Railway

- Dashboard Railway → "+ New" → "Database" → "PostgreSQL"
- Railway génère une `DATABASE_URL` automatiquement

### 4️⃣ Configurer les variables d'environnement sur Railway

Dans le service Web du projet Railway, ajouter :

```
DATABASE_URL=postgresql://...  (généré par Railway PostgreSQL)
SECRET_KEY=<copier depuis: python generate_secrets.py>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
BASE_URL=https://<ton-app>.railway.app  (copier après 1er déploiement)
SMTP_USER=yayatraore115@gmail.com
SMTP_PASSWORD=<app_password_Gmail>
DEBUG=False
```

### 5️⃣ Générer une nouvelle SECRET_KEY (local)

```bash
python generate_secrets.py
```

### 6️⃣ Attendre et vérifier les logs

Railway va automatiquement :
1. ✅ Télécharger ton code
2. ✅ Builder le Dockerfile
3. ✅ Lancer le conteneur
4. ✅ Exécuter `docker-entrypoint.sh` → alembic upgrade head
5. ✅ Démarrer uvicorn

Vérifie les logs dans le dashboard Railway pour voir :
```
Starting container entrypoint
alembic.ini found — running migrations: alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl
...
INFO:     Started server process [1]
INFO:     Uvicorn running on http://0.0.0.0:10000
```

---

## 📋 Fichiers de déploiement créés

| Fichier | Utilité |
|---------|---------|
| `railway.json` | Configuration Railway |
| `Procfile` | Commande de démarrage |
| `docker-entrypoint.sh` | Exécute Alembic puis uvicorn |
| `Dockerfile` | Image Docker optimisée |
| `alembic.ini` + `alembic/env.py` | Migrations DB |
| `generate_secrets.py` | Générer SECRET_KEY sécurisée |
| `RAILWAY_DEPLOYMENT.md` | Guide complet (ce que tu lis) |

---

## 🆘 Dépannage rapide

| Problème | Solution |
|----------|----------|
| `alembic upgrade head` échoue | Attendre que PostgreSQL démarre (~30s), vérifier DATABASE_URL |
| Pas de domaine personnalisé | Railway génère une URL gratuite automatiquement |
| SMTP ne marche pas | Utiliser une [app password Gmail](https://support.google.com/accounts/answer/185833), pas le mot de passe principal |
| Logs invisibles | Railway → Deployments → voir les logs en live |

---

## 🔗 Liens utiles

- 📊 Dashboard Railway: https://railway.app/dashboard
- 📖 Docs Railway: https://docs.railway.app
- 🐘 PostgreSQL: Railway ajoute automatiquement
- 🔐 Gmail App Password: https://support.google.com/accounts/answer/185833

---

## 💡 Prochaines étapes (après déploiement)

1. **Tester l'app** → https://ton-app.railway.app
2. **Créer un compte admin** → Utiliser les routes `/auth`
3. **Vérifier les emails** → Tester création de compte
4. **Ajouter un domaine personnalisé** (optionnel)
5. **Configurer les backups PostgreSQL** (optionnel)

---

**Tu as besoin de mon aide pour une étape ? Dis-moi laquelle et je guide pas à pas.**
