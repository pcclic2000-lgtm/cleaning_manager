# services/employee_status_service.py
"""
Service centralisé pour gérer les changements de statut des employés
Actif <-> Inactif
"""

from typing import List
from datetime import date
from database.db import SessionLocal, get_session
from models.employee import Employee


class EmployeeStatusService:
    """Service pour gérer les changements de statut des employés"""

    @staticmethod
    def change_employee_status(employee_id: int, new_status: bool) -> List[str]:
        """
        Change le statut d'un employé de manière sécurisée.
        new_status = True  -> Actif
        new_status = False -> Inactif
        """
        try:
            with get_session() as session:
                actions = []

                employee = session.query(Employee).filter(Employee.id == employee_id).first()
                if not employee:
                    return ["❌ Employé introuvable"]

                old_status = employee.est_actif

                # Aucun changement
                if old_status == new_status:
                    return ["ℹ️ Aucun changement de statut"]

                # Appliquer le nouveau statut
                employee.est_actif = new_status

                if old_status and not new_status:
                    actions.append("🚫 Employé désactivé")
                    EmployeeStatusService._handle_deactivation(session, employee, actions)

                elif not old_status and new_status:
                    actions.append("✅ Employé réactivé")
                    EmployeeStatusService._handle_reactivation(session, employee, actions)

                session.commit()
                return actions

        except Exception as e:
            return [f"❌ Erreur changement statut : {e}"]

    # ------------------------------------------------------------------

    @staticmethod
    def _handle_deactivation(session, employee: Employee, actions: List[str]):
        """Actions automatiques lors de la désactivation"""
        try:
            # 1. Mettre en pause les tâches actives
            from models.tache import Tache

            active_tasks = session.query(Tache).filter(
                Tache.employee_id == employee.id,
                Tache.est_terminee == False,
                Tache.en_pause == False
            ).all()

            raison = employee.raison_arret or "Statut inactif"

            for task in active_tasks:
                task.en_pause = True
                task.pause_systeme = True
                task.date_pause = date.today()
                task.raison_pause = f"Employé désactivé : {raison}"
                actions.append(f"⏸️ Tâche '{task.titre}' mise en pause")

        except Exception as e:
            actions.append(f"⚠️ Erreur pause tâches : {e}")

        try:
            # 2. Terminer les affectations en cours
            from models.affectation import Affectation

            active_assignments = session.query(Affectation).filter(
                Affectation.employee_id == employee.id,
                Affectation.date_fin == None
            ).all()

            for assignment in active_assignments:
                assignment.date_fin = employee.date_arret or date.today()
                assignment.raison_fin = "Employé désactivé"
                actions.append(f"📌 Affectation #{assignment.id} terminée")

        except Exception as e:
            actions.append(f"⚠️ Erreur affectations : {e}")

    # ------------------------------------------------------------------

    @staticmethod
    def _handle_reactivation(session, employee: Employee, actions: List[str]):
        """Actions automatiques lors de la réactivation"""
        try:
            from models.tache import Tache

            paused_tasks = session.query(Tache).filter(
                Tache.employee_id == employee.id,
                Tache.en_pause == True,
                Tache.pause_systeme == True
            ).all()

            for task in paused_tasks:
                task.en_pause = False
                task.pause_systeme = False
                task.date_reprise = date.today()
                actions.append(f"▶️ Tâche '{task.titre}' reprise")

            # Nettoyage des infos d'arrêt
            employee.date_arret = None
            employee.raison_arret = None

        except Exception as e:
            actions.append(f"⚠️ Erreur reprise tâches : {e}")