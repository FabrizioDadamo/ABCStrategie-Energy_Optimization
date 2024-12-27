{
    'name': 'Ottimizzazione Energetica Basata su AI',
    'version': '1.0',
    'category': 'Industry',
    'summary': 'Modulo per ottimizzare i consumi energetici e integrarsi con energy_management.',
    'description': """
        Utilizza modelli avanzati di Machine Learning per ottimizzare i consumi energetici 
        e fornisce integrazione con energy_management.
    """,
    'author': 'Fabrizio',
    'depends': ['base', 'energy_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/energy_optimization_views.xml',
        'views/energy_management_extension_views.xml',
        'data/energy_optimization_data.xml',
        'data/energy_efficiency_update.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
