from locust import HttpUser, task, between, LoadTestShape
import random
import time

# ===============================================================
# PASO 1: Define el comportamiento del usuario (QUÉ hacen)
# Esta clase es la misma que la anterior, define las tareas.
# ===============================================================
class WebUser(HttpUser):
    wait_time = between(1, 3)

    @task(10)
    def get_all_users(self):
        self.client.get("/user-service/api/users")

    @task(5)
    def get_user_by_id(self):
        user_id = random.randint(1, 4)
        self.client.get(f"/user-service/api/users/{user_id}", name="/user-service/api/users/[id]")
    
    # ... puedes añadir las otras tareas si quieres que también se ejecuten
    # durante el spike test para tener una carga más variada.


# ===============================================================
# PASO 2: Define la forma de la carga (CUÁNDO y CUÁNTOS usuarios)
# Aquí está la lógica del Spike Test.
# ===============================================================
class SpikeTestShape(LoadTestShape):
    """
    Una forma de carga para simular picos (spikes).

    Consta de 4 etapas que se repiten en un ciclo:
    1. Carga baja y estable (línea base).
    2. Rampa de subida muy rápida (el pico).
    3. Carga alta y estable (mantenimiento del pico).
    4. Rampa de bajada para volver a la normalidad.
    """
    
    stages = [
        {"duration": 60, "users": 20, "spawn_rate": 10},  # 1. Línea base
        {"duration": 70, "users": 200, "spawn_rate": 50}, # 2. Rampa hacia el pico (dura 10s)
        {"duration": 100, "users": 200, "spawn_rate": 50},# 3. Mantenimiento del pico (dura 30s)
        {"duration": 110, "users": 20, "spawn_rate": 50}, # 4. Enfriamiento (dura 10s)
    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                # Devuelve la cantidad de usuarios y la tasa de generación para la etapa actual
                return (stage["users"], stage["spawn_rate"])
        return None