from sklearn.preprocessing import MinMaxScaler

from odoo import models, fields, api
from sklearn.ensemble import RandomForestRegressor
import numpy as np

class EnergyOptimization(models.Model):
    _name = 'energy.optimization'
    _description = 'Ottimizzazione Energetica Basata su AI'

    name = fields.Char(string='Name', required=True)
    machine_efficiency = fields.Float(string='Machine Efficiency')
    energy_usage = fields.Float(string='Consumo Energetico (kWh)', required=True)

    temperature = fields.Float(string='Temperatura (°C)', required=False)
    humidity = fields.Float(string='Umidità (%)', required=False)
    optimized_schedule = fields.Text(string='Pianificazione Ottimizzata', compute='_compute_optimization')
    maintenance_flag = fields.Boolean(string='Manutenzione Necessaria', compute='_compute_maintenance')

    @api.depends('energy_usage', 'machine_efficiency', 'temperature', 'humidity')
    def _compute_optimization(self):
        for record in self:
            # Recupera i dati storici per addestrare il modello
            historical_data = self._get_historical_data()

            if not historical_data:
                record.optimized_schedule = "Dati storici insufficienti per calcolare l'ottimizzazione."
                return

            features = []
            targets = []

            for rec in historical_data:
                features.append([rec.energy_usage, rec.machine_efficiency, rec.temperature or 22, rec.humidity or 50])
                targets.append(rec.energy_usage)

            features = np.array(features)
            targets = np.array(targets)

            # Scaler dei dati
            scaler_X = MinMaxScaler()
            scaler_y = MinMaxScaler()
            features_scaled = scaler_X.fit_transform(features)
            targets_scaled = scaler_y.fit_transform(targets.reshape(-1, 1)).ravel()

            # Allena il modello
            model = RandomForestRegressor()
            model.fit(features_scaled, targets_scaled)

            # Previsione e ottimizzazione
            current_data = np.array(
                [[record.energy_usage, record.machine_efficiency, record.temperature or 22, record.humidity or 50]])
            current_data_scaled = scaler_X.transform(current_data)
            prediction_scaled = model.predict(current_data_scaled)[0]
            prediction = scaler_y.inverse_transform([[prediction_scaled]])[0][0]

            record.optimized_consumption = prediction
            record.optimized_schedule = f"Consumo previsto ottimizzato: {prediction:.2f} kWh"
            record.potential_savings = record.energy_usage - prediction

    @api.depends('energy_usage', 'machine_efficiency')
    def _compute_maintenance(self):
        for record in self:
            if record.machine_efficiency < 70 or record.energy_usage > 120:
                record.maintenance_flag = True
            else:
                record.maintenance_flag = False
