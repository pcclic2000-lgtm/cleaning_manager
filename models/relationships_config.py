# models/relationships_config.py
"""
Configure manuellement les relations après l'import de tous les modèles
"""

def configure_relationships():
    """Configure toutes les relations problématiques"""
    print("🔗 Configuration manuelle des relations...")
    
    try:
        import sqlalchemy.orm
        
        # Importez les classes
        from .contrat import Contrat
        from .tache import Tache
        from .employee import Employee
        from .client import Client
        
        # Configurez Contrat -> Tache
        Contrat.taches = sqlalchemy.orm.relationship(
            Tache,
            back_populates="contrat",
            cascade="all, delete-orphan"
        )
        
        # Configurez Tache -> Contrat
        Tache.contrat = sqlalchemy.orm.relationship(
            Contrat,
            back_populates="taches"
        )
        
        print("✅ Relations Contrat-Tache configurées")
        
        
        
    except Exception as e:
        print(f"⚠️  Erreur configuration: {e}")