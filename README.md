# 🚀 Azure Deployment Guide


## ⭐ Project Purpose

This project demonstrates **cloud deployment of a Flask application using Microsoft Azure**, focusing on **security, scalability, and automation**.

The objective of this project is to demonstrate a **complete cloud deployment workflow**, including:

* Azure App Service configuration
* PostgreSQL database setup
* Azure Key Vault security
* GitHub CI/CD deployment
* Environment configuration
* Production deployment testing

---

## ☁️ Deployment Architecture

The application is deployed using the following Azure services:

* **Azure App Service** — Host Flask application
* **Azure PostgreSQL Flexible Server** — Database
* **Azure Key Vault** — Secret management
* **Azure Virtual Network** — Secure communication
* **GitHub Actions** — CI/CD Deployment

---

## 🛠️ Deployment Technologies

* Python 3.12
* Flask
* Gunicorn
* PostgreSQL
* Azure App Service
* Azure Key Vault
* GitHub Actions
* Python-dotenv

---

## 🚀 Deployment Workflow

### 1. GitHub Repository Setup

Create a GitHub repository and link your local project:

```bash
git init
git remote add origin https://github.com/username/repository.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

---

## ☁️ Azure Deployment Steps

### Step 1 — Create Azure Resource Group

* Resource Group Name: `your_grp_name`
* Region: `your_nearest_region`

This resource group contains all deployment components.

---

### Step 2 — Create Azure App Service

Configuration:

* Runtime: Python 3.12
* OS: Linux
* Region: South Africa North
* Plan: Basic

This service hosts the Flask application.

---

### Step 3 — Create PostgreSQL Database

* PostgreSQL Flexible Server
* Database Name: `your-database_name`
* Server Name: `tyour_server_name`

Used for persistent storage.

---

### Step 4 — Configure Azure Key Vault

Azure Key Vault is used to store:

* Database password
* Connection strings
* Secrets

This improves security and prevents exposing credentials.

---

### Step 5 — Configure Service Connector

Connect Azure App Service to PostgreSQL:

* Select PostgreSQL server
* Configure authentication
* Store secrets in Key Vault

---

## ⚙️ Application Deployment Configuration

### Startup Configuration

Create `startup.txt`

```bash
gunicorn --bind 0.0.0.0:$PORT app:app
```

Configure startup command in Azure:

```
startup.txt
```

---

## 🔐 Environment Variables

Create `.env` file

```env
AZURE_POSTGRESQL_USER=
AZURE_POSTGRESQL_PASSWORD=
AZURE_POSTGRESQL_HOST=
AZURE_POSTGRESQL_NAME=
```

Install dotenv:

```bash
pip install python-dotenv
```

---

## 🔄 CI/CD Deployment (GitHub Actions)

Enable GitHub deployment from Azure:

* Deployment Center
* Select GitHub
* Select repository
* Select branch main

Azure automatically creates GitHub workflow.

Deployment triggers on push:

```bash
git add .
git commit -m "Deploy"
git push origin main
```

---

## 🧪 Database Migration

Using Azure SSH:

```bash
flask db upgrade
```

---

## 🌐 Access Application

After deployment:

```
https://taskease.azurewebsites.net
```
---

## 🔒 Security Implementation

* Azure Key Vault
* Private Endpoint
* Environment Variables
* Secure PostgreSQL connection

---

## 📊 Deployment Pipeline

```
GitHub → GitHub Actions → Azure App Service → PostgreSQL
```

---

## ✅ Deployment Result

* Application deployed successfully
* PostgreSQL connected
* CI/CD enabled
* Secure secrets configured

---


