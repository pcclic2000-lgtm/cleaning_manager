# init_db.py - Script d'initialisation dédié
import os
import sys

print("🧹 CLEAN MANAGER - Initialisation de la base de données")
print("=" * 70)

# Supprimer l'ancienne base si elle existe
for db_file in ['cleaning_manager.db', 'database.db']:
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
            print(f"✅ Ancienne base '{db_file}' supprimée")
        except Exception as e:
            print(f"⚠️ Impossible de supprimer {db_file} : {e}")

try:
    print("\n1. Configuration de l'environnement...")
    # Ajouter le chemin courant au PYTHONPATH
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))

    from database.db import Base, engine

    print("2. Importation des modèles...")
    import models.client
    import models.employee
    import models.contrat
    import models.tache
    import models.invoice
    # Le module de paie est dans models/paye_globale (+cotisation)
    import models.paye_globale

    print("3. Création des tables...")
    Base.metadata.create_all(bind=engine)

    print("4. Vérification des tables créées...")
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n📊 Tables créées ({len(tables)}):")
    for i, table in enumerate(tables, 1):
        print(f"   {i:2d}. {table}")

    print("\n5. Création de données de test...")
    from database.db import get_session
    from datetime import date
    from models.employee import Employee
    from models.client import Client
    from models.paye_globale import PayrollPeriod

    with get_session() as session:
        if session.query(Employee).count() == 0:
            admin = Employee(
                code_employe="EMP-ADMIN-001",
                nom="Admin",
                prenom="Système",
                telephone="0550000000",
                adresse="Adresse admin",
                date_embauche=date.today(),
                est_actif=True,
            )
            session.add(admin)

            test_employees = [
                Employee(
                    code_employe="EMP-202501-001",
                    nom="Dupont",
                    prenom="Jean",
                    telephone="0551123456",
                    adresse="123 Rue Principale, Alger",
                    date_embauche=date(2024, 1, 15),
                    est_actif=True,
                ),
                Employee(
                    code_employe="EMP-202501-002",
                    nom="Martin",
                    prenom="Marie",
                    telephone="0551234567",
                    adresse="456 Avenue Centrale, Oran",
                    date_embauche=date(2024, 3, 10),
                    est_actif=True,
                ),
            ]
            session.add_all(test_employees)

        if session.query(Client).count() == 0:
            client = Client(
                code_client="CL-TEST-001",
                nom="Entreprise Test",
                prenom="Client",
                telephone="0559876543",
                email="client@test.com",
                adresse="789 Rue Commerciale",
                date_naissance=date(1980, 5, 15),
                statut="Actif",
                type_client="Entreprise",
                est_actif=True,
            )
            session.add(client)

        if session.query(PayrollPeriod).count() == 0:
            period = PayrollPeriod(
                month=date.today().month,
                year=date.today().year,
                status="Ouvert",
                date_debut=date(date.today().year, date.today().month, 1),
                date_fin=date(date.today().year, date.today().month, 28),
            )
            session.add(period)

        session.commit()

    print("\n" + "=" * 70)
    print("✅ BASE DE DONNÉES INITIALISÉE AVEC SUCCÈS!")
    print("=" * 70)

except Exception as e:
    print(f"\n❌ ERREUR D'INITIALISATION: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
