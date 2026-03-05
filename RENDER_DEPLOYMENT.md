# 📱 Guide de Déploiement sur Render - Pharmacie Moustapha

## ✅ ÉTAPE 1 : Préparer ton projet local

Assure-toi que tout est commité et pushé sur GitHub :
```bash
git add .
git commit -m "Préparation pour déploiement Render"
git push origin main
```

---

## 📚 ÉTAPE 2 : Créer une Base de Données PostgreSQL sur Render

1. **Accéder à Render** : https://render.com
2. **Se connecter** avec GitHub (ou créer un compte)
3. **Créer une nouvelle base de données** :
   - Cliquer sur **"New +"** → **"PostgreSQL"**
   - **Name** : `pharmacie-moustapha-db` (ou ton choix)
   - **Database** : `pharmacie_db`
   - **User** : `pharmacie_user`
   - **Region** : Selectionne la région la plus proche (ex: Frankfurt pour l'Europe)
   - **Plan** : Free (ou paid si tu veux plus de performance)
   - Cliquer sur **"Create Database"**

4. **Copier la chaîne de connexion** :
   - Une fois la DB créée, tu verras une URL du type :
   ```
   postgresql://pharmacie_user:PASSWORD@hostname:5432/pharmacie_db
   ```
   - **Sauvegarde cette URL** pour l'étape 4 (elle contiendra le mot de passe auto-généré)

---

## 🚀 ÉTAPE 3 : Créer l'Application Web sur Render

1. **Créer un nouveau Web Service** :
   - Cliquer sur **"New +"** → **"Web Service"**
   - **Connect Repository** :
     - Si c'est la première fois, autoriser Render à accéder à GitHub
     - Selectionne le repo `pharmacy_app`
     - Clique **"Connect"**

2. **Configurer le service** :
   - **Name** : `pharmacie-moustapha` (ou `pharmacy-app`)
   - **Environment** : `Python 3`
   - **Region** : Sélectionne la même région que la DB (ex: Frankfurt)
   - **Branch** : `main`
   - **Build Command** : 
     ```
     pip install -r requirements.txt
     ```
   - **Start Command** : 
     ```
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan** : Free (ou Starter pour la production)
   - Cliquer sur **"Create Web Service"**

---

## ⚙️ ÉTAPE 4 : Configurer les Variables d'Environnement

Dans le **Web Service** que tu viens de créer :

1. Aller dans l'onglet **"Environment"**

2. Ajouter les variables suivantes (cliquer sur **"Add Environment Variable"**) :

   ```
   DATABASE_URL = postgresql://pharmacie_user:PASSWORD@hostname:5432/pharmacie_db
   ```
   (Utilise la chaîne copiée à l'étape 2)

   ```
   SECRET_KEY = un_secret_tres_long_et_aleatoire_ici
   ```
   (Génère une clé secrète forte, ex: avec `openssl rand -hex 32`)

   ```
   ALGORITHM = HS256
   ```

   ```
   ACCESS_TOKEN_EXPIRE_MINUTES = 60
   ```

   ```
   PYTHONUNBUFFERED = true
   ```

3. Cliquer sur **"Save"**

---

## 🔄 ÉTAPE 5 : Initialiser la Base de Données

Une fois le déploiement terminé :

1. **Attendre le déploiement** (~2-5 minutes)
2. **Ouvrir le terminal Render** (dans le Web Service) ou utiliser une commande de shell
3. Les tables seront créées automatiquement via `Base.metadata.create_all()` au démarrage

---

## 🔗 ÉTAPE 6 : Accéder à l'Application

Une fois déployée, ton app sera accessible à :
```
https://pharmacie-moustapha.onrender.com
```
(Remplace le nom par celui que tu as donné à ton service)

---

## 🐛 Dépannage

### Erreur : "ModuleNotFoundError"
→ Vérifier que `requirements.txt` est à jour :
```bash
pip freeze > requirements.txt
```

### Erreur : "Database connection failed"
→ Vérifier la `DATABASE_URL` est exacte dans les variables d'environnement

### Erreur : "Port already in use"
→ C'est normal avec les ports fixes, Render gère cela automatiquement avec `$PORT`

### Application lente au démarrage
→ C'est normal sur le plan Free de Render (il y a un délai de démarrage)

### Voir les logs
→ Dans le Web Service, aller dans **"Logs"** pour debuguer les erreurs

---

## 📦 Fichiers Créés pour le Déploiement

✅ **render.yaml** - Configuration de déploiement automatique (optionnel)
✅ **build.sh** - Script de build personnalisé (optionnel)

---

## 🔐 Sécurité

⚠️ **IMPORTANT** :
- ❌ Ne jamais push ton `.env` local sur GitHub
- ✅ Générer une `SECRET_KEY` forte pour Render (différente de celle locale)
- ✅ Utiliser `DATABASE_URL` auto-générée par Render
- ✅ Activer HTTPS (automatique sur Render)

---

## 📝 Étapes Rapides Résumées

```
1. GitHub → Commit & Push
2. Render → Créer PostgreSQL DB + copier URL
3. Render → Créer Web Service (Git connected)
4. Render → Ajouter Environment Variables (DATABASE_URL, SECRET_KEY, etc.)
5. Attendre le déploiement
6. Accéder à https://pharmacie-moustapha.onrender.com
```

---

## 🆘 Besoin d'Aide ?

Si quelque chose ne marche pas :
1. **Vérifier les logs** dans le Web Service
2. **Tester localement** avec les mêmes variables d'env
3. **Me montrer l'erreur** exacte des logs Render

Bon déploiement ! 🚀
