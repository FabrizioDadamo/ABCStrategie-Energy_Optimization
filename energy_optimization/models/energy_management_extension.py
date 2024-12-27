from odoo import models, fields, api
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
from datetime import datetime, timedelta
import logging
import pickle
import os

_logger = logging.getLogger(__name__)

class EnergyConsumption(models.Model):
    _inherit = 'energy.consumption'

    machine_efficiency = fields.Float(string='Efficienza Macchinari (%)',
                                      help='Percentuale di efficienza del macchinario')
    optimized_schedule = fields.Text(string='Pianificazione Ottimizzata', compute='_compute_optimization', store=True)
    optimized_consumption = fields.Float(string='Consumo Ottimizzato (kWh)', compute='_compute_optimization',
                                         store=True)
    suggested_efficiency = fields.Float(string='Efficienza Suggerita (%)', compute='_compute_optimization', store=True)
    potential_savings = fields.Float(string='Potenziale Risparmio (kWh)', compute='_compute_optimization', store=True)
    maintenance_flag = fields.Boolean(string='Manutenzione Necessaria', compute='_compute_maintenance', store=True)

    def _get_historical_data(self):
        """Recupera i dati storici degli ultimi 5 giorni per l'analisi"""
        date_limit = datetime.now() - timedelta(days=5)
        historical_data = self.search([
            ('date', '>=', date_limit),
            ('type', '=', 'real')
        ])
        return historical_data

    def _train_or_load_model(self, features, targets):
        """Carica o allena un modello di previsione se non esiste"""
        model_directory = os.path.join("C:/odoo", "model")  # Directory dove salvare il modello
        model_path = os.path.join(model_directory, "model.pkl")

        # Crea la cartella se non esiste
        if not os.path.exists(model_directory):
            os.makedirs(model_directory)

        try:
            # Carica il modello se esiste
            with open(model_path, "rb") as f:
                model = pickle.load(f)
        except FileNotFoundError:
            # Se non esiste, allena il modello
            _logger.info("Modello non trovato, allenamento del modello.")
            model = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)
            model.fit(features, targets)

            # Salva il modello addestrato
            with open(model_path, "wb") as f:
                pickle.dump(model, f)
            _logger.info("Modello allenato e salvato con successo.")

        return model

    def _find_optimal_efficiency(self, record, model, scaler_X, scaler_y):
        """Trova l'efficienza ottimale per minimizzare il consumo"""
        best_efficiency = record.machine_efficiency
        best_consumption = None

        for test_efficiency in np.arange(record.machine_efficiency, 100, 2):
            test_data = np.array([[record.energy_usage, test_efficiency]])
            test_data_scaled = scaler_X.transform(test_data)
            test_prediction_scaled = model.predict(test_data_scaled)[0]
            test_prediction = scaler_y.inverse_transform([[test_prediction_scaled]])[0][0]

            if best_consumption is None or test_prediction < best_consumption:
                best_consumption = test_prediction
                best_efficiency = test_efficiency

        return best_efficiency, best_consumption

    @api.depends('energy_usage', 'machine_efficiency')
    def _compute_optimization(self):
        """Calcola l'ottimizzazione per ogni record di consumo energetico"""
        historical_data = self._get_historical_data()

        if not historical_data:
            for record in self:
                record.optimized_consumption = 0.0
                record.suggested_efficiency = 0.0
                record.potential_savings = 0.0
                record.optimized_schedule = "Dati storici insufficienti per calcolare l'ottimizzazione."
            return

        features = []
        targets = []

        for record in historical_data:
            efficiency = getattr(record, 'machine_efficiency', 80.0)
            features.append([record.energy_usage, efficiency])
            targets.append(record.energy_usage)

        features = np.array(features)
        targets = np.array(targets)

        scaler_X = MinMaxScaler()
        scaler_y = MinMaxScaler()
        features_scaled = scaler_X.fit_transform(features)
        targets_scaled = scaler_y.fit_transform(targets.reshape(-1, 1)).ravel()

        # Carica o allena il modello
        model = self._train_or_load_model(features_scaled, targets_scaled)

        # Calcola le ottimizzazioni per ogni record
        for record in self:
            if record.machine_efficiency and record.energy_usage:
                current_data = np.array([[record.energy_usage, record.machine_efficiency]])
                current_data_scaled = scaler_X.transform(current_data)
                current_prediction_scaled = model.predict(current_data_scaled)[0]
                current_prediction = scaler_y.inverse_transform([[current_prediction_scaled]])[0][0]

                best_efficiency, best_consumption = self._find_optimal_efficiency(record, model, scaler_X, scaler_y)

                record.optimized_consumption = best_consumption
                record.suggested_efficiency = best_efficiency
                record.potential_savings = current_prediction - best_consumption

                record.optimized_schedule = f"Efficienza suggerita: {best_efficiency}% - Risparmio: {record.potential_savings:.2f} kWh"

    @api.depends('energy_usage', 'machine_efficiency')
    def _compute_maintenance(self):
        for record in self:
            if record.energy_usage > 150 or (hasattr(record, 'machine_efficiency') and record.machine_efficiency < 70):
                record.maintenance_flag = True
            else:
                record.maintenance_flag = False