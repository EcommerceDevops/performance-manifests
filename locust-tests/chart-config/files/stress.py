from locust import HttpUser, task, between, LoadTestShape
import random
import math

# ===============================================================
# PASO 1: Define el comportamiento del usuario (QUÉ hacen)
# Esta clase define las tareas con pesos, usando IDs dinámicos.
# No se especifica el 'host', por lo que debe ser proporcionado
# al iniciar Locust.
# ===============================================================
class WebUser(HttpUser):
    wait_time = between(1, 3)

    # Tareas más frecuentes
    @task(10)
    def get_all_users(self):
        self.client.get("/user-service/api/users")

    @task(10)
    def get_all_addresses(self):
        self.client.get("/user-service/api/address")

    # Tareas de frecuencia media
    @task(5)
    def get_user_by_id(self):
        user_id = random.randint(1, 4)
        self.client.get(f"/user-service/api/users/{user_id}", name="/user-service/api/users/[id]")

    @task(5)
    def get_address_by_id(self):
        address_id = random.randint(1, 4)
        self.client.get(f"/user-service/api/address/{address_id}", name="/user-service/api/address/[id]")
    
    # Tareas menos frecuentes
    @task(2)
    def get_all_credentials(self):
        self.client.get("/user-service/api/credentials")

    @task(2)
    def get_credential_by_id(self):
        credential_id = random.randint(1, 4)
        self.client.get(f"/user-service/api/credentials/{credential_id}", name="/user-service/api/credentials/[id]")

    # Las tareas de token suelen ser las menos comunes
    @task
    def get_all_verification_tokens(self):
        self.client.get("/user-service/api/verificationTokens")

    @task
    def get_verification_token_by_id(self):
        token_id = random.randint(1, 4)
        self.client.get(f"/user-service/api/verificationTokens/{token_id}", name="/user-service/api/verificationTokens/[id]")


# ===============================================================
# PASO 2: Define la forma de la carga (patrón de escalera)
# Aquí está la lógica de la prueba de estrés.
# ===============================================================
class StressTestShape(LoadTestShape):
    """
    Una forma de carga para una prueba de estrés con patrón de escalera.
    Aumenta gradualmente la cantidad de usuarios en pasos discretos y
    mantiene cada paso durante un tiempo determinado.
    """

    # --- Parámetros configurables para la prueba de estrés ---
    TIME_TO_HOLD_STEP = 30  # Segundos para mantener cada "escalón" de carga
    USERS_PER_STEP = 200      # Cuántos usuarios añadir en cada nuevo escalón
    SPAWN_RATE = 50          # Tasa de generación de usuarios para cada escalón
    MAX_STEPS = 20  # Máximo número de escalones (carga máxima total)
    # ---------------------------------------------------------

    def tick(self):
        run_time = self.get_run_time()
        
        # Calcula en qué "escalón" de tiempo nos encontramos
        # math.floor() redondea hacia abajo al entero más cercano
        current_step = math.floor(run_time / self.TIME_TO_HOLD_STEP)

        # --- Condición de parada ---
        if current_step >= self.MAX_STEPS:
            return None # Esto detiene la prueba
        # ---------------------------
        
        # Calcula el número de usuarios para el escalón actual
        current_users = (current_step + 1) * self.USERS_PER_STEP
        
        # Devuelve el total de usuarios y la tasa de generación
        return (current_users, self.SPAWN_RATE)