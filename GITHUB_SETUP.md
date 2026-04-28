# 📌 Instructions pour déployer ProjectFlow sur GitHub

## 🔧 Prérequis
- ✅ Git installé sur votre ordinateur (https://git-scm.com/)
- ✅ Compte GitHub créé (https://github.com)
- ✅ Accès à la ligne de commande (Command Prompt, PowerShell, Git Bash)

## 📍 Étape 1 : Créer un nouveau repository sur GitHub

1. Allez sur https://github.com/new
2. Entrez le nom du repository : **projectflow**
3. Description : "Gestion de Projets Étudiants avec Scrum"
4. Cochez **Public** (pour GitHub Pages)
5. ✅ Cliquez sur **Create repository**

## 🖥️ Étape 2 : Initialiser Git localement

Ouvrez Command Prompt ou PowerShell et exécutez ces commandes :

```bash
# Naviguez vers le dossier du projet
cd "c:\Users\mouha_edbx2zz\OneDrive\Desktop\GLSI2\S2\PFA"

# Initialisez Git
git init

# Ajoutez votre identité
git config user.name "Votre Nom"
git config user.email "votre-email@github.com"

# Ajoutez tous les fichiers
git add .

# Créez un commit initial
git commit -m "Initial commit: ProjectFlow v1.0"

# Ajoutez le remote GitHub (remplacez USERNAME par votre pseudo GitHub)
git remote add origin https://github.com/USERNAME/projectflow.git

# Poussez vers GitHub
git push -u origin main
```

## 📝 Notes importantes

### Si la branche par défaut est "master" au lieu de "main"
```bash
git branch -M main
git push -u origin main
```

### Si vous avez des problèmes d'authentification
- **Avec Git Bash/Command Prompt** : Un navigateur s'ouvrira pour l'authentification
- **Alternative avec token** : Générez un Personal Access Token sur GitHub (Settings → Developer settings → Personal access tokens)

## 🌐 Étape 3 : Activer GitHub Pages (optionnel)

Pour rendre votre app accessible en ligne :

1. Allez sur votre repository GitHub
2. **Settings** → **Pages**
3. Sélectionnez **Branch: main** et **Folder: / (root)**
4. ✅ Cliquez sur **Save**

Votre app sera disponible à : `https://USERNAME.github.io/projectflow/`

## 📤 Après chaque modification

Pour pousser vos changements :

```bash
git add .
git commit -m "Description de vos changements"
git push
```

## ✅ Vérification

Pour vérifier que tout est configuré correctement :

```bash
git remote -v
# Devrait afficher :
# origin  https://github.com/USERNAME/projectflow.git (fetch)
# origin  https://github.com/USERNAME/projectflow.git (push)
```

## 🆘 Besoin d'aide ?

- Documentation Git : https://git-scm.com/book
- Aide GitHub : https://docs.github.com
- Commandes Git courantes : https://github.github.com/training-kit/

---
**Bon déploiement ! 🚀**
