#!/usr/bin/env python3
"""
Script de création de données de développement/test.
USAGE : python tools/seed_dev_data.py
Ne jamais exécuter en production.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from database.db import SessionLocal, get_session
from models.employee import Employee
from models.client import Client


def seed():
    try:
        with get_session() as session:
            if session.query(Employee).count() == 0:
                session.add(Employee(
                    code_employe="EMP-TEST-001",
                    nom="Test",
                    prenom="Employé",
                    telephone="0550000001",
                    date_embauche=date.today(),
                    est_actif=True
                ))
                print("✅ Employé de test créé")

            if session.query(Client).count() == 0:
                session.add(Client(
                    code_client="CL-TEST-001",
                    nom="Client",
                    prenom="Test",
                    telephone="0550000002",
                    email="test@example.com",
                    est_actif=True
                ))
                print("✅ Client de test créé")

            session.commit()
            print("✅ Données de test insérées avec succès")
    except Exception as e:
        print(f"❌ Erreur: {e}")


if __name__ == "__main__":
    confirm = input("⚠️  Insérer des données de TEST ? (oui/non) : ")
    if confirm.strip().lower() == "oui":
        seed()
    else:
        print("Annulé.")